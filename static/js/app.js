/**
 * SilenceCutter - JavaScript Principal
 * ====================================
 * Maneja la interacción del usuario con la aplicación de recorte de silencios
 */

// =============================================================================
// Estado de la Aplicación
// =============================================================================
const state = {
    selectedFile: null,
    downloadId: null,
    downloadFilename: null,
    isProcessing: false
};

// =============================================================================
// Elementos del DOM
// =============================================================================
const elements = {
    // Upload
    uploadArea: document.getElementById('uploadArea'),
    uploadSection: document.getElementById('uploadSection'),
    videoInput: document.getElementById('videoInput'),
    filePreview: document.getElementById('filePreview'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    removeFile: document.getElementById('removeFile'),

    // Settings
    maxSilence: document.getElementById('maxSilence'),
    maxSilenceValue: document.getElementById('maxSilenceValue'),
    sensitivity: document.getElementById('sensitivity'),
    sensitivityValue: document.getElementById('sensitivityValue'),

    // Buttons
    processBtn: document.getElementById('processBtn'),
    downloadBtn: document.getElementById('downloadBtn'),
    newVideoBtn: document.getElementById('newVideoBtn'),
    retryBtn: document.getElementById('retryBtn'),

    // Sections
    settingsSection: document.getElementById('settingsSection'),
    progressSection: document.getElementById('progressSection'),
    progressTitle: document.getElementById('progressTitle'),
    progressMessage: document.getElementById('progressMessage'),
    resultsSection: document.getElementById('resultsSection'),
    errorSection: document.getElementById('errorSection'),
    errorMessage: document.getElementById('errorMessage'),

    // Stats
    originalDuration: document.getElementById('originalDuration'),
    newDuration: document.getElementById('newDuration'),
    timeSaved: document.getElementById('timeSaved'),
    percentageSaved: document.getElementById('percentageSaved')
};

// =============================================================================
// Utilidades
// =============================================================================

/**
 * Formatea bytes a una cadena legible
 */
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Formatea segundos a formato mm:ss o hh:mm:ss
 */
function formatDuration(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hrs > 0) {
        return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Muestra una sección y oculta las demás
 */
function showSection(section) {
    const sections = ['progressSection', 'resultsSection', 'errorSection'];
    sections.forEach(s => {
        elements[s].classList.add('hidden');
    });
    if (section) {
        elements[section].classList.remove('hidden');
    }
}

/**
 * Resetea la aplicación al estado inicial
 */
function resetApp() {
    state.selectedFile = null;
    state.downloadId = null;
    state.downloadFilename = null;
    state.isProcessing = false;

    elements.uploadArea.classList.remove('hidden');
    elements.filePreview.classList.add('hidden');
    elements.processBtn.disabled = true;
    showSection(null);
}

// =============================================================================
// Manejo de Archivos
// =============================================================================

/**
 * Maneja la selección de un archivo
 */
function handleFileSelect(file) {
    if (!file) return;

    // Verificar tipo de archivo
    const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/webm', 'video/x-ms-wmv'];
    const validExtensions = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'wmv'];
    const extension = file.name.split('.').pop().toLowerCase();

    if (!validTypes.includes(file.type) && !validExtensions.includes(extension)) {
        showError('Formato de archivo no válido. Por favor usa: MP4, AVI, MOV, MKV, WebM');
        return;
    }

    // Verificar tamaño (500MB máximo)
    if (file.size > 500 * 1024 * 1024) {
        showError('El archivo es demasiado grande. Máximo permitido: 500MB');
        return;
    }

    state.selectedFile = file;

    // Actualizar UI
    elements.uploadArea.classList.add('hidden');
    elements.filePreview.classList.remove('hidden');
    elements.fileName.textContent = file.name;
    elements.fileSize.textContent = formatBytes(file.size);
    elements.processBtn.disabled = false;
    showSection(null);
}

/**
 * Muestra un mensaje de error
 */
function showError(message) {
    elements.errorMessage.textContent = message;
    showSection('errorSection');
}

// =============================================================================
// Drag & Drop
// =============================================================================

elements.uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.uploadArea.classList.add('drag-over');
});

elements.uploadArea.addEventListener('dragleave', (e) => {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
});

elements.uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

elements.uploadArea.addEventListener('click', () => {
    elements.videoInput.click();
});

elements.videoInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

// =============================================================================
// Controles de Configuración
// =============================================================================

elements.maxSilence.addEventListener('input', (e) => {
    elements.maxSilenceValue.textContent = `${e.target.value}s`;
});

elements.sensitivity.addEventListener('input', (e) => {
    elements.sensitivityValue.textContent = e.target.value;
});

// =============================================================================
// Botones de Acción
// =============================================================================

elements.removeFile.addEventListener('click', (e) => {
    e.stopPropagation();
    resetApp();
});

elements.processBtn.addEventListener('click', processVideo);

elements.downloadBtn.addEventListener('click', downloadVideo);

elements.newVideoBtn.addEventListener('click', () => {
    // Limpiar archivo anterior del servidor
    if (state.downloadId && state.downloadFilename) {
        fetch(`/api/cleanup/${state.downloadId}/${state.downloadFilename}`, { method: 'DELETE' })
            .catch(() => { }); // Ignorar errores de limpieza
    }
    resetApp();
});

elements.retryBtn.addEventListener('click', () => {
    if (state.selectedFile) {
        processVideo();
    } else {
        resetApp();
    }
});

// =============================================================================
// Procesamiento de Video
// =============================================================================

async function processVideo() {
    if (!state.selectedFile || state.isProcessing) return;

    state.isProcessing = true;
    showSection('progressSection');
    elements.processBtn.disabled = true;

    const formData = new FormData();
    formData.append('video', state.selectedFile);
    formData.append('max_silence', elements.maxSilence.value);
    formData.append('sensitivity', elements.sensitivity.value);

    try {
        elements.progressTitle.textContent = 'Subiendo video...';
        elements.progressMessage.textContent = 'Preparando el archivo para procesar';

        const response = await fetch('/api/process', {
            method: 'POST',
            body: formData
        });

        elements.progressTitle.textContent = 'Procesando video...';
        elements.progressMessage.textContent = 'Detectando y recortando silencios, esto puede tomar unos minutos';

        const result = await response.json();

        if (response.ok && result.success) {
            // Éxito
            state.downloadId = result.download_id;
            state.downloadFilename = result.filename;

            // Actualizar estadísticas
            elements.originalDuration.textContent = formatDuration(result.stats.original_duration);
            elements.newDuration.textContent = formatDuration(result.stats.new_duration);
            elements.timeSaved.textContent = formatDuration(result.stats.time_saved);
            elements.percentageSaved.textContent = `${result.stats.percentage_saved}%`;

            showSection('resultsSection');
        } else {
            showError(result.error || 'Error desconocido al procesar el video');
        }
    } catch (error) {
        console.error('Error:', error);
        showError(`Error de conexión: ${error.message}`);
    } finally {
        state.isProcessing = false;
        elements.processBtn.disabled = false;
    }
}

// =============================================================================
// Descarga de Video
// =============================================================================

function downloadVideo() {
    if (!state.downloadId || !state.downloadFilename) return;

    const downloadUrl = `/api/download/${state.downloadId}/${state.downloadFilename}`;

    // Crear enlace temporal para descargar
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = state.downloadFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// =============================================================================
// Inicialización
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Verificar que el servidor esté funcionando
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            console.log('✅ Servidor conectado:', data.message);
        })
        .catch(error => {
            console.warn('⚠️ No se pudo conectar con el servidor:', error);
        });
});

console.log('🎬 SilenceCutter cargado correctamente');
