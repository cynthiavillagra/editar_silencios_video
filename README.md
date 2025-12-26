# ✂️ SilenceCutter v3

**Recorta automáticamente silencios largos en videos** - Perfecto para editar clases grabadas, presentaciones y podcasts.

![Python](https://img.shields.io/badge/Python-3.13+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Características

### 🎬 Procesamiento Inteligente
- **Recorte de silencios**: Los silencios mayores al umbral se **acortan** (no se borran completamente)
- **División automática**: Videos >30 min se dividen en partes para mejor manejo de memoria
- **Preserva pausas naturales**: Mantiene transiciones suaves entre segmentos

### 📁 Procesamiento por Lotes
- Procesa **múltiples videos** de una carpeta
- Selecciona archivos individuales o carpetas completas
- **Checkboxes** para elegir qué videos procesar
- Cola de procesamiento uno a uno

### 💾 Guardado de Estado
- **Resume automático**: Si el proceso se interrumpe, puedes continuar donde quedaste
- Estado guardado en localStorage (navegador) y JSON (servidor)

### 📊 Progreso en Tiempo Real
- Barra de progreso con porcentaje
- Muestra en qué **parte** del video está (ej: "Parte 2/4")
- Etapas visibles: Subir → Audio → Analizar → Cortar → Renderizar

### 📥 Opciones de Descarga Flexibles
- **Todo junto**: Un solo archivo MP4
- **Por partes**: Archivos separados (Parte1.mp4, Parte2.mp4...)
- **ZIP**: Todas las partes comprimidas

## 🚀 Instalación

### Requisitos
- Python 3.13+
- FFmpeg (debe estar en el PATH del sistema)

### Pasos

```bash
# Clonar repositorio
git clone https://github.com/cynthiavillagra/editar_silencios_video.git
cd editar_silencios_video

# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Activar entorno (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python app.py
```

Abrir en el navegador: **http://localhost:5000**

## ⚙️ Configuración

### Duración Máxima de Silencio
- **Rango**: 0.5s - 10s
- **Por defecto**: 3s
- Los silencios mayores a este valor se **recortan** a esta duración

### Sensibilidad de Detección
| Valor | Decibeles | Uso Recomendado |
|:-----:|:---------:|-----------------|
| 1 | -25 dB | Grabaciones con mucho ruido de fondo |
| 3 | -32 dB | Aulas ruidosas |
| **5** | **-38 dB** | **Balance general (por defecto)** |
| 7 | -45 dB | Grabaciones limpias |
| 10 | -55 dB | Audio de estudio |

- **Bajo (1-3)**: Solo detecta silencios muy obvios
- **Alto (7-10)**: Detecta como silencio cualquier ruido muy bajo

## 📂 Estructura del Proyecto

```
app silencios/
├── app.py                 # Backend Flask
├── requirements.txt       # Dependencias Python
├── templates/
│   └── index.html         # Página principal
└── static/
    ├── css/
    │   └── styles.css     # Estilos (tema oscuro)
    └── js/
        └── app.js         # Lógica del frontend
```

## 🔧 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Página principal |
| GET | `/api/health` | Estado del servidor |
| POST | `/api/process` | Procesar video (sincrónico) |
| POST | `/api/process/async` | Procesar video (asíncrono con SSE) |
| GET | `/api/progress/<job_id>` | Stream SSE de progreso |
| GET | `/api/job/<job_id>` | Estado de un trabajo |
| POST | `/api/batch/start` | Iniciar batch |
| POST | `/api/batch/<id>/process/<index>` | Procesar archivo de batch |
| GET | `/api/download/<job_id>/merged` | Descargar video completo |
| GET | `/api/download/<job_id>/part/<n>` | Descargar parte específica |
| GET | `/api/download/<job_id>/all` | Descargar ZIP con todas las partes |
| DELETE | `/api/cleanup/<job_id>` | Limpiar archivos temporales |

## 📋 Formatos Soportados

- MP4
- AVI
- MOV
- MKV
- WebM
- WMV

## 🎯 Casos de Uso

1. **Clases grabadas**: Recortar pausas largas del profesor pensando
2. **Presentaciones**: Eliminar silencios entre diapositivas
3. **Podcasts**: Acortar pausas incómodas
4. **Tutoriales**: Hacer videos más dinámicos

## 📝 Notas Técnicas

- Los videos >30 minutos se dividen automáticamente en partes de ~30 min
- El procesamiento usa MoviePy (basado en FFmpeg)
- La detección de silencios usa NumPy y SciPy (análisis RMS)
- Compatible con Python 3.14 (no usa audioop/pydub)

## 🐛 Solución de Problemas

### "FFmpeg no encontrado"
Instalar FFmpeg y agregarlo al PATH del sistema.

### "Error al procesar video"
- Verificar que el formato sea soportado
- Probar con un video más corto para diagnóstico

### El progreso no se actualiza
- Refrescar la página
- Verificar que el servidor esté corriendo

## 📄 Licencia

MIT License - Uso libre para proyectos educativos y personales.

---

Desarrollado con ❤️ para educadores que quieren ahorrar tiempo editando videos.
