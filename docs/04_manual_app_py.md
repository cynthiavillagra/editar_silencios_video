# 04 - Manual Técnico: app.py (Backend)

## 1. Información General

| Campo | Valor |
|-------|-------|
| **Archivo** | `app.py` |
| **Módulo** | Backend / Servidor |
| **Líneas** | ~720 |
| **Lenguaje** | Python 3.13+ |
| **Framework** | Flask 3.0 |

---

## 2. Trazabilidad

| Elemento | Referencia |
|----------|------------|
| **Requisitos** | RF01-RF12 |
| **Historias de Usuario** | HU-01, HU-02, HU-03, HU-04, HU-05, HU-06 |
| **Casos de Uso** | CU-01, CU-02 |
| **Patrones** | Singleton, Observer, Pipeline, State Machine, Factory, Memento |

---

## 3. Estrategia de Construcción

### 3.1 Estructura del Archivo

```
app.py
├── Imports y Configuración (líneas 1-40)
│   ├── Imports estándar (os, uuid, tempfile, etc.)
│   ├── Imports de terceros (Flask, MoviePy, NumPy, SciPy)
│   └── Configuración global (UPLOAD_FOLDER, stores, constantes)
│
├── Funciones de Utilidad (líneas 41-75)
│   ├── allowed_file()
│   ├── save_state() / load_state()
│   └── update_progress()
│
├── Procesamiento de Video (líneas 76-290)
│   ├── detect_silent_segments_numpy()
│   ├── process_single_video()
│   └── process_video_async()
│
├── Endpoints REST (líneas 291-600)
│   ├── / (index)
│   ├── /api/health
│   ├── /api/progress/<job_id> (SSE)
│   ├── /api/process (sync)
│   ├── /api/process/async
│   ├── /api/job/<job_id>
│   ├── /api/batch/*
│   └── /api/download/*
│
└── Main (líneas 700-720)
    └── if __name__ == "__main__": app.run()
```

### 3.2 Dependencias

```python
# Estándar
import os, uuid, tempfile, json, time, shutil, threading
from pathlib import Path

# Terceros
import numpy as np
from scipy.io import wavfile
from flask import Flask, request, jsonify, send_file, render_template, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, concatenate_videoclips
```

---

## 4. Análisis Dual de Funciones Clave

### 4.1 `detect_silent_segments_numpy()`

```python
def detect_silent_segments_numpy(audio_path, silence_threshold_db=-40, 
                                  min_silence_ms=300, min_sound_ms=200):
```

**Por qué SÍ se usó esta implementación:**
- ✅ NumPy es extremadamente eficiente para operaciones vectorizadas
- ✅ SciPy.wavfile lee WAV sin dependencias problemáticas
- ✅ Análisis RMS (Root Mean Square) es estándar para detección de volumen
- ✅ Ventana deslizante permite análisis granular sin cargar todo en memoria

**Por qué NO se usaron alternativas:**
- ❌ `pydub`: Usa `audioop` que fue removido en Python 3.13+
- ❌ `librosa`: Dependencia pesada, overkill para esta tarea
- ❌ FFmpeg directo: Más complejo de parsear salida

**Funcionamiento:**
1. Lee archivo WAV con `wavfile.read()`
2. Convierte a mono si es estéreo
3. Normaliza amplitud a rango [-1, 1]
4. Aplica ventana deslizante (20ms) calculando RMS
5. Clasifica ventanas como sonido/silencio
6. Agrupa ventanas contiguas de sonido en segmentos

---

### 4.2 `process_single_video()`

```python
def process_single_video(input_path, output_dir, base_filename, 
                          max_silence, silence_threshold, job_id=None):
```

**Por qué SÍ se implementó así:**
- ✅ División en chunks de 30 min evita agotar RAM
- ✅ Progress updates granulares vía `job_id`
- ✅ Limpieza de recursos con `chunk.close()` y `video.close()`
- ✅ Manejo de videos sin audio (caso edge)

**Por qué NO:**
- ❌ Procesamiento paralelo de chunks: Complejidad de sincronización
- ❌ FFmpeg puro: Menor control sobre la lógica de recorte

**Flujo:**
```
1. Cargar video con MoviePy
2. Calcular número de partes (si > 30 min)
3. Para cada parte:
   a. Extraer chunk
   b. Exportar audio a WAV temporal
   c. Detectar segmentos de sonido
   d. Procesar silencios (acortar, no eliminar)
   e. Concatenar clips resultantes
   f. Renderizar a MP4
   g. Actualizar progreso
4. Retornar estadísticas
```

---

### 4.3 `process_video_async()`

```python
def process_video_async(job_id, input_path, output_dir, base_filename, 
                         max_silence, silence_threshold):
```

**Por qué SÍ Threading:**
- ✅ No bloquea el servidor HTTP
- ✅ Permite SSE de progreso mientras procesa
- ✅ Simple de implementar en Python
- ✅ GIL no afecta porque el trabajo pesado es I/O (FFmpeg)

**Por qué NO:**
- ❌ `asyncio`: MoviePy no es async-native
- ❌ `multiprocessing`: Más complejo compartir `progress_store`
- ❌ Celery: Overkill para app local

---

### 4.4 Lógica de Recorte de Silencios

```python
if gap > max_silence:
    # Silencio largo: recortar a max_silence
    silence_to_keep = max_silence
    # Mantener max_silence/2 al final del anterior
    new_prev_end = min(prev_end + silence_to_keep/2, chunk.duration)
    # El nuevo segmento empieza con max_silence/2 antes del audio
    seg_start = max(s - silence_to_keep/2, 0)
```

**Por qué SÍ esta lógica:**
- ✅ Preserva pausas naturales (no cortes abruptos)
- ✅ Distribución equitativa del silencio restante
- ✅ Usuario controla exactamente cuánto silencio mantener

**Por qué NO eliminar silencios completamente:**
- ❌ Transiciones bruscas entre oraciones
- ❌ Pérdida del ritmo natural del habla
- ❌ Puede sonar "robótico" o editado

---

## 5. Endpoints Críticos

### 5.1 `/api/progress/<job_id>` (SSE)

```python
@app.route('/api/progress/<job_id>')
def get_progress(job_id):
    def generate():
        last_data = None
        timeout = 600  # 10 minutos max
        start = time.time()
        
        while time.time() - start < timeout:
            if job_id in progress_store:
                data = progress_store[job_id]
                if data != last_data:
                    last_data = data.copy()
                    yield f"data: {json.dumps(data)}\n\n"
                if data.get('stage') in ['complete', 'error']:
                    break
            time.sleep(0.3)
    
    return Response(generate(), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
```

**Análisis:**
- `last_data`: Evita enviar duplicados
- `timeout`: Previene conexiones zombies
- `time.sleep(0.3)`: Balance entre responsividad y CPU
- Headers: Previenen buffering que rompería SSE

---

### 5.2 `/api/process/async`

```python
@app.route('/api/process/async', methods=['POST'])
def process_video_async_endpoint():
    # Validaciones...
    
    # Carpeta de salida personalizada
    output_folder = request.form.get('output_folder', '').strip()
    
    if output_folder and os.path.isdir(output_folder):
        output_dir = output_folder
        save_to_custom = True
    elif output_folder:
        os.makedirs(output_folder, exist_ok=True)
        output_dir = output_folder
        save_to_custom = True
    else:
        output_dir = os.path.join(UPLOAD_FOLDER, f"output_{job_id}")
        save_to_custom = False
    
    # Iniciar thread
    thread = threading.Thread(
        target=process_video_async,
        args=(job_id, input_path, output_dir, ...)
    )
    thread.start()
    
    return jsonify({...})
```

**Análisis:**
- Retorna inmediatamente con `job_id`
- Thread procesa en background
- Cliente usa SSE para monitorear progreso

---

## 6. Prueba de Fuego

### 6.1 Bloque `if __name__ == "__main__":`

```python
if __name__ == '__main__':
    print("=" * 60)
    print("✂️  SilenceCutter v3 - Procesamiento por Lotes")
    print("=" * 60)
    print("🌐 http://localhost:5000")
    print("📁 Procesa carpetas completas de videos")
    print("💾 Guarda estado para resumir")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
```

**Parámetros importantes:**
- `debug=True`: Auto-reload en cambios de código
- `host='0.0.0.0'`: Acepta conexiones externas (LAN)
- `port=5000`: Puerto estándar de desarrollo Flask
- `threaded=True`: Múltiples requests simultáneos

### 6.2 Prueba Manual

```bash
# 1. Activar entorno virtual
.\venv\Scripts\activate

# 2. Ejecutar servidor
python app.py

# 3. Verificar health
curl http://localhost:5000/api/health
# Esperado: {"status":"ok"}

# 4. Abrir navegador
start http://localhost:5000
```

---

## 7. Troubleshooting

### 7.1 Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `FFmpeg not found` | FFmpeg no en PATH | Instalar FFmpeg y agregar a PATH |
| `Memory Error` | Video muy largo | Reducir CHUNK_DURATION_MINUTES |
| `Permission denied` | Carpeta de salida protegida | Verificar permisos de escritura |
| `Port 5000 in use` | Otro proceso usando puerto | Cambiar puerto o cerrar conflicto |

### 7.2 Debugging SSE

```python
# Agregar logging temporal
@app.route('/api/progress/<job_id>')
def get_progress(job_id):
    def generate():
        print(f"[SSE] Cliente conectado para job {job_id}")
        while ...:
            print(f"[SSE] Enviando: {progress_store.get(job_id)}")
            yield ...
    return Response(generate(), ...)
```

### 7.3 Verificar Stores

```python
# Agregar endpoint de debug (solo desarrollo)
@app.route('/api/debug/stores')
def debug_stores():
    return jsonify({
        'progress': dict(progress_store),
        'jobs': dict(jobs_store),
        'results': {k: 'exists' for k in results_store.keys()}
    })
```

---

## 8. Consideraciones de Seguridad

| Aspecto | Implementación | Riesgo Residual |
|---------|----------------|-----------------|
| Nombres de archivo | `secure_filename()` | Bajo |
| Rutas de carpeta | Validación básica | Medio (path traversal teórico) |
| Tamaño de archivo | Sin límite | Medio (DoS con archivos enormes) |
| CORS | Habilitado global | Bajo (app local) |

**Nota**: Esta app está diseñada para uso local. No exponer a internet sin agregar autenticación.

---

## Historial de Cambios

| Fecha | Cambio |
|-------|--------|
| 2025-12-26 | Documento inicial - Ingeniería inversa |
