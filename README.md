# ✂️ SilenceCutter v3

**Recorta automáticamente silencios largos en videos** - Perfecto para editar clases grabadas, presentaciones y podcasts.

![Python](https://img.shields.io/badge/Python-3.13+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![License](https://img.shields.io/badge/License-CC%20BY%204.0-yellow)

---

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
- **Carpeta personalizada**: Guarda directamente donde quieras

---

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

---

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

---

## 🛠️ Scripts CLI Auxiliares

### Calcular duración total de videos
```bash
python duracion_videos.py "C:\ruta\a\videos"
```

### Unir múltiples videos
```bash
python unir_videos.py "C:\ruta\a\videos"
```

---

## 📂 Estructura del Proyecto

```
app silencios/
├── app.py                 # Backend Flask
├── requirements.txt       # Dependencias Python
├── duracion_videos.py     # Script: calcular duración
├── unir_videos.py         # Script: unir videos
├── templates/
│   └── index.html         # Página principal
├── static/
│   ├── css/styles.css     # Estilos (tema oscuro)
│   └── js/app.js          # Lógica del frontend
└── docs/                  # Documentación técnica
    ├── 01_planificacion.md
    ├── 02_analisis.md
    ├── 03_a_diseno_arquitectura_patrones.md
    ├── 03_b_modelado_datos.md
    ├── 03_c_api_dinamica.md
    ├── 04_manual_app_py.md
    ├── 05_manual_app_js.md
    ├── 06_manual_scripts_cli.md
    └── CHECKPOINT.md
```

---

## 🔧 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Página principal |
| GET | `/api/health` | Estado del servidor |
| POST | `/api/process/async` | Procesar video (async con SSE) |
| GET | `/api/progress/<job_id>` | Stream SSE de progreso |
| GET | `/api/job/<job_id>` | Estado de un trabajo |
| POST | `/api/batch/start` | Iniciar batch |
| GET | `/api/download/<job_id>/merged` | Descargar video completo |
| GET | `/api/download/<job_id>/all` | Descargar ZIP |

---

## 📋 Formatos Soportados

- MP4, AVI, MOV, MKV, WebM, WMV

---

## 🤖 AI Stack

Este proyecto fue desarrollado con asistencia de inteligencia artificial:

| Herramienta | Versión | Uso |
|-------------|---------|-----|
| **Google Antigravity** | Claude 4 | Asistente de desarrollo, arquitectura, documentación |

### ⚠️ Aviso Importante

Este proyecto fue creado con fines **educativos y de prototipado rápido**. 

- ✅ Apto para: uso local, proyectos pedagógicos, MVPs
- ❌ No apto para: producción sin revisión, sistemas críticos

El código generado por IA ha sido revisado pero puede contener:
- Vulnerabilidades de seguridad no detectadas
- Casos edge no contemplados
- Optimizaciones pendientes

**Úselo bajo su propia responsabilidad.**

---

## 📝 Documentación Técnica

La documentación completa siguiendo la **Guía V10** está disponible en la carpeta `docs/`:

1. **Planificación**: Objetivos, alcance, análisis de riesgos
2. **Análisis**: Requisitos MoSCoW, historias de usuario, casos de uso
3. **Arquitectura**: Patrones de diseño, decisiones técnicas
4. **Modelado**: Diagramas ER y de clases (Mermaid)
5. **API**: Endpoints, diagramas de secuencia
6. **Manuales**: Guías técnicas por archivo

---

## 📄 Licencia

Este proyecto está licenciado bajo **Creative Commons Attribution 4.0 International (CC BY 4.0)**.

Puedes:
- ✅ Compartir — copiar y redistribuir el material
- ✅ Adaptar — remezclar, transformar y construir sobre el material
- ✅ Para cualquier propósito, incluso comercial

Con la condición de:
- 📌 **Atribución** — Debes dar crédito apropiado

Ver [LICENSE](LICENSE) para más detalles.

---

## 🙏 Agradecimientos

Desarrollado con ❤️ para educadores que quieren ahorrar tiempo editando videos.

**Autor**: Cynthia Villagra  
**Asistencia IA**: Google Antigravity (Claude)  
**Año**: 2025
