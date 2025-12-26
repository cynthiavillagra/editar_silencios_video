# 03-B - Modelado de Datos

## 1. Diagrama Entidad-Relación (DER)

> Nota: Esta aplicación no usa base de datos tradicional. El DER representa las estructuras de datos en memoria y archivos JSON.

```mermaid
erDiagram
    JOB ||--o{ PART : contains
    JOB {
        string job_id PK
        string status
        string output_dir
        string base_filename
        float total_original_duration
        float total_new_duration
        float time_saved
        float percentage_saved
        int num_parts
    }
    
    PART {
        int part_num PK
        string filename
        string path
        float original_duration
        float new_duration
    }
    
    BATCH ||--o{ BATCH_FILE : contains
    BATCH {
        string batch_id PK
        int total_files
        int completed
        int failed
        int current_index
        json settings
        timestamp created_at
    }
    
    BATCH_FILE {
        int index PK
        string name
        int size
        string status
        json result
        string error
    }
    
    PROGRESS {
        string job_id PK
        string stage
        int percent
        string message
        int part
        int total_parts
        timestamp timestamp
    }
    
    SETTINGS {
        float max_silence
        int sensitivity
        string output_folder
    }
```

---

## 2. Diagrama de Clases

```mermaid
classDiagram
    class FlaskApp {
        +dict progress_store
        +dict results_store
        +dict batch_store
        +dict jobs_store
        +index() Response
        +health() Response
        +get_progress(job_id) Response
        +process_video_endpoint() Response
        +process_video_async_endpoint() Response
        +get_job_status(job_id) Response
        +start_batch() Response
        +process_batch_file(batch_id, file_index) Response
        +download_part(job_id, part_num) Response
        +download_merged(job_id) Response
        +download_all(job_id) Response
        +cleanup(job_id) Response
    }
    
    class VideoProcessor {
        +detect_silent_segments_numpy(audio_path, threshold_db, min_silence, min_sound) list
        +process_single_video(input_path, output_dir, base_filename, max_silence, threshold, job_id) dict
        +process_video_async(job_id, input_path, output_dir, base_filename, max_silence, threshold) void
    }
    
    class ProgressManager {
        +update_progress(job_id, stage, percent, message, kwargs) void
        +get_progress_stream(job_id) Generator
    }
    
    class StateManager {
        +save_state(batch_id, state) string
        +load_state(batch_id) dict
    }
    
    class Utilities {
        +allowed_file(filename) bool
        +format_duration(seconds) string
    }
    
    FlaskApp --> VideoProcessor : uses
    FlaskApp --> ProgressManager : uses
    FlaskApp --> StateManager : uses
    FlaskApp --> Utilities : uses
    
    class FrontendState {
        +string mode
        +array selectedFiles
        +array batchFiles
        +bool isProcessing
        +string batchId
        +dict settings
        +array results
        +handle dirHandle
    }
    
    class FrontendElements {
        +Element modeSwitch
        +Element uploadArea
        +Element progressBar
        +Element downloadOptions
        +Element outputFolder
    }
    
    class FrontendFunctions {
        +processSingle() Promise
        +processBatch() Promise
        +fetchJobResult(jobId) Promise
        +updateProgressBar(percent, message, stage) void
        +renderDownloadOptions(result) void
        +handleSingleFile(file) void
        +handleBatchFiles(files) void
    }
    
    FrontendFunctions --> FrontendState : modifies
    FrontendFunctions --> FrontendElements : updates
```

---

## 3. Estructuras de Datos Detalladas

### 3.1 Progress Store (Backend)

```python
progress_store = {
    "job_id_uuid": {
        "stage": "processing",      # uploading|loading|extracting|analyzing|cutting|rendering|complete|error
        "percent": 45,              # 0-100
        "message": "⚙️ Procesando parte 2/3",
        "timestamp": 1703548800.123,
        "part": 2,                  # Opcional: parte actual
        "total_parts": 3            # Opcional: total de partes
    }
}
```

### 3.2 Results Store (Backend)

```python
results_store = {
    "job_id_uuid": {
        "job_id": "job_id_uuid",
        "output_dir": "C:\\Temp\\output_uuid",
        "base_filename": "video_editado",
        "num_parts": 2,
        "parts": [
            {
                "filename": "video_editado_parte1.mp4",
                "path": "C:\\Temp\\output_uuid\\video_editado_parte1.mp4",
                "part_num": 1,
                "original_duration": 1800.5,
                "new_duration": 1520.3
            },
            {
                "filename": "video_editado_parte2.mp4",
                "path": "C:\\Temp\\output_uuid\\video_editado_parte2.mp4",
                "part_num": 2,
                "original_duration": 1750.2,
                "new_duration": 1480.8
            }
        ],
        "total_original_duration": 3550.7,
        "total_new_duration": 3001.1,
        "total_time_saved": 549.6,
        "percentage_saved": 15.5
    }
}
```

### 3.3 Batch Store (Backend)

```python
batch_store = {
    "batch_id_uuid": {
        "batch_id": "batch_id_uuid",
        "total_files": 5,
        "completed": 2,
        "failed": 0,
        "current_index": 3,
        "files": [
            {"name": "video1.mp4", "size": 104857600, "status": "completed", "result": {...}},
            {"name": "video2.mp4", "size": 209715200, "status": "completed", "result": {...}},
            {"name": "video3.mp4", "size": 157286400, "status": "processing", "result": None},
            {"name": "video4.mp4", "size": 262144000, "status": "pending", "result": None},
            {"name": "video5.mp4", "size": 188743680, "status": "pending", "result": None}
        ],
        "settings": {
            "max_silence": 3.0,
            "sensitivity": 5
        },
        "created_at": 1703548800.0
    }
}
```

### 3.4 Jobs Store (Backend)

```python
jobs_store = {
    "job_id_uuid": {
        "status": "processing",  # processing|completed|error
        "save_to_custom": True,
        "output_folder": "C:\\Videos\\Editados",
        "result": {...}          # Solo cuando status=completed
    }
}
```

### 3.5 Frontend State (JavaScript)

```javascript
const state = {
    mode: 'single',           // 'single' | 'batch'
    selectedFiles: [],        // Array<File>
    batchFiles: [],           // Array<{file, name, size, selected, status}>
    isProcessing: false,
    batchId: null,
    settings: {
        maxSilence: 3.0,      // 0.5 - 10.0
        sensitivity: 5         // 1 - 10
    },
    results: [],              // Array<ResultObject>
    dirHandle: null           // FileSystemDirectoryHandle (optional)
};
```

### 3.6 LocalStorage Schema (Frontend)

```javascript
// Key: 'silencecutter_state'
{
    "batchId": "batch_id_uuid",
    "files": [
        {"name": "video1.mp4", "size": 104857600, "status": "completed"},
        {"name": "video2.mp4", "size": 209715200, "status": "pending"}
    ],
    "settings": {
        "maxSilence": 3.0,
        "sensitivity": 5
    },
    "results": [...]
}
```

---

## 4. Flujo de Datos

### 4.1 Flujo de Procesamiento Single

```mermaid
flowchart TD
    A[Usuario sube video] --> B[Frontend FormData]
    B --> C[POST /api/process/async]
    C --> D[Backend genera job_id]
    D --> E[Thread inicia procesamiento]
    E --> F[update_progress cada etapa]
    F --> G[SSE /api/progress/job_id]
    G --> H[Frontend EventSource recibe]
    H --> I[Actualiza UI progress]
    E --> J[Procesamiento completo]
    J --> K[results_store actualizado]
    K --> L[Frontend GET /api/job/job_id]
    L --> M[Muestra opciones descarga]
```

### 4.2 Flujo de Procesamiento Batch

```mermaid
flowchart TD
    A[Usuario selecciona archivos] --> B[POST /api/batch/start]
    B --> C[Backend crea batch_id]
    C --> D[Loop: por cada archivo]
    D --> E[POST /api/batch/id/process/index]
    E --> F[Procesar archivo individual]
    F --> G[Actualizar batch_store]
    G --> H{Más archivos?}
    H -->|Sí| D
    H -->|No| I[Mostrar resumen]
    
    F --> J[SSE progreso individual]
    J --> K[UI actualiza archivo actual]
    
    G --> L[save_state JSON]
    L --> M[localStorage frontend]
```

---

## 5. Persistencia

### 5.1 Archivos JSON (Server-side)

| Archivo | Ubicación | Contenido |
|---------|-----------|-----------|
| `batch_state_{id}.json` | `%TEMP%/` | Estado del batch para resume |

### 5.2 LocalStorage (Client-side)

| Key | Contenido | TTL |
|-----|-----------|-----|
| `silencecutter_state` | Estado del batch + resultados | Hasta dismiss |

### 5.3 Archivos Temporales

| Tipo | Ubicación | Limpieza |
|------|-----------|----------|
| Input video | `%TEMP%/input_{uuid}_{filename}` | Automática post-proceso |
| Output videos | `%TEMP%/output_{uuid}/` | Manual via `/api/cleanup` |
| Audio WAV temporal | `%TEMP%/{uuid}.wav` | Automática post-análisis |

---

## Historial de Cambios

| Fecha | Cambio |
|-------|--------|
| 2025-12-26 | Documento inicial - Ingeniería inversa |
