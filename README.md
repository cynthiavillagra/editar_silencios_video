# ✂️ SilenceCutter - Recorte Automático de Silencios en Videos

Aplicación web local para recortar automáticamente pausas y silencios largos de tus videos. Perfecta para editar grabaciones de clases, presentaciones y tutoriales.

## 🚀 Características

- **Detección automática de silencios** usando análisis de audio
- **Configurable**: ajusta la duración máxima de silencio (0.5s - 10s)
- **Sensibilidad ajustable**: controla qué tan "silencioso" debe ser el audio para considerarse pausa
- **Procesamiento 100% local**: tus videos nunca salen de tu computadora
- **Interfaz moderna y fácil de usar**
- **Soporta múltiples formatos**: MP4, AVI, MOV, MKV, WebM

## 📋 Requisitos Previos

1. **Python 3.8+** instalado
2. **FFmpeg** instalado en el sistema

### Instalar FFmpeg en Windows

Opción 1 - Usando Chocolatey:
```bash
choco install ffmpeg
```

Opción 2 - Descarga manual:
1. Descarga desde [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extrae y añade la carpeta `bin` al PATH del sistema

## 🔧 Instalación

1. **Crear entorno virtual** (recomendado):
```bash
python -m venv venv
venv\Scripts\activate  # En Windows
# o
source venv/bin/activate  # En Linux/Mac
```

2. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

## ▶️ Uso

1. **Iniciar la aplicación**:
```bash
python app.py
```

2. **Abrir en el navegador**:
   - Ve a `http://localhost:5000`

3. **Procesar un video**:
   - Arrastra o selecciona tu video
   - Ajusta la duración máxima de silencio (por defecto: 3 segundos)
   - Ajusta la sensibilidad de detección
   - Haz clic en "Procesar Video"
   - Descarga el resultado

## ⚙️ Configuración

### Duración Máxima de Silencio
- **Rango**: 0.5 - 10 segundos
- **Recomendado**: 2-3 segundos para clases grabadas
- Los silencios mayores a este valor serán recortados

### Sensibilidad
- **Rango**: 1 - 10
- **1**: Menos sensible, solo detecta silencios muy claros
- **10**: Muy sensible, detecta incluso susurros como silencio
- **Recomendado**: 5-6 para la mayoría de grabaciones

## 📁 Estructura del Proyecto

```
app silencios/
├── app.py              # Backend Flask
├── requirements.txt    # Dependencias Python
├── README.md           # Esta documentación
├── templates/
│   └── index.html      # Página principal
└── static/
    ├── css/
    │   └── styles.css  # Estilos
    └── js/
        └── app.js      # JavaScript frontend
```

## 🔧 Solución de Problemas

### Error: "FFmpeg not found"
Asegúrate de que FFmpeg esté instalado y en el PATH del sistema.

### El video no se procesa
- Verifica que el formato sea compatible
- Asegúrate de que el video tenga audio
- Revisa que el archivo no esté corrupto

### El procesamiento es muy lento
- Los videos largos pueden tomar varios minutos
- Considera reducir la resolución del video original

## 📝 Licencia

Este proyecto es de uso libre para fines educativos.

---

Desarrollado con ❤️ para hacer la edición de videos más fácil
