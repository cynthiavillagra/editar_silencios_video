"""
App de Recorte de Silencios en Videos v3
========================================
- División inteligente para videos largos
- Procesamiento por lotes (batch)
- Guardado de estado para resumir

Compatible con Python 3.13+
"""

import os
import uuid
import tempfile
import json
import time
import shutil
import numpy as np
from pathlib import Path
from scipy.io import wavfile
from flask import Flask, request, jsonify, send_file, render_template, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, concatenate_videoclips

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configuración
UPLOAD_FOLDER = tempfile.gettempdir()
STATE_FILE = os.path.join(tempfile.gettempdir(), 'silencecutter_state.json')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv'}
SPLIT_THRESHOLD_MINUTES = 30
CHUNK_DURATION_MINUTES = 30

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = None

# Almacén de progreso y resultados
progress_store = {}
results_store = {}
batch_store = {}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_state(batch_id, state):
    """Guarda el estado del batch para poder resumir."""
    state_path = os.path.join(UPLOAD_FOLDER, f'batch_state_{batch_id}.json')
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    return state_path


def load_state(batch_id):
    """Carga el estado guardado de un batch."""
    state_path = os.path.join(UPLOAD_FOLDER, f'batch_state_{batch_id}.json')
    if os.path.exists(state_path):
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def update_progress(job_id, stage, percent, message, **kwargs):
    """Actualiza el progreso de un trabajo."""
    progress_store[job_id] = {
        'stage': stage,
        'percent': percent,
        'message': message,
        'timestamp': time.time(),
        **kwargs
    }


def detect_silent_segments_numpy(audio_path, silence_threshold_db=-40, min_silence_ms=300, min_sound_ms=200):
    """Detecta segmentos de silencio en el audio."""
    try:
        sample_rate, audio_data = wavfile.read(audio_path)
    except Exception as e:
        print(f"Error leyendo audio: {e}")
        return []
    
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)
    
    audio_data = audio_data.astype(np.float64)
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        audio_data = audio_data / max_val
    
    silence_threshold = 10 ** (silence_threshold_db / 20)
    window_size = int(sample_rate * 0.02)
    hop_size = window_size // 2
    num_windows = (len(audio_data) - window_size) // hop_size + 1
    is_sound = np.zeros(num_windows, dtype=bool)
    
    for i in range(num_windows):
        start = i * hop_size
        end = start + window_size
        window = audio_data[start:end]
        rms = np.sqrt(np.mean(window ** 2))
        is_sound[i] = rms > silence_threshold
    
    min_sound_windows = int((min_sound_ms / 1000) * sample_rate / hop_size)
    
    segments = []
    current_state = is_sound[0]
    segment_start = 0
    
    for i in range(1, len(is_sound)):
        if is_sound[i] != current_state:
            if current_state and (i - segment_start) >= min_sound_windows:
                start_sec = segment_start * hop_size / sample_rate
                end_sec = i * hop_size / sample_rate
                segments.append((start_sec, end_sec))
            segment_start = i
            current_state = is_sound[i]
    
    if current_state and (len(is_sound) - segment_start) >= min_sound_windows:
        start_sec = segment_start * hop_size / sample_rate
        end_sec = len(audio_data) / sample_rate
        segments.append((start_sec, end_sec))
    
    return segments


def process_single_video(input_path, output_dir, base_filename, max_silence, silence_threshold, job_id=None):
    """Procesa un único video."""
    if job_id:
        update_progress(job_id, 'loading', 5, '📂 Cargando video...')
    
    video = VideoFileClip(input_path)
    total_duration = video.duration
    duration_minutes = total_duration / 60
    
    # Determinar si dividir
    if duration_minutes > SPLIT_THRESHOLD_MINUTES:
        num_parts = int(np.ceil(duration_minutes / CHUNK_DURATION_MINUTES))
        chunk_seconds = CHUNK_DURATION_MINUTES * 60
    else:
        num_parts = 1
        chunk_seconds = total_duration
    
    if job_id:
        update_progress(job_id, 'loading', 10, f'📂 Video: {int(duration_minutes)} min → {num_parts} parte(s)')
    
    os.makedirs(output_dir, exist_ok=True)
    
    parts_info = []
    total_original = 0
    total_new = 0
    
    for part_num in range(1, num_parts + 1):
        start_time = (part_num - 1) * chunk_seconds
        end_time = min(part_num * chunk_seconds, total_duration)
        
        if num_parts > 1:
            part_filename = f"{base_filename}_parte{part_num}.mp4"
        else:
            part_filename = f"{base_filename}.mp4"
        
        output_path = os.path.join(output_dir, part_filename)
        
        if job_id:
            base_pct = int(10 + (part_num - 1) / num_parts * 80)
            update_progress(job_id, 'processing', base_pct, 
                          f'⚙️ Parte {part_num}/{num_parts}', part=part_num, total_parts=num_parts)
        
        # Procesar chunk
        chunk = video.subclip(start_time, min(end_time, video.duration))
        chunk_duration = chunk.duration
        
        if chunk.audio is None:
            chunk.write_videofile(output_path, codec='libx264', audio_codec='aac',
                                 verbose=False, logger=None)
            new_duration = chunk_duration
        else:
            # Extraer audio
            temp_audio = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.wav")
            chunk.audio.write_audiofile(temp_audio, fps=22050, verbose=False, logger=None)
            
            # Detectar silencios
            segments = detect_silent_segments_numpy(temp_audio, silence_threshold)
            
            if os.path.exists(temp_audio):
                try: os.remove(temp_audio)
                except: pass
            
            if not segments:
                chunk.write_videofile(output_path, codec='libx264', audio_codec='aac',
                                     verbose=False, logger=None)
                new_duration = chunk_duration
            else:
                # Procesar segmentos
                processed = []
                buffer = 0.15
                
                for i, (s, e) in enumerate(segments):
                    if i == 0:
                        seg_start = max(0, s - buffer)
                    else:
                        prev_end = segments[i-1][1]
                        gap = s - prev_end
                        if gap > max_silence:
                            seg_start = processed[-1][1] + max_silence if processed else s - buffer
                            seg_start = max(seg_start, s - buffer)
                        else:
                            if processed:
                                processed[-1] = (processed[-1][0], min(chunk.duration, e + buffer))
                                continue
                            else:
                                seg_start = max(0, s - buffer)
                    
                    seg_end = min(chunk.duration, e + buffer)
                    if seg_end > seg_start + 0.1:
                        processed.append((seg_start, seg_end))
                
                if processed:
                    clips = []
                    for s, e in processed:
                        try:
                            clips.append(chunk.subclip(s, min(e, chunk.duration)))
                        except: pass
                    
                    if clips:
                        final = concatenate_videoclips(clips, method="compose")
                        final.write_videofile(output_path, codec='libx264', audio_codec='aac',
                                             verbose=False, logger=None)
                        new_duration = final.duration
                        final.close()
                        for c in clips: c.close()
                    else:
                        chunk.write_videofile(output_path, codec='libx264', audio_codec='aac',
                                             verbose=False, logger=None)
                        new_duration = chunk_duration
                else:
                    chunk.write_videofile(output_path, codec='libx264', audio_codec='aac',
                                         verbose=False, logger=None)
                    new_duration = chunk_duration
        
        chunk.close()
        
        parts_info.append({
            'filename': part_filename,
            'path': output_path,
            'part_num': part_num,
            'original_duration': round(chunk_duration, 2),
            'new_duration': round(new_duration, 2)
        })
        
        total_original += chunk_duration
        total_new += new_duration
    
    video.close()
    
    return {
        'num_parts': num_parts,
        'parts': parts_info,
        'total_original_duration': round(total_original, 2),
        'total_new_duration': round(total_new, 2),
        'total_time_saved': round(total_original - total_new, 2),
        'percentage_saved': round((1 - total_new/total_original) * 100, 1) if total_original > 0 else 0
    }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/api/progress/<job_id>')
def get_progress(job_id):
    def generate():
        while True:
            if job_id in progress_store:
                yield f"data: {json.dumps(progress_store[job_id])}\n\n"
                if progress_store[job_id].get('stage') in ['complete', 'error']:
                    break
            time.sleep(0.3)
    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/process', methods=['POST'])
def process_video_endpoint():
    """Procesa un único video."""
    if 'video' not in request.files:
        return jsonify({'error': 'No se envió archivo'}), 400
    
    file = request.files['video']
    if not file.filename or not allowed_file(file.filename):
        return jsonify({'error': 'Archivo no válido'}), 400
    
    try:
        max_silence = float(request.form.get('max_silence', 3.0))
        sensitivity = int(request.form.get('sensitivity', 5))
    except:
        return jsonify({'error': 'Parámetros inválidos'}), 400
    
    silence_threshold = -25 - (sensitivity - 1) * 3.33
    filename = secure_filename(file.filename)
    base_name = filename.rsplit('.', 1)[0]
    unique_id = str(uuid.uuid4())
    
    input_path = os.path.join(UPLOAD_FOLDER, f"input_{unique_id}_{filename}")
    output_dir = os.path.join(UPLOAD_FOLDER, f"output_{unique_id}")
    
    update_progress(unique_id, 'uploading', 0, '📤 Recibiendo...')
    
    try:
        file.save(input_path)
        result = process_single_video(input_path, output_dir, f"editado_{base_name}",
                                      max_silence, silence_threshold, unique_id)
        result['job_id'] = unique_id
        result['output_dir'] = output_dir
        result['base_filename'] = f"editado_{base_name}"
        results_store[unique_id] = result
        update_progress(unique_id, 'complete', 100, '✅ ¡Listo!')
        return jsonify({'success': True, 'job_id': unique_id, **result})
    except Exception as e:
        update_progress(unique_id, 'error', 0, f'❌ {str(e)}')
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(input_path):
            try: os.remove(input_path)
            except: pass


@app.route('/api/batch/start', methods=['POST'])
def start_batch():
    """Inicia un procesamiento por lotes."""
    data = request.get_json()
    files_info = data.get('files', [])
    max_silence = data.get('max_silence', 3.0)
    sensitivity = data.get('sensitivity', 5)
    
    batch_id = str(uuid.uuid4())
    
    # Crear estado del batch
    state = {
        'batch_id': batch_id,
        'total_files': len(files_info),
        'completed': 0,
        'failed': 0,
        'current_index': 0,
        'files': [{'name': f['name'], 'size': f['size'], 'status': 'pending', 'result': None} 
                  for f in files_info],
        'settings': {'max_silence': max_silence, 'sensitivity': sensitivity},
        'created_at': time.time()
    }
    
    batch_store[batch_id] = state
    save_state(batch_id, state)
    
    return jsonify({'batch_id': batch_id, 'state': state})


@app.route('/api/batch/<batch_id>/process/<int:file_index>', methods=['POST'])
def process_batch_file(batch_id, file_index):
    """Procesa un archivo específico del batch."""
    if batch_id not in batch_store:
        state = load_state(batch_id)
        if state:
            batch_store[batch_id] = state
        else:
            return jsonify({'error': 'Batch no encontrado'}), 404
    
    state = batch_store[batch_id]
    
    if file_index >= len(state['files']):
        return jsonify({'error': 'Índice inválido'}), 400
    
    if 'video' not in request.files:
        return jsonify({'error': 'No se envió archivo'}), 400
    
    file = request.files['video']
    file_state = state['files'][file_index]
    
    max_silence = state['settings']['max_silence']
    sensitivity = state['settings']['sensitivity']
    silence_threshold = -25 - (sensitivity - 1) * 3.33
    
    filename = secure_filename(file.filename)
    base_name = filename.rsplit('.', 1)[0]
    job_id = f"{batch_id}_{file_index}"
    
    input_path = os.path.join(UPLOAD_FOLDER, f"batch_{batch_id}_input_{filename}")
    output_dir = os.path.join(UPLOAD_FOLDER, f"batch_{batch_id}_output_{file_index}")
    
    update_progress(job_id, 'uploading', 0, f'📤 Archivo {file_index + 1}/{state["total_files"]}')
    
    try:
        file.save(input_path)
        
        file_state['status'] = 'processing'
        save_state(batch_id, state)
        
        result = process_single_video(input_path, output_dir, f"editado_{base_name}",
                                      max_silence, silence_threshold, job_id)
        
        file_state['status'] = 'completed'
        file_state['result'] = {
            'job_id': job_id,
            'output_dir': output_dir,
            'base_filename': f"editado_{base_name}",
            **result
        }
        state['completed'] += 1
        state['current_index'] = file_index + 1
        
        save_state(batch_id, state)
        results_store[job_id] = file_state['result']
        
        update_progress(job_id, 'complete', 100, '✅ Completado')
        
        return jsonify({
            'success': True,
            'file_index': file_index,
            'result': file_state['result'],
            'batch_progress': {
                'completed': state['completed'],
                'total': state['total_files'],
                'percent': round(state['completed'] / state['total_files'] * 100, 1)
            }
        })
        
    except Exception as e:
        file_state['status'] = 'failed'
        file_state['error'] = str(e)
        state['failed'] += 1
        state['current_index'] = file_index + 1
        save_state(batch_id, state)
        
        update_progress(job_id, 'error', 0, f'❌ {str(e)}')
        return jsonify({'error': str(e), 'file_index': file_index}), 500
    finally:
        if os.path.exists(input_path):
            try: os.remove(input_path)
            except: pass


@app.route('/api/batch/<batch_id>/state')
def get_batch_state(batch_id):
    """Obtiene el estado actual del batch."""
    if batch_id in batch_store:
        return jsonify(batch_store[batch_id])
    
    state = load_state(batch_id)
    if state:
        batch_store[batch_id] = state
        return jsonify(state)
    
    return jsonify({'error': 'Batch no encontrado'}), 404


@app.route('/api/batch/<batch_id>/resume')
def resume_batch(batch_id):
    """Obtiene información para resumir un batch."""
    state = load_state(batch_id)
    if not state:
        return jsonify({'error': 'No hay estado guardado'}), 404
    
    batch_store[batch_id] = state
    
    # Encontrar el primer archivo pendiente
    resume_index = 0
    for i, f in enumerate(state['files']):
        if f['status'] == 'pending':
            resume_index = i
            break
        elif f['status'] == 'failed':
            resume_index = i
            break
    
    return jsonify({
        'can_resume': True,
        'batch_id': batch_id,
        'state': state,
        'resume_from_index': resume_index
    })


@app.route('/api/download/<job_id>/part/<int:part_num>')
def download_part(job_id, part_num):
    if job_id not in results_store:
        return jsonify({'error': 'No encontrado'}), 404
    result = results_store[job_id]
    for part in result.get('parts', []):
        if part['part_num'] == part_num and os.path.exists(part['path']):
            return send_file(part['path'], as_attachment=True, download_name=part['filename'])
    return jsonify({'error': 'Parte no encontrada'}), 404


@app.route('/api/download/<job_id>/merged')
def download_merged(job_id):
    if job_id not in results_store:
        return jsonify({'error': 'No encontrado'}), 404
    result = results_store[job_id]
    
    if result.get('num_parts', 1) == 1:
        part = result['parts'][0]
        return send_file(part['path'], as_attachment=True, download_name=part['filename'])
    
    merged_path = os.path.join(result['output_dir'], f"{result['base_filename']}_completo.mp4")
    
    if not os.path.exists(merged_path):
        clips = [VideoFileClip(p['path']) for p in result['parts']]
        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(merged_path, codec='libx264', audio_codec='aac', 
                             verbose=False, logger=None)
        final.close()
        for c in clips: c.close()
    
    return send_file(merged_path, as_attachment=True, 
                    download_name=f"{result['base_filename']}_completo.mp4")


@app.route('/api/download/<job_id>/all')
def download_all(job_id):
    import zipfile
    if job_id not in results_store:
        return jsonify({'error': 'No encontrado'}), 404
    result = results_store[job_id]
    
    zip_path = os.path.join(result['output_dir'], f"{result['base_filename']}.zip")
    with zipfile.ZipFile(zip_path, 'w') as z:
        for p in result['parts']:
            if os.path.exists(p['path']):
                z.write(p['path'], p['filename'])
    
    return send_file(zip_path, as_attachment=True, download_name=f"{result['base_filename']}.zip")


@app.route('/api/cleanup/<job_id>', methods=['DELETE'])
def cleanup(job_id):
    if job_id in results_store:
        result = results_store[job_id]
        if 'output_dir' in result and os.path.exists(result['output_dir']):
            try: shutil.rmtree(result['output_dir'])
            except: pass
        del results_store[job_id]
    if job_id in progress_store:
        del progress_store[job_id]
    return jsonify({'success': True})


if __name__ == '__main__':
    print("=" * 60)
    print("✂️  SilenceCutter v3 - Procesamiento por Lotes")
    print("=" * 60)
    print("🌐 http://localhost:5000")
    print("📁 Procesa carpetas completas de videos")
    print("💾 Guarda estado para resumir")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
