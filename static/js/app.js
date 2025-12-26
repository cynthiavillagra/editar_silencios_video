/**
 * SilenceCutter v3 - Procesamiento por Lotes
 * ==========================================
 * - Selección múltiple de archivos o carpeta
 * - Procesamiento en cola uno a uno
 * - Guardado de estado para resumir
 */

// =============================================================================
// Estado de la Aplicación
// =============================================================================
const state = {
    mode: 'single', // 'single' o 'batch'
    selectedFiles: [],
    batchId: null,
    currentFileIndex: 0,
    results: [],
    isProcessing: false,
    settings: {
        maxSilence: 3.0,
        sensitivity: 5
    }
};

// Persistencia en localStorage
const STORAGE_KEY = 'silencecutter_batch_state';

function saveToLocalStorage() {
    const saveState = {
        batchId: state.batchId,
        currentFileIndex: state.currentFileIndex,
        results: state.results,
        settings: state.settings,
        files: state.selectedFiles.map(f => ({
            name: f.name,
            size: f.size,
            status: f.status || 'pending'
        })),
        savedAt: Date.now()
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(saveState));
}

function loadFromLocalStorage() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
        try {
            return JSON.parse(saved);
        } catch {
            return null;
        }
    }
    return null;
}

function clearLocalStorage() {
    localStorage.removeItem(STORAGE_KEY);
}

// =============================================================================
// Elementos del DOM
// =============================================================================
const elements = {
    // Modo
    modeSwitch: document.getElementById('modeSwitch'),
    singleMode: document.getElementById('singleMode'),
    batchMode: document.getElementById('batchMode'),

    // Upload
    uploadArea: document.getElementById('uploadArea'),
    videoInput: document.getElementById('videoInput'),
    folderInput: document.getElementById('folderInput'),
    filePreview: document.getElementById('filePreview'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    removeFile: document.getElementById('removeFile'),

    // Batch
    batchUploadArea: document.getElementById('batchUploadArea'),
    batchFilesList: document.getElementById('batchFilesList'),
    batchCount: document.getElementById('batchCount'),
    selectAllBtn: document.getElementById('selectAllBtn'),
    clearSelectionBtn: document.getElementById('clearSelectionBtn'),

    // Settings
    maxSilence: document.getElementById('maxSilence'),
    maxSilenceValue: document.getElementById('maxSilenceValue'),
    sensitivity: document.getElementById('sensitivity'),
    sensitivityValue: document.getElementById('sensitivityValue'),
    outputFolder: document.getElementById('outputFolder'),
    browseFolder: document.getElementById('browseFolder'),

    // Actions
    processBtn: document.getElementById('processBtn'),

    // Progress
    progressSection: document.getElementById('progressSection'),
    progressTitle: document.getElementById('progressTitle'),
    progressMessage: document.getElementById('progressMessage'),
    progressBar: document.getElementById('progressBar'),
    progressPercent: document.getElementById('progressPercent'),
    batchProgressInfo: document.getElementById('batchProgressInfo'),

    // Results
    resultsSection: document.getElementById('resultsSection'),
    downloadOptions: document.getElementById('downloadOptions'),
    batchResults: document.getElementById('batchResults'),

    // Error
    errorSection: document.getElementById('errorSection'),
    errorMessage: document.getElementById('errorMessage'),
    retryBtn: document.getElementById('retryBtn'),

    // Resume
    resumeBanner: document.getElementById('resumeBanner'),
    resumeInfo: document.getElementById('resumeInfo'),
    resumeBtn: document.getElementById('resumeBtn'),
    dismissResumeBtn: document.getElementById('dismissResumeBtn'),

    // New
    newVideoBtn: document.getElementById('newVideoBtn'),

    // Stats
    originalDuration: document.getElementById('originalDuration'),
    newDuration: document.getElementById('newDuration'),
    timeSaved: document.getElementById('timeSaved'),
    percentageSaved: document.getElementById('percentageSaved')
};

// =============================================================================
// Utilidades
// =============================================================================

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hrs > 0) return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function showSection(section) {
    ['progressSection', 'resultsSection', 'errorSection'].forEach(s => {
        if (elements[s]) elements[s].classList.add('hidden');
    });
    if (section && elements[section]) elements[section].classList.remove('hidden');
}

function updateProgressBar(percent, message, stage) {
    if (elements.progressBar) elements.progressBar.style.width = `${percent}%`;
    if (elements.progressPercent) elements.progressPercent.textContent = `${Math.round(percent)}%`;
    if (elements.progressMessage) elements.progressMessage.textContent = message;
}

function isValidVideo(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    return ['mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv'].includes(ext);
}

// =============================================================================
// Modo Single/Batch
// =============================================================================

function switchMode(mode) {
    state.mode = mode;

    if (mode === 'single') {
        elements.singleMode?.classList.add('active');
        elements.batchMode?.classList.remove('active');
        document.querySelector('.single-upload')?.classList.remove('hidden');
        document.querySelector('.batch-upload')?.classList.add('hidden');
    } else {
        elements.singleMode?.classList.remove('active');
        elements.batchMode?.classList.add('active');
        document.querySelector('.single-upload')?.classList.add('hidden');
        document.querySelector('.batch-upload')?.classList.remove('hidden');
    }

    resetApp();
}

// =============================================================================
// Manejo de Archivos - Single
// =============================================================================

function handleSingleFile(file) {
    if (!file || !isValidVideo(file)) {
        showError('Formato no válido');
        return;
    }

    state.selectedFiles = [file];
    elements.uploadArea?.classList.add('hidden');
    elements.filePreview?.classList.remove('hidden');
    if (elements.fileName) elements.fileName.textContent = file.name;
    if (elements.fileSize) elements.fileSize.textContent = formatBytes(file.size);
    if (elements.processBtn) elements.processBtn.disabled = false;
}

// =============================================================================
// Manejo de Archivos - Batch
// =============================================================================

function handleBatchFiles(files) {
    const validFiles = Array.from(files).filter(isValidVideo);

    if (validFiles.length === 0) {
        showError('No se encontraron videos válidos');
        return;
    }

    // Agregar estado a cada archivo
    state.selectedFiles = validFiles.map(f => {
        f.status = 'pending';
        f.selected = true;
        return f;
    });

    renderBatchFilesList();
    if (elements.processBtn) elements.processBtn.disabled = false;
}

function renderBatchFilesList() {
    if (!elements.batchFilesList) return;

    const selected = state.selectedFiles.filter(f => f.selected);
    if (elements.batchCount) {
        elements.batchCount.textContent = `${selected.length} videos seleccionados`;
    }

    elements.batchFilesList.innerHTML = '';

    state.selectedFiles.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = `batch-file-item ${file.selected ? 'selected' : ''} ${file.status || ''}`;
        item.innerHTML = `
            <label class="file-checkbox">
                <input type="checkbox" ${file.selected ? 'checked' : ''} data-index="${index}">
                <span class="checkmark"></span>
            </label>
            <div class="file-info">
                <span class="file-name">${file.name}</span>
                <span class="file-size">${formatBytes(file.size)}</span>
            </div>
            <span class="file-status">
                ${file.status === 'completed' ? '✅' :
                file.status === 'processing' ? '⏳' :
                    file.status === 'failed' ? '❌' : '⏸️'}
            </span>
        `;

        item.querySelector('input').addEventListener('change', (e) => {
            state.selectedFiles[index].selected = e.target.checked;
            renderBatchFilesList();
        });

        elements.batchFilesList.appendChild(item);
    });

    // Ocultar área de upload, mostrar lista
    elements.batchUploadArea?.classList.add('hidden');
    document.querySelector('.batch-files-container')?.classList.remove('hidden');
}

function selectAllFiles(select) {
    state.selectedFiles.forEach(f => f.selected = select);
    renderBatchFilesList();
}

// =============================================================================
// Procesamiento - Single
// =============================================================================

async function processSingle() {
    const file = state.selectedFiles[0];
    if (!file) return;

    state.isProcessing = true;
    showSection('progressSection');
    elements.processBtn.disabled = true;
    updateProgressBar(0, '📤 Subiendo video...', 'uploading');

    const formData = new FormData();
    formData.append('video', file);
    formData.append('max_silence', state.settings.maxSilence);
    formData.append('sensitivity', state.settings.sensitivity);

    // Carpeta de salida opcional
    const outputFolder = elements.outputFolder?.value?.trim() || '';
    if (outputFolder) {
        formData.append('output_folder', outputFolder);
    }

    let eventSource = null;
    let jobId = null;
    let completed = false;

    try {
        // 1. Enviar archivo y recibir job_id
        updateProgressBar(2, '📤 Enviando video al servidor...', 'uploading');

        const startResponse = await fetch('/api/process/async', {
            method: 'POST',
            body: formData
        });

        const startResult = await startResponse.json();

        if (!startResponse.ok || !startResult.success) {
            showError(startResult.error || 'Error al iniciar procesamiento');
            return;
        }

        jobId = startResult.job_id;

        // 2. Conectar SSE para escuchar progreso en tiempo real
        updateProgressBar(5, '🔗 Conectando para ver progreso...', 'uploading');

        eventSource = new EventSource(`/api/progress/${jobId}`);

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                // Actualizar barra de progreso
                updateProgressBar(data.percent, data.message, data.stage);

                // Actualizar título con info de partes
                if (data.part && data.total_parts && data.total_parts > 1 && elements.progressTitle) {
                    elements.progressTitle.textContent = `⚙️ Parte ${data.part}/${data.total_parts}`;
                } else if (elements.progressTitle) {
                    const titles = {
                        'uploading': '📤 Subiendo',
                        'loading': '📂 Cargando',
                        'extracting': '🎵 Extrayendo audio',
                        'analyzing': '🔍 Analizando',
                        'cutting': '✂️ Recortando',
                        'rendering': '🎬 Renderizando',
                        'processing': '⚙️ Procesando',
                        'complete': '✅ Completado',
                        'error': '❌ Error'
                    };
                    elements.progressTitle.textContent = titles[data.stage] || 'Procesando...';
                }

                // Si completó o error, cerrar SSE
                if (data.stage === 'complete') {
                    completed = true;
                    eventSource.close();
                    // Obtener resultado final
                    fetchJobResult(jobId);
                } else if (data.stage === 'error') {
                    eventSource.close();
                    showError(data.message);
                }
            } catch (e) {
                console.error('Error parsing SSE:', e);
            }
        };

        eventSource.onerror = () => {
            if (!completed) {
                // Puede ser que el servidor terminó, verificar estado
                setTimeout(() => fetchJobResult(jobId), 1000);
            }
            eventSource.close();
        };

    } catch (error) {
        showError(`Error: ${error.message}`);
        state.isProcessing = false;
        elements.processBtn.disabled = false;
        if (eventSource) eventSource.close();
    }
}

/**
 * Obtiene el resultado de un job completo
 */
async function fetchJobResult(jobId) {
    try {
        const response = await fetch(`/api/job/${jobId}`);
        const data = await response.json();

        if (data.status === 'completed' && data.result) {
            state.results = [data.result];

            if (data.result.num_parts > 1 && elements.progressTitle) {
                elements.progressTitle.textContent = `✅ Procesado en ${data.result.num_parts} partes`;
            }

            await new Promise(r => setTimeout(r, 500));
            showSingleResult(data.result);
        } else if (data.status === 'error') {
            showError(data.error || 'Error en procesamiento');
        } else if (data.status === 'processing') {
            // Todavía procesando, esperar y reintentar
            setTimeout(() => fetchJobResult(jobId), 2000);
        } else {
            showError('Estado desconocido');
        }
    } catch (error) {
        showError(`Error obteniendo resultado: ${error.message}`);
    } finally {
        state.isProcessing = false;
        elements.processBtn.disabled = false;
    }
}

function showSingleResult(result) {
    if (elements.originalDuration) elements.originalDuration.textContent = formatDuration(result.total_original_duration);
    if (elements.newDuration) elements.newDuration.textContent = formatDuration(result.total_new_duration);
    if (elements.timeSaved) elements.timeSaved.textContent = formatDuration(result.total_time_saved);
    if (elements.percentageSaved) elements.percentageSaved.textContent = `${result.percentage_saved}%`;

    renderDownloadOptions(result);
    showSection('resultsSection');
}

// =============================================================================
// Procesamiento - Batch
// =============================================================================

async function processBatch() {
    const filesToProcess = state.selectedFiles.filter(f => f.selected && f.status !== 'completed');

    if (filesToProcess.length === 0) {
        showError('No hay archivos para procesar');
        return;
    }

    state.isProcessing = true;
    showSection('progressSection');
    elements.processBtn.disabled = true;

    // Iniciar batch en el servidor
    const filesInfo = filesToProcess.map(f => ({ name: f.name, size: f.size }));

    try {
        const startResponse = await fetch('/api/batch/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                files: filesInfo,
                max_silence: state.settings.maxSilence,
                sensitivity: state.settings.sensitivity
            })
        });

        const startResult = await startResponse.json();
        state.batchId = startResult.batch_id;

        // Procesar cada archivo
        for (let i = 0; i < state.selectedFiles.length; i++) {
            const file = state.selectedFiles[i];

            if (!file.selected || file.status === 'completed') continue;

            file.status = 'processing';
            renderBatchFilesList();

            const batchPercent = (i / state.selectedFiles.length) * 100;
            updateProgressBar(batchPercent, `⚙️ Procesando ${i + 1}/${state.selectedFiles.length}: ${file.name}`, 'processing');

            if (elements.batchProgressInfo) {
                elements.batchProgressInfo.textContent = `Archivo ${i + 1} de ${state.selectedFiles.length}`;
                elements.batchProgressInfo.classList.remove('hidden');
            }

            try {
                const formData = new FormData();
                formData.append('video', file);

                const response = await fetch(`/api/batch/${state.batchId}/process/${i}`, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    file.status = 'completed';
                    file.result = result.result;
                    state.results.push(result.result);
                } else {
                    file.status = 'failed';
                    file.error = result.error;
                }
            } catch (error) {
                file.status = 'failed';
                file.error = error.message;
            }

            renderBatchFilesList();
            saveToLocalStorage();
        }

        // Mostrar resultados
        showBatchResults();

    } catch (error) {
        showError(`Error iniciando batch: ${error.message}`);
    } finally {
        state.isProcessing = false;
        elements.processBtn.disabled = false;
    }
}

function showBatchResults() {
    const completed = state.selectedFiles.filter(f => f.status === 'completed');
    const failed = state.selectedFiles.filter(f => f.status === 'failed');

    // Calcular totales
    let totalOriginal = 0, totalNew = 0;
    completed.forEach(f => {
        if (f.result) {
            totalOriginal += f.result.total_original_duration || 0;
            totalNew += f.result.total_new_duration || 0;
        }
    });

    if (elements.originalDuration) elements.originalDuration.textContent = formatDuration(totalOriginal);
    if (elements.newDuration) elements.newDuration.textContent = formatDuration(totalNew);
    if (elements.timeSaved) elements.timeSaved.textContent = formatDuration(totalOriginal - totalNew);
    if (elements.percentageSaved) {
        const pct = totalOriginal > 0 ? ((1 - totalNew / totalOriginal) * 100).toFixed(1) : 0;
        elements.percentageSaved.textContent = `${pct}%`;
    }

    // Renderizar lista de resultados
    if (elements.batchResults) {
        elements.batchResults.innerHTML = `
            <div class="batch-summary">
                <span class="success">✅ ${completed.length} completados</span>
                ${failed.length > 0 ? `<span class="failed">❌ ${failed.length} fallidos</span>` : ''}
            </div>
            <div class="batch-results-list">
                ${completed.map(f => `
                    <div class="result-item">
                        <span class="result-name">${f.name}</span>
                        <div class="result-actions">
                            <button onclick="downloadResult('${f.result?.job_id}', 'merged')">⬇️ Descargar</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        elements.batchResults.classList.remove('hidden');
    }

    showSection('resultsSection');
    clearLocalStorage();
}

// =============================================================================
// Descarga
// =============================================================================

function renderDownloadOptions(result) {
    if (!elements.downloadOptions) return;

    const numParts = result.num_parts || 1;
    const outputFolder = result.output_dir || '';

    // Verificar si se guardó en carpeta personalizada
    const savedToCustomFolder = outputFolder && !outputFolder.includes('\\Temp\\') && !outputFolder.includes('/tmp/');

    if (savedToCustomFolder) {
        // Los archivos ya están en la carpeta del usuario
        elements.downloadOptions.innerHTML = `
            <div class="download-header saved-locally">
                <h4>✅ Archivos guardados</h4>
                <p class="download-info folder-path">📁 ${outputFolder}</p>
            </div>
            <div class="saved-files-list">
                ${result.parts.map(p => `
                    <div class="saved-file-item">
                        <span class="file-icon">🎬</span>
                        <span class="file-name">${p.filename}</span>
                        <span class="file-duration">${formatDuration(p.new_duration)}</span>
                    </div>
                `).join('')}
            </div>
            <p class="saved-note">Los archivos están listos en tu carpeta</p>
        `;
    } else if (numParts > 1) {
        elements.downloadOptions.innerHTML = `
            <div class="download-header">
                <h4>📦 Opciones de Descarga</h4>
                <p class="download-info">Video dividido en ${numParts} partes</p>
            </div>
            <div class="download-buttons">
                <button class="btn-download-main" onclick="downloadResult('${result.job_id}', 'merged')">
                    <span class="btn-icon">🎬</span>
                    <span class="btn-text">Todo Junto</span>
                </button>
                <button class="btn-download-alt" onclick="downloadResult('${result.job_id}', 'all')">
                    <span class="btn-icon">📂</span>
                    <span class="btn-text">ZIP Partes</span>
                </button>
            </div>
            <div class="parts-section">
                <h5>Partes individuales:</h5>
                <div class="parts-list">
                    ${result.parts.map(p => `
                        <div class="part-item">
                            <span>Parte ${p.part_num} (${formatDuration(p.new_duration)})</span>
                            <button onclick="downloadResult('${result.job_id}', 'part', ${p.part_num})">⬇️</button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    } else {
        elements.downloadOptions.innerHTML = `
            <div class="download-buttons single">
                <button class="btn-download-main" onclick="downloadResult('${result.job_id}', 'merged')">
                    <span class="btn-icon">⬇️</span>
                    <span class="btn-text">Descargar Video</span>
                </button>
            </div>
        `;
    }
}

function downloadResult(jobId, type, partNum = null) {
    let url = `/api/download/${jobId}/${type}`;
    if (type === 'part' && partNum) url = `/api/download/${jobId}/part/${partNum}`;
    window.location.href = url;
}

// =============================================================================
// Resume
// =============================================================================

function checkForResume() {
    const saved = loadFromLocalStorage();
    if (saved && saved.files && saved.files.some(f => f.status === 'pending')) {
        const pending = saved.files.filter(f => f.status === 'pending').length;
        const completed = saved.files.filter(f => f.status === 'completed').length;

        if (elements.resumeBanner) {
            elements.resumeBanner.classList.remove('hidden');
            if (elements.resumeInfo) {
                elements.resumeInfo.textContent = `${completed}/${saved.files.length} videos procesados. ¿Continuar?`;
            }
        }
    }
}

function resumeProcessing() {
    // TODO: Implementar resume desde localStorage
    const saved = loadFromLocalStorage();
    if (saved) {
        state.batchId = saved.batchId;
        state.settings = saved.settings;
        state.results = saved.results || [];

        // Necesitamos que el usuario vuelva a seleccionar los archivos
        alert('Por favor, vuelve a seleccionar los mismos archivos para continuar el procesamiento.');
        switchMode('batch');
    }
    elements.resumeBanner?.classList.add('hidden');
}

function dismissResume() {
    clearLocalStorage();
    elements.resumeBanner?.classList.add('hidden');
}

// =============================================================================
// Error y Reset
// =============================================================================

function showError(message) {
    if (elements.errorMessage) elements.errorMessage.textContent = message;
    showSection('errorSection');
}

function resetApp() {
    state.selectedFiles = [];
    state.results = [];
    state.batchId = null;
    state.currentFileIndex = 0;
    state.isProcessing = false;

    elements.uploadArea?.classList.remove('hidden');
    elements.filePreview?.classList.add('hidden');
    elements.batchUploadArea?.classList.remove('hidden');
    document.querySelector('.batch-files-container')?.classList.add('hidden');

    if (elements.batchFilesList) elements.batchFilesList.innerHTML = '';
    if (elements.batchResults) elements.batchResults.classList.add('hidden');
    if (elements.processBtn) elements.processBtn.disabled = true;
    if (elements.progressBar) elements.progressBar.style.width = '0%';

    showSection(null);
}

// =============================================================================
// Event Listeners
// =============================================================================

// Modo switch
elements.singleMode?.addEventListener('click', () => switchMode('single'));
elements.batchMode?.addEventListener('click', () => switchMode('batch'));

// Single upload
elements.uploadArea?.addEventListener('click', () => elements.videoInput?.click());
elements.uploadArea?.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.uploadArea.classList.add('drag-over');
});
elements.uploadArea?.addEventListener('dragleave', () => elements.uploadArea.classList.remove('drag-over'));
elements.uploadArea?.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
        if (state.mode === 'single') {
            handleSingleFile(e.dataTransfer.files[0]);
        } else {
            handleBatchFiles(e.dataTransfer.files);
        }
    }
});

elements.videoInput?.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        if (state.mode === 'single') {
            handleSingleFile(e.target.files[0]);
        } else {
            handleBatchFiles(e.target.files);
        }
    }
});

// Batch upload
elements.batchUploadArea?.addEventListener('click', () => elements.folderInput?.click());
elements.folderInput?.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleBatchFiles(e.target.files);
});

// Remove file
elements.removeFile?.addEventListener('click', (e) => {
    e.stopPropagation();
    resetApp();
});

// Batch selection
elements.selectAllBtn?.addEventListener('click', () => selectAllFiles(true));
elements.clearSelectionBtn?.addEventListener('click', () => selectAllFiles(false));

// Settings
elements.maxSilence?.addEventListener('input', (e) => {
    state.settings.maxSilence = parseFloat(e.target.value);
    if (elements.maxSilenceValue) elements.maxSilenceValue.textContent = `${e.target.value}s`;
});

/**
 * Calcula los decibeles según la sensibilidad
 * Fórmula: -25 - (sensitivity - 1) * 3.33
 */
function sensitivityToDb(sensitivity) {
    return Math.round(-25 - (sensitivity - 1) * 3.33);
}

elements.sensitivity?.addEventListener('input', (e) => {
    const sens = parseInt(e.target.value);
    state.settings.sensitivity = sens;
    const db = sensitivityToDb(sens);
    if (elements.sensitivityValue) {
        elements.sensitivityValue.textContent = `${sens} (${db} dB)`;
    }
});

// Browse folder - usa File System Access API si está disponible
elements.browseFolder?.addEventListener('click', async () => {
    // Verificar si el navegador soporta la API
    if ('showDirectoryPicker' in window) {
        try {
            const dirHandle = await window.showDirectoryPicker({
                mode: 'readwrite'
            });
            // Obtener la ruta (solo funciona en algunos contextos)
            // Como fallback, usamos el nombre del directorio
            if (elements.outputFolder) {
                // La API no da la ruta completa por seguridad
                // Mostramos el nombre y guardamos el handle
                elements.outputFolder.value = dirHandle.name;
                elements.outputFolder.dataset.dirHandle = 'set';
                // Guardar el handle para uso posterior
                state.dirHandle = dirHandle;
                alert(`Carpeta seleccionada: ${dirHandle.name}\n\nNota: Por seguridad del navegador, debes escribir la ruta completa manualmente.\n\nEjemplo: C:\\Users\\Cynthia\\Videos\\${dirHandle.name}`);
            }
        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error('Error seleccionando carpeta:', err);
            }
        }
    } else {
        // Fallback para navegadores que no soportan la API
        alert('Tu navegador no soporta el selector de carpetas.\n\nEscribe la ruta manualmente, por ejemplo:\nC:\\Users\\Cynthia\\Videos\\Editados');
    }
});

// Process
elements.processBtn?.addEventListener('click', () => {
    if (state.mode === 'single') processSingle();
    else processBatch();
});

// Retry
elements.retryBtn?.addEventListener('click', () => {
    if (state.selectedFiles.length > 0) {
        if (state.mode === 'single') processSingle();
        else processBatch();
    } else {
        resetApp();
    }
});

// New video
elements.newVideoBtn?.addEventListener('click', () => {
    state.results.forEach(r => {
        if (r.job_id) fetch(`/api/cleanup/${r.job_id}`, { method: 'DELETE' }).catch(() => { });
    });
    resetApp();
});

// Resume
elements.resumeBtn?.addEventListener('click', resumeProcessing);
elements.dismissResumeBtn?.addEventListener('click', dismissResume);

// =============================================================================
// Inicialización
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    checkForResume();
    fetch('/api/health').then(r => r.json()).then(() => console.log('✅ Servidor OK'));
});

console.log('🎬 SilenceCutter v3 - Batch Processing');
