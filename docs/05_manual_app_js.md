# 05 - Manual Técnico: app.js (Frontend)

## 1. Información General

| Campo | Valor |
|-------|-------|
| **Archivo** | `static/js/app.js` |
| **Módulo** | Frontend / Cliente |
| **Líneas** | ~850 |
| **Lenguaje** | JavaScript ES6+ |
| **Dependencias** | Ninguna (Vanilla JS) |

---

## 2. Trazabilidad

| Elemento | Referencia |
|----------|------------|
| **Requisitos** | RF01-RF14 |
| **Historias de Usuario** | HU-01 a HU-06 |
| **Casos de Uso** | CU-01, CU-02 |
| **Patrones** | State Machine, Observer, Memento |

---

## 3. Estrategia de Construcción

### 3.1 Estructura del Archivo

```
app.js
├── Constantes y Storage (líneas 1-60)
│   ├── STORAGE_KEY
│   ├── saveToLocalStorage()
│   ├── loadFromLocalStorage()
│   └── clearLocalStorage()
│
├── Elementos del DOM (líneas 61-130)
│   └── const elements = { ... }
│
├── Estado Global (líneas 131-145)
│   └── const state = { ... }
│
├── Funciones UI (líneas 146-280)
│   ├── showSection()
│   ├── updateProgressBar()
│   ├── showError()
│   └── resetApp()
│
├── Manejo de Archivos (líneas 281-350)
│   ├── handleSingleFile()
│   ├── handleBatchFiles()
│   ├── formatFileSize()
│   └── renderBatchFilesList()
│
├── Procesamiento Single (líneas 351-430)
│   ├── processSingle()
│   └── fetchJobResult()
│
├── Procesamiento Batch (líneas 431-580)
│   ├── processBatch()
│   └── showBatchResults()
│
├── Descarga (líneas 581-660)
│   ├── renderDownloadOptions()
│   └── downloadResult()
│
├── Resume (líneas 661-720)
│   ├── checkForResume()
│   ├── resumeProcessing()
│   └── dismissResume()
│
├── Event Listeners (líneas 721-830)
│   └── Todos los addEventListener
│
└── Inicialización (líneas 831-850)
    └── DOMContentLoaded handler
```

### 3.2 Sin Dependencias Externas

**Por qué SÍ Vanilla JS:**
- ✅ Zero dependencias = zero vulnerabilidades de terceros
- ✅ Bundle size mínimo
- ✅ Control total sobre comportamiento
- ✅ Apropiado para una app de esta complejidad

**Por qué NO React/Vue:**
- ❌ Overkill para una SPA simple
- ❌ Requiere build step (webpack, vite)
- ❌ Curva de aprendizaje innecesaria para el scope

---

## 4. Análisis Dual de Componentes Clave

### 4.1 Estado Global

```javascript
const state = {
    mode: 'single',        // 'single' | 'batch'
    selectedFiles: [],     // File objects
    batchFiles: [],        // {file, name, size, selected, status}
    isProcessing: false,
    batchId: null,
    settings: {
        maxSilence: 3.0,
        sensitivity: 5
    },
    results: [],
    dirHandle: null        // File System Access API handle
};
```

**Por qué SÍ un objeto global:**
- ✅ Simple de acceder desde cualquier función
- ✅ Estado centralizado = debugging fácil
- ✅ No requiere prop drilling como en React

**Riesgos:**
- ⚠️ Mutación no controlada (mitigado con funciones wrapper)
- ⚠️ No hay reactividad automática (actualizamos UI manualmente)

---

### 4.2 SSE con EventSource

```javascript
async function processSingle() {
    // ...
    const startResponse = await fetch('/api/process/async', {
        method: 'POST',
        body: formData
    });
    const startResult = await startResponse.json();
    jobId = startResult.job_id;
    
    // Conectar SSE
    eventSource = new EventSource(`/api/progress/${jobId}`);
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateProgressBar(data.percent, data.message, data.stage);
        
        if (data.stage === 'complete') {
            eventSource.close();
            fetchJobResult(jobId);
        }
    };
    
    eventSource.onerror = () => {
        if (!completed) {
            setTimeout(() => fetchJobResult(jobId), 1000);
        }
        eventSource.close();
    };
}
```

**Por qué SÍ EventSource:**
- ✅ API nativa del browser
- ✅ Reconexión automática
- ✅ Más simple que WebSocket para unidireccional

**Por qué NO polling:**
- ❌ Ineficiente (muchas requests)
- ❌ Latencia (mínimo intervalo humano)
- ❌ Mayor carga en servidor

---

### 4.3 LocalStorage para Resume

```javascript
const STORAGE_KEY = 'silencecutter_state';

function saveToLocalStorage(data) {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch (e) {
        console.warn('No se pudo guardar en localStorage:', e);
    }
}

function loadFromLocalStorage() {
    try {
        const saved = localStorage.getItem(STORAGE_KEY);
        return saved ? JSON.parse(saved) : null;
    } catch (e) {
        console.warn('No se pudo cargar de localStorage:', e);
        return null;
    }
}
```

**Por qué SÍ localStorage:**
- ✅ Persiste entre sesiones
- ✅ ~5MB de espacio
- ✅ API sincrónica simple

**Por qué NO IndexedDB:**
- ❌ Más complejo (async, transacciones)
- ❌ Overkill para datos pequeños

**Por qué NO sessionStorage:**
- ❌ Se borra al cerrar pestaña (no útil para resume)

---

### 4.4 File System Access API

```javascript
elements.browseFolder?.addEventListener('click', async () => {
    if ('showDirectoryPicker' in window) {
        try {
            const dirHandle = await window.showDirectoryPicker({
                mode: 'readwrite'
            });
            elements.outputFolder.value = dirHandle.name;
            state.dirHandle = dirHandle;
            alert('Carpeta seleccionada: ' + dirHandle.name);
        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error('Error:', err);
            }
        }
    } else {
        alert('Tu navegador no soporta el selector de carpetas.');
    }
});
```

**Por qué SÍ esta API:**
- ✅ Selector nativo del SO
- ✅ UX familiar para el usuario

**Limitaciones:**
- ⚠️ Solo Chrome/Edge (no Firefox/Safari)
- ⚠️ No retorna path completo por seguridad
- ⚠️ Por eso pedimos escribir ruta manualmente

---

### 4.5 Cálculo de Decibeles

```javascript
function sensitivityToDb(sensitivity) {
    return Math.round(-25 - (sensitivity - 1) * 3.33);
}

// Resultado:
// 1 → -25 dB
// 5 → -38 dB
// 10 → -55 dB
```

**Por qué esta fórmula:**
- ✅ Rango de -25 a -55 dB cubre casos de uso típicos
- ✅ Lineal = fácil de entender para usuarios
- ✅ Consistente con el backend

---

## 5. Funciones de UI Críticas

### 5.1 `updateProgressBar()`

```javascript
function updateProgressBar(percent, message, stage) {
    if (elements.progressBar) {
        elements.progressBar.style.width = `${percent}%`;
    }
    if (elements.progressPercent) {
        elements.progressPercent.textContent = `${Math.round(percent)}%`;
    }
    if (elements.progressMessage) {
        elements.progressMessage.textContent = message;
    }
}
```

**Análisis:**
- Actualiza 3 elementos independientes
- Optional chaining (`?.`) previene errores si elementos no existen
- Porcentaje redondeado para mejor legibilidad

### 5.2 `renderDownloadOptions()`

```javascript
function renderDownloadOptions(result) {
    const numParts = result.num_parts || 1;
    const outputFolder = result.output_dir || '';
    
    // Detectar si se guardó en carpeta personalizada
    const savedToCustomFolder = outputFolder && 
        !outputFolder.includes('\\Temp\\') && 
        !outputFolder.includes('/tmp/');

    if (savedToCustomFolder) {
        // Mostrar mensaje de "archivos guardados"
    } else if (numParts > 1) {
        // Mostrar opciones: todo junto, ZIP, partes
    } else {
        // Mostrar botón simple de descarga
    }
}
```

**Lógica:**
1. Si guardó en carpeta custom → No mostrar descarga, solo confirmar ubicación
2. Si tiene múltiples partes → Mostrar 3 opciones
3. Si es video único → Botón simple

---

## 6. Prueba de Fuego

### 6.1 Inicialización

```javascript
document.addEventListener('DOMContentLoaded', () => {
    checkForResume();  // Verificar si hay batch pendiente
    fetch('/api/health')
        .then(r => r.json())
        .then(() => console.log('✅ Servidor OK'));
});

console.log('🎬 SilenceCutter v3 - Batch Processing');
```

**Flujo de arranque:**
1. DOM cargado
2. Verificar localStorage para resume banner
3. Health check al servidor
4. App lista para uso

### 6.2 Prueba Manual en Consola

```javascript
// Abrir DevTools (F12) y probar:

// Ver estado actual
console.log(state);

// Verificar elementos cargados
console.log(elements);

// Simular actualización de progreso
updateProgressBar(50, '⚙️ Prueba', 'processing');

// Ver localStorage
console.log(loadFromLocalStorage());
```

---

## 7. Troubleshooting

### 7.1 Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `elements.X is null` | Elemento no existe en HTML | Verificar ID en index.html |
| `EventSource failed` | Servidor no corriendo | Iniciar `python app.py` |
| `localStorage quota` | Demasiados datos | Limpiar con `clearLocalStorage()` |
| `Fetch failed` | CORS o red | Verificar que servidor corre en localhost |

### 7.2 Debugging SSE

```javascript
// En la consola del browser:
const es = new EventSource('/api/progress/test-job-id');
es.onmessage = (e) => console.log('SSE:', JSON.parse(e.data));
es.onerror = (e) => console.error('SSE Error:', e);
```

### 7.3 Verificar Estado

```javascript
// Agregar al final de app.js para debugging:
window.debugSilenceCutter = {
    state,
    elements,
    saveToLocalStorage,
    loadFromLocalStorage,
    clearLocalStorage
};

// Usar desde consola:
window.debugSilenceCutter.state
```

---

## 8. Patrones de Código

### 8.1 Optional Chaining

```javascript
// Usado extensivamente para elementos opcionales
elements.progressBar?.style.width = `${percent}%`;
elements.resumeBanner?.classList.add('hidden');
```

### 8.2 Async/Await

```javascript
async function processSingle() {
    try {
        const response = await fetch('/api/process/async', {...});
        const result = await response.json();
        // ...
    } catch (error) {
        showError(`Error: ${error.message}`);
    }
}
```

### 8.3 Template Literals para HTML

```javascript
elements.downloadOptions.innerHTML = `
    <div class="download-header">
        <h4>📦 Opciones de Descarga</h4>
        <p>Video dividido en ${numParts} partes</p>
    </div>
    ${result.parts.map(p => `
        <div class="part-item">
            <span>Parte ${p.part_num}</span>
        </div>
    `).join('')}
`;
```

---

## 9. Consideraciones de Performance

| Aspecto | Implementación |
|---------|----------------|
| DOM Updates | Mínimas, solo cuando cambia estado |
| Event Delegation | No usado (pocos elementos) |
| Memory Leaks | EventSource.close() en cleanup |
| Bundle Size | ~30KB sin minificar |

---

## Historial de Cambios

| Fecha | Cambio |
|-------|--------|
| 2025-12-26 | Documento inicial - Ingeniería inversa |
