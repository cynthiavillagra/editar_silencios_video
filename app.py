"""
App de Recorte de Silencios en Videos
=====================================
Esta aplicación detecta silencios mayores a un umbral configurable
y los recorta automáticamente, manteniendo una transición suave.

Compatible con Python 3.13+ (no usa audioop/pydub)
"""

import os
import uuid
import tempfile
import numpy as np
from scipy.io import wavfile
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, concatenate_videoclips

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configuración
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB máximo

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def detect_silent_segments_numpy(audio_path, silence_threshold_db=-40, min_silence_ms=300, min_sound_ms=200):
    """
    Detecta segmentos de silencio en el audio usando NumPy/SciPy.
    
    Args:
        audio_path: Ruta al archivo WAV
        silence_threshold_db: Umbral de silencio en dB (más negativo = más sensible)
        min_silence_ms: Duración mínima de silencio para considerarlo (ms)
        min_sound_ms: Duración mínima de sonido para considerarlo segmento válido (ms)
    
    Returns:
        Lista de tuplas (inicio, fin) de segmentos NO silenciosos en segundos
    """
    try:
        sample_rate, audio_data = wavfile.read(audio_path)
    except Exception as e:
        print(f"Error leyendo audio: {e}")
        return []
    
    # Convertir a mono si es estéreo
    if len(audio_data.shape) > 1:
        audio_data = audio_data.mean(axis=1)
    
    # Normalizar a float
    audio_data = audio_data.astype(np.float64)
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        audio_data = audio_data / max_val
    
    # Calcular el umbral lineal desde dB
    silence_threshold = 10 ** (silence_threshold_db / 20)
    
    # Tamaño de ventana para análisis (en muestras)
    window_size = int(sample_rate * 0.02)  # 20ms ventanas
    hop_size = window_size // 2  # 50% overlap
    
    # Calcular energía RMS por ventana
    num_windows = (len(audio_data) - window_size) // hop_size + 1
    is_sound = np.zeros(num_windows, dtype=bool)
    
    for i in range(num_windows):
        start = i * hop_size
        end = start + window_size
        window = audio_data[start:end]
        rms = np.sqrt(np.mean(window ** 2))
        is_sound[i] = rms > silence_threshold
    
    # Convertir ventanas de silencio/sonido a segmentos de tiempo
    # Aplicar filtro de duración mínima
    min_silence_windows = int((min_silence_ms / 1000) * sample_rate / hop_size)
    min_sound_windows = int((min_sound_ms / 1000) * sample_rate / hop_size)
    
    # Encontrar cambios de estado
    segments = []
    current_state = is_sound[0]
    segment_start = 0
    
    for i in range(1, len(is_sound)):
        if is_sound[i] != current_state:
            segment_length = i - segment_start
            
            # Verificar duración mínima
            if current_state:  # Era sonido
                if segment_length >= min_sound_windows:
                    start_sec = segment_start * hop_size / sample_rate
                    end_sec = i * hop_size / sample_rate
                    segments.append((start_sec, end_sec))
            
            segment_start = i
            current_state = is_sound[i]
    
    # Último segmento
    if current_state and (len(is_sound) - segment_start) >= min_sound_windows:
        start_sec = segment_start * hop_size / sample_rate
        end_sec = len(audio_data) / sample_rate
        segments.append((start_sec, end_sec))
    
    return segments


def process_video(input_path, output_path, max_silence_duration=3.0, 
                  silence_threshold=-40, progress_callback=None):
    """
    Procesa un video recortando silencios mayores al umbral especificado.
    
    Args:
        input_path: Ruta al video de entrada
        output_path: Ruta al video de salida
        max_silence_duration: Duración máxima de silencio permitida (segundos)
        silence_threshold: Umbral de silencio en dB
        progress_callback: Función para reportar progreso
    
    Returns:
        dict con estadísticas del procesamiento
    """
    print(f"[INFO] Procesando: {input_path}")
    print(f"[INFO] Configuración: max_silence={max_silence_duration}s, threshold={silence_threshold}dB")
    
    # Cargar el video
    video = VideoFileClip(input_path)
    original_duration = video.duration
    print(f"[INFO] Duración original: {original_duration:.2f}s")
    
    # Verificar si tiene audio
    if video.audio is None:
        print("[WARN] El video no tiene audio, devolviendo original")
        video.write_videofile(output_path, verbose=False, logger=None)
        video.close()
        return {
            'original_duration': round(original_duration, 2),
            'new_duration': round(original_duration, 2),
            'time_saved': 0,
            'segments_processed': 0,
            'percentage_saved': 0
        }
    
    # Extraer audio temporalmente como WAV
    temp_audio_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.wav")
    print(f"[INFO] Extrayendo audio a: {temp_audio_path}")
    video.audio.write_audiofile(temp_audio_path, fps=22050, verbose=False, logger=None)
    
    # Detectar segmentos no silenciosos
    print("[INFO] Analizando audio...")
    nonsilent_segments = detect_silent_segments_numpy(
        temp_audio_path, 
        silence_threshold_db=silence_threshold,
        min_silence_ms=300,
        min_sound_ms=200
    )
    print(f"[INFO] Segmentos de sonido detectados: {len(nonsilent_segments)}")
    
    # Limpiar archivo temporal de audio
    if os.path.exists(temp_audio_path):
        try:
            os.remove(temp_audio_path)
        except:
            pass
    
    if not nonsilent_segments:
        # No se detectó audio con sonido, devolver original
        print("[WARN] No se detectaron segmentos de sonido")
        video.write_videofile(output_path, codec='libx264', audio_codec='aac', verbose=False, logger=None)
        video.close()
        return {
            'original_duration': round(original_duration, 2),
            'new_duration': round(original_duration, 2),
            'time_saved': 0,
            'segments_processed': 0,
            'percentage_saved': 0
        }
    
    # Procesar segmentos: unir cercanos y limitar silencios largos
    processed_segments = []
    buffer = 0.15  # 150ms de buffer para transiciones suaves
    
    for i, (start, end) in enumerate(nonsilent_segments):
        if i == 0:
            # Primer segmento: empezar desde el inicio o casi
            segment_start = max(0, start - buffer)
        else:
            # Calcular gap desde el segmento anterior
            prev_end = nonsilent_segments[i-1][1]
            gap = start - prev_end
            
            if gap > max_silence_duration:
                # Silencio muy largo: mantener solo max_silence_duration
                segment_start = processed_segments[-1][1] + max_silence_duration if processed_segments else start - buffer
                segment_start = max(segment_start, start - buffer)
            else:
                # Silencio aceptable: extender desde el segmento anterior
                if processed_segments:
                    # Unir con el segmento anterior
                    processed_segments[-1] = (processed_segments[-1][0], min(video.duration, end + buffer))
                    continue
                else:
                    segment_start = max(0, start - buffer)
        
        segment_end = min(video.duration, end + buffer)
        
        # Evitar segmentos muy cortos o inválidos
        if segment_end > segment_start + 0.1:
            processed_segments.append((segment_start, segment_end))
    
    print(f"[INFO] Segmentos procesados: {len(processed_segments)}")
    
    # Crear subclips y concatenar
    if processed_segments:
        clips = []
        for start, end in processed_segments:
            try:
                clip = video.subclip(start, min(end, video.duration))
                clips.append(clip)
            except Exception as e:
                print(f"[WARN] Error en segmento ({start}, {end}): {e}")
                continue
        
        if clips:
            print(f"[INFO] Concatenando {len(clips)} clips...")
            final_video = concatenate_videoclips(clips, method="compose")
            print(f"[INFO] Escribiendo video: {output_path}")
            final_video.write_videofile(
                output_path, 
                codec='libx264',
                audio_codec='aac',
                verbose=False, 
                logger=None
            )
            new_duration = final_video.duration
            final_video.close()
            for clip in clips:
                clip.close()
        else:
            print("[WARN] No se generaron clips válidos")
            video.write_videofile(output_path, codec='libx264', audio_codec='aac', verbose=False, logger=None)
            new_duration = original_duration
    else:
        print("[WARN] No hay segmentos procesados")
        video.write_videofile(output_path, codec='libx264', audio_codec='aac', verbose=False, logger=None)
        new_duration = original_duration
    
    video.close()
    
    time_saved = original_duration - new_duration
    percentage_saved = (time_saved / original_duration * 100) if original_duration > 0 else 0
    
    print(f"[INFO] Procesamiento completo. Ahorrado: {time_saved:.2f}s ({percentage_saved:.1f}%)")
    
    return {
        'original_duration': round(original_duration, 2),
        'new_duration': round(new_duration, 2),
        'time_saved': round(time_saved, 2),
        'segments_processed': len(processed_segments),
        'percentage_saved': round(percentage_saved, 1)
    }


@app.route('/')
def index():
    """Página principal."""
    return render_template('index.html')


@app.route('/api/health')
def health():
    """Endpoint de health check."""
    return jsonify({'status': 'ok', 'message': 'Servidor funcionando correctamente'})


@app.route('/api/process', methods=['POST'])
def process_video_endpoint():
    """
    Endpoint para procesar un video.
    
    Form Data:
        - video: Archivo de video
        - max_silence: Duración máxima de silencio (segundos, default: 3)
        - sensitivity: Sensibilidad de detección (1-10, default: 5)
    """
    # Verificar que se envió un archivo
    if 'video' not in request.files:
        return jsonify({'error': 'No se envió ningún archivo de video'}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'error': f'Formato no permitido. Usa: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    # Obtener parámetros
    try:
        max_silence = float(request.form.get('max_silence', 3.0))
        sensitivity = int(request.form.get('sensitivity', 5))
    except ValueError:
        return jsonify({'error': 'Parámetros inválidos'}), 400
    
    # Convertir sensibilidad a umbral de dB
    # Sensibilidad 1 = -25dB (menos sensible), 10 = -55dB (muy sensible)
    silence_threshold = -25 - (sensitivity - 1) * 3.33
    
    # Guardar archivo temporal
    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"input_{unique_id}_{filename}")
    output_filename = f"editado_{filename.rsplit('.', 1)[0]}.mp4"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"output_{unique_id}_{output_filename}")
    
    try:
        print(f"[API] Guardando archivo temporal: {input_path}")
        file.save(input_path)
        
        # Procesar el video
        stats = process_video(
            input_path, 
            output_path,
            max_silence_duration=max_silence,
            silence_threshold=silence_threshold
        )
        
        # Verificar que se generó el output
        if os.path.exists(output_path):
            return jsonify({
                'success': True,
                'message': 'Video procesado exitosamente',
                'stats': stats,
                'download_id': unique_id,
                'filename': output_filename
            })
        else:
            return jsonify({'error': 'Error al generar el video procesado'}), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error procesando el video: {str(e)}'}), 500
    finally:
        # Limpiar archivo de entrada
        if os.path.exists(input_path):
            try:
                os.remove(input_path)
            except:
                pass


@app.route('/api/download/<download_id>/<filename>')
def download_video(download_id, filename):
    """Descarga el video procesado."""
    output_path = os.path.join(
        app.config['UPLOAD_FOLDER'], 
        f"output_{download_id}_{filename}"
    )
    
    if not os.path.exists(output_path):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    return send_file(
        output_path,
        as_attachment=True,
        download_name=filename,
        mimetype='video/mp4'
    )


@app.route('/api/cleanup/<download_id>/<filename>', methods=['DELETE'])
def cleanup_video(download_id, filename):
    """Limpia los archivos temporales después de la descarga."""
    output_path = os.path.join(
        app.config['UPLOAD_FOLDER'], 
        f"output_{download_id}_{filename}"
    )
    
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except:
            pass
    
    return jsonify({'success': True})


if __name__ == '__main__':
    print("=" * 60)
    print("✂️  SilenceCutter - Recorte Automático de Silencios")
    print("=" * 60)
    print("🌐 Abriendo en: http://localhost:5000")
    print("📋 Formatos soportados: MP4, AVI, MOV, MKV, WebM")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
