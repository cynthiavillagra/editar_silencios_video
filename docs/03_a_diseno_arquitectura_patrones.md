# 03-A - Diseño de Arquitectura y Patrones

## 1. Visión General de la Arquitectura

### 1.1 Tipo de Arquitectura

**Arquitectura Cliente-Servidor con Procesamiento Asíncrono**

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Browser)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   HTML/CSS   │  │  JavaScript │  │  LocalStorage (Resume) │  │
│  │  (UI Layer)  │  │ (App Logic) │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                           │                                      │
│                     HTTP/SSE                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (Flask Server)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  API REST   │  │    SSE      │  │  Threading (Async)      │  │
│  │  Endpoints  │──│  Progress   │──│  Video Processing       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                  VIDEO PROCESSING PIPELINE                   ││
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐ ││
│  │  │ Upload │→ │ Split  │→ │ Audio  │→ │Analyze │→ │ Render │ ││
│  │  │        │  │ Chunks │  │Extract │  │Silence │  │ Output │ ││
│  │  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
│                           │                                      │
│                           ▼                                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐│
│  │  MoviePy      │  │  NumPy/SciPy  │  │  FFmpeg (subprocess)  ││
│  │  (Video I/O)  │  │  (Analysis)   │  │  (Encoding)           ││
│  └───────────────┘  └───────────────┘  └───────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Justificación de la Arquitectura

| Decisión | Por qué SÍ | Por qué NO (alternativas descartadas) |
|----------|------------|--------------------------------------|
| **Cliente-Servidor** | Separación clara de responsabilidades, UI reactiva | Monolítico desktop requeriría GUI framework (Tkinter, PyQt) |
| **Flask** | Ligero, Python nativo, fácil de extender | Django sería overkill para esta aplicación |
| **SSE (no WebSocket)** | Unidireccional suficiente, más simple | WebSocket añade complejidad innecesaria |
| **Threading** | Procesamiento async sin bloquear HTTP | Multiprocessing más complejo para compartir estado |
| **LocalStorage** | Persistencia cliente sin backend DB | Cookies limitadas en tamaño |

---

## 2. Patrones de Diseño Identificados

### 2.1 Singleton Pattern

**Ubicación**: `app.py` - Stores globales

```python
# Almacén de progreso y resultados (Singletons de módulo)
progress_store = {}
results_store = {}
batch_store = {}
jobs_store = {}
```

**Por qué se usó:**
- ✅ Acceso global desde cualquier endpoint
- ✅ Estado compartido entre requests
- ✅ Simple de implementar en Python

**Riesgos:**
- ⚠️ No persiste al reiniciar servidor (mitigado con JSON)
- ⚠️ No thread-safe por defecto (mitigado con GIL y operaciones atómicas)

---

### 2.2 Observer Pattern (via SSE)

**Ubicación**: `app.py` - `/api/progress/<job_id>`, `app.js` - `EventSource`

```python
# Backend: Publicador
def update_progress(job_id, stage, percent, message, **kwargs):
    progress_store[job_id] = {...}

# Endpoint SSE: Stream de eventos
@app.route('/api/progress/<job_id>')
def get_progress(job_id):
    def generate():
        while ...:
            yield f"data: {json.dumps(progress_store[job_id])}\n\n"
    return Response(generate(), mimetype='text/event-stream')
```

```javascript
// Frontend: Suscriptor
eventSource = new EventSource(`/api/progress/${jobId}`);
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateProgressBar(data.percent, data.message, data.stage);
};
```

**Por qué se usó:**
- ✅ Desacoplamiento entre productor (procesamiento) y consumidor (UI)
- ✅ Actualizaciones push sin polling
- ✅ Eficiente en recursos

---

### 2.3 State Machine Pattern

**Ubicación**: `app.py` - Estados de job, `app.js` - Estados de UI

```python
# Estados posibles de un job
jobs_store[job_id] = {
    'status': 'processing' | 'completed' | 'error'
}

# Transiciones en progress_store
progress_store[job_id] = {
    'stage': 'uploading' → 'loading' → 'extracting' → 
             'analyzing' → 'cutting' → 'rendering' → 'complete' | 'error'
}
```

```javascript
// Frontend: Máquina de estados visual
const titles = {
    'uploading': '📤 Subiendo',
    'loading': '📂 Cargando',
    'extracting': '🎵 Extrayendo audio',
    'analyzing': '🔍 Analizando',
    'cutting': '✂️ Recortando',
    'rendering': '🎬 Renderizando',
    'complete': '✅ Completado',
    'error': '❌ Error'
};
```

**Por qué se usó:**
- ✅ Lógica clara de transiciones
- ✅ UI predecible según estado
- ✅ Fácil de debuggear

---

### 2.4 Factory Pattern (implícito)

**Ubicación**: `app.py` - Creación de jobs

```python
def start_batch():
    batch_id = str(uuid.uuid4())
    state = {
        'batch_id': batch_id,
        'total_files': len(files_info),
        'files': [...],
        'settings': {...}
    }
    batch_store[batch_id] = state
    return jsonify({'batch_id': batch_id, 'state': state})
```

**Por qué se usó:**
- ✅ Encapsula lógica de creación de objetos complejos
- ✅ IDs únicos generados consistentemente

---

### 2.5 Pipeline Pattern

**Ubicación**: `app.py` - `process_single_video()`

```
Input → Split → Extract Audio → Analyze Silence → 
    Cut Segments → Render → Output
```

**Implementación:**
```python
def process_single_video(input_path, output_dir, ...):
    # Etapa 1: Cargar
    video = VideoFileClip(input_path)
    
    # Etapa 2: Dividir si es largo
    for part_num in range(1, num_parts + 1):
        chunk = video.subclip(start_time, end_time)
        
        # Etapa 3: Extraer audio
        chunk.audio.write_audiofile(temp_audio, ...)
        
        # Etapa 4: Analizar silencios
        segments = detect_silent_segments_numpy(temp_audio, ...)
        
        # Etapa 5: Cortar y concatenar
        final = concatenate_videoclips(clips, ...)
        
        # Etapa 6: Renderizar
        final.write_videofile(output_path, ...)
```

**Por qué se usó:**
- ✅ Cada etapa es independiente y testeable
- ✅ Fácil añadir/modificar etapas
- ✅ Progreso granular por etapa

---

### 2.6 Memento Pattern (Resume)

**Ubicación**: `app.py` - `save_state()`/`load_state()`, `app.js` - localStorage

```python
# Backend: Guardar estado a disco
def save_state(batch_id, state):
    state_path = os.path.join(UPLOAD_FOLDER, f'batch_state_{batch_id}.json')
    with open(state_path, 'w') as f:
        json.dump(state, f)

def load_state(batch_id):
    with open(state_path, 'r') as f:
        return json.load(f)
```

```javascript
// Frontend: Guardar en localStorage
function saveToLocalStorage(data) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function loadFromLocalStorage() {
    return JSON.parse(localStorage.getItem(STORAGE_KEY));
}
```

**Por qué se usó:**
- ✅ Recuperación ante fallos
- ✅ Persistencia sin base de datos
- ✅ Híbrido cliente-servidor

---

## 3. Capas de la Aplicación

### 3.1 Capa de Presentación (Frontend)

| Componente | Archivo | Responsabilidad |
|------------|---------|-----------------|
| Estructura | `index.html` | Layout y elementos del DOM |
| Estilos | `styles.css` | Tema oscuro, componentes visuales |
| Lógica | `app.js` | Gestión de estado, eventos, API calls |

### 3.2 Capa de Aplicación (Backend)

| Componente | Función | Responsabilidad |
|------------|---------|-----------------|
| Rutas | `@app.route(...)` | Endpoints REST y SSE |
| Servicios | `process_single_video()` | Lógica de negocio |
| Utilidades | `format_duration()`, etc. | Funciones auxiliares |

### 3.3 Capa de Datos (Stores)

| Store | Tipo | Persistencia |
|-------|------|--------------|
| `progress_store` | Dict en memoria | No persiste |
| `results_store` | Dict en memoria | No persiste |
| `jobs_store` | Dict en memoria | No persiste |
| `batch_store` | Dict + JSON | Persiste en disco |
| localStorage | Browser storage | Persiste en cliente |

---

## 4. Decisiones Arquitectónicas Clave

### DA-01: Procesamiento Asíncrono con Threading

**Problema**: El procesamiento de video bloquea el servidor HTTP.

**Solución**: 
```python
thread = threading.Thread(
    target=process_video_async,
    args=(job_id, input_path, ...)
)
thread.start()
return jsonify({'job_id': job_id, 'status': 'processing'})
```

**Alternativas descartadas:**
- Celery: Overkill para app local
- Multiprocessing: Más complejo compartir estado
- Asyncio: MoviePy no es async-native

---

### DA-02: División de Videos Largos

**Problema**: Videos >1 hora agotan la RAM.

**Solución**: Dividir en chunks de 30 minutos.

```python
SPLIT_THRESHOLD_MINUTES = 30
CHUNK_DURATION_MINUTES = 30

if duration_minutes > SPLIT_THRESHOLD_MINUTES:
    num_parts = ceil(duration_minutes / CHUNK_DURATION_MINUTES)
```

**Trade-off**: Más archivos de salida, pero procesamiento estable.

---

### DA-03: Recortar, No Eliminar Silencios

**Problema**: Usuario quiere mantener pausas naturales.

**Solución**: Silencio > umbral → recortar A umbral, no eliminar.

```python
if gap > max_silence:
    # Mantener max_silence/2 al final del anterior
    # + max_silence/2 al inicio del siguiente
    silence_to_keep = max_silence
```

**Beneficio**: Transiciones suaves, contenido natural.

---

## 5. Dependencias Externas

| Dependencia | Versión | Propósito | Alternativa |
|-------------|---------|-----------|-------------|
| Flask | 3.0+ | Framework web | FastAPI |
| MoviePy | 1.0+ | Edición de video | FFmpeg directo |
| NumPy | 1.26+ | Análisis numérico | - |
| SciPy | 1.11+ | Lectura de WAV | pydub (no compatible 3.14) |
| Flask-CORS | 4.0+ | CORS headers | Middleware manual |
| Werkzeug | 3.0+ | Utilidades web | - |

---

## Historial de Cambios

| Fecha | Cambio |
|-------|--------|
| 2025-12-26 | Documento inicial - Ingeniería inversa |
