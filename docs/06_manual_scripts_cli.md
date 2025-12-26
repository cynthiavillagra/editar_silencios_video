# 06 - Manual Técnico: Scripts CLI

## 1. Información General

| Script | Propósito | Líneas |
|--------|-----------|--------|
| `duracion_videos.py` | Calcular duración total de videos en carpeta | ~130 |
| `unir_videos.py` | Concatenar múltiples videos en uno | ~190 |

---

## 2. Trazabilidad

| Elemento | Referencia |
|----------|------------|
| **Requisitos** | RF15 (Could Have) |
| **Historias de Usuario** | HU-07, HU-08 |
| **Arquitectura** | Scripts independientes (no parte de la app web) |

---

## SCRIPT 1: duracion_videos.py

### 3.1 Propósito

Calcular la duración total de todos los videos en una carpeta, mostrando:
- Lista de videos con duración individual
- Suma total en formato HH:MM:SS
- Duración promedio

### 3.2 Uso

```bash
# Interactivo (pide ruta)
python duracion_videos.py

# Con argumento
python duracion_videos.py "C:\Videos\MisClases"
```

### 3.3 Estructura

```python
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.wmv', '.flv', '.m4v'}

def format_duration(seconds):
    """Formatea segundos a HH:MM:SS"""
    
def get_video_duration(filepath):
    """Obtiene duración usando MoviePy"""
    
def find_videos(folder_path):
    """Encuentra archivos de video en carpeta"""
    
def main():
    """Flujo principal interactivo"""
```

### 3.4 Análisis Dual

**Por qué SÍ MoviePy para duración:**
- ✅ Ya es dependencia del proyecto
- ✅ Maneja todos los formatos soportados
- ✅ API simple: `VideoFileClip(path).duration`

**Por qué NO FFprobe:**
- ❌ Requiere parsear output JSON/XML
- ❌ Dependencia adicional de sistema

### 3.5 Flujo de Ejecución

```
1. Obtener ruta (argumento o input)
2. Validar que existe y es directorio
3. Buscar archivos con extensiones válidas
4. Ordenar alfabéticamente
5. Para cada video:
   a. Cargar con MoviePy
   b. Obtener duración
   c. Mostrar progreso
6. Calcular totales
7. Mostrar resumen
```

### 3.6 Output Ejemplo

```
============================================================
🎬 Calculador de Duración de Videos
============================================================

🔍 Buscando videos en: C:\Videos\MisClases
✅ Encontrados 5 videos

📊 Analizando duración de cada video...
------------------------------------------------------------
   [1/5] clase_01.mp4... ✅ 45:32
   [2/5] clase_02.mp4... ✅ 52:18
   [3/5] clase_03.mp4... ✅ 38:45
   [4/5] clase_04.mp4... ✅ 1:01:02
   [5/5] clase_05.mp4... ✅ 47:23
------------------------------------------------------------

📋 RESUMEN
============================================================

🎯 TOTAL: 5 videos
⏱️  Duración total: 4:05:00
   (245.0 minutos / 4.08 horas)
📊 Duración promedio: 49:00
```

### 3.7 Troubleshooting

| Error | Causa | Solución |
|-------|-------|----------|
| `moviepy no instalado` | Python global sin moviepy | Usar `.\venv\Scripts\python.exe` |
| `No se encontraron videos` | Extensión no soportada | Verificar formato de archivos |
| `Error leyendo X` | Archivo corrupto | Verificar integridad del video |

---

## SCRIPT 2: unir_videos.py

### 4.1 Propósito

Concatenar todos los videos de una carpeta en un único archivo MP4.

### 4.2 Uso

```bash
# Interactivo
python unir_videos.py

# Con carpeta
python unir_videos.py "C:\Videos\MisClases"

# Con carpeta y nombre de salida
python unir_videos.py "C:\Videos\MisClases" "curso_completo.mp4"
```

### 4.3 Estructura

```python
VIDEO_EXTENSIONS = {...}

def format_duration(seconds):
    """Formatea segundos a HH:MM:SS"""
    
def find_videos(folder_path):
    """Encuentra videos ordenados alfabéticamente"""
    
def main():
    """Flujo principal con confirmaciones"""
```

### 4.4 Análisis Dual

**Por qué SÍ MoviePy concatenate:**
- ✅ Maneja diferentes resoluciones (method="compose")
- ✅ Transiciones suaves
- ✅ Un solo codec de salida

**Por qué NO FFmpeg concat demuxer:**
- ❌ Requiere archivos con mismo codec
- ❌ Más complejo de configurar

**Riesgos:**
- ⚠️ Videos con resoluciones muy diferentes pueden verse mal
- ⚠️ Proceso lento para muchos videos largos

### 4.5 Flujo de Ejecución

```
1. Obtener ruta de carpeta
2. Buscar y ordenar videos
3. Mostrar lista y pedir confirmación de orden
4. Pedir nombre de archivo de salida
5. Verificar si ya existe (sobrescribir?)
6. Cargar todos los clips en memoria
7. Concatenar con method="compose"
8. Renderizar a MP4
9. Mostrar estadísticas finales
```

### 4.6 Output Ejemplo

```
============================================================
🎬 Unir Videos
============================================================

🔍 Buscando videos en: C:\Videos\Partes
✅ Encontrados 3 videos

📹 Videos a unir (en este orden):
------------------------------------------------------------
   1. parte1_intro.mp4
   2. parte2_contenido.mp4
   3. parte3_cierre.mp4
------------------------------------------------------------

¿El orden es correcto? (s/n)
   > s

📝 Nombre del archivo de salida [Partes_completo.mp4]:
   > curso_final.mp4

🎬 Cargando videos...
   [1/3] Cargando parte1_intro.mp4... ✅ 10:00
   [2/3] Cargando parte2_contenido.mp4... ✅ 45:00
   [3/3] Cargando parte3_cierre.mp4... ✅ 5:00
------------------------------------------------------------
⏱️  Duración total: 1:00:00

🔗 Uniendo videos...
💾 Guardando en: C:\Videos\Partes\curso_final.mp4
   (esto puede tomar varios minutos...)

============================================================
✅ ¡Videos unidos exitosamente!
📁 Archivo: C:\Videos\Partes\curso_final.mp4
⏱️  Duración: 1:00:00
💾 Tamaño: 450.5 MB
============================================================
```

### 4.7 Troubleshooting

| Error | Causa | Solución |
|-------|-------|----------|
| `Solo hay 1 video` | No hay nada que unir | Agregar más videos |
| `Error cargando video` | Formato incompatible | Verificar codecs |
| `Memory Error` | Muchos videos grandes | Procesar en grupos |
| `El archivo ya existe` | Nombre duplicado | Elegir otro nombre o sobrescribir |

### 4.8 Recomendación de Nombres

Para que el orden alfabético sea correcto:

```
✅ Correcto:
01_intro.mp4
02_tema1.mp4
03_tema2.mp4
04_cierre.mp4

❌ Incorrecto (orden inesperado):
intro.mp4
tema1.mp4
tema10.mp4   ← Aparece antes de tema2
tema2.mp4
```

---

## 5. Prueba de Fuego

### 5.1 duracion_videos.py

```python
if __name__ == "__main__":
    main()
```

**Flujo de main():**
1. Parsear argumentos o pedir input
2. Validar carpeta
3. Buscar videos
4. Calcular duraciones
5. Mostrar resumen
6. Esperar Enter para cerrar

### 5.2 unir_videos.py

```python
if __name__ == "__main__":
    main()
```

**Flujo de main():**
1. Obtener carpeta y nombre de salida
2. Confirmar orden de videos
3. Verificar sobrescritura
4. Cargar, concatenar, renderizar
5. Mostrar resultado

### 5.3 Testing Manual

```bash
# Preparar carpeta de prueba
mkdir test_videos
# Copiar algunos videos cortos

# Probar duración
.\venv\Scripts\python.exe duracion_videos.py test_videos

# Probar unión
.\venv\Scripts\python.exe unir_videos.py test_videos
```

---

## 6. Diferencias con la App Web

| Aspecto | App Web | Scripts CLI |
|---------|---------|-------------|
| Interfaz | Browser GUI | Terminal |
| Entrada | Drag & drop | Ruta como texto |
| Progreso | Barra visual + SSE | Print en consola |
| Configuración | Sliders | Ninguna (valores fijos) |
| Output | Descarga/Carpeta | Solo disco |

---

## 7. Extensiones Futuras

| Mejora | Dificultad | Beneficio |
|--------|------------|-----------|
| Agregar barra de progreso (tqdm) | Baja | UX mejorada |
| Permitir filtrar por fecha | Media | Más control |
| Exportar lista a CSV | Baja | Documentación |
| GUI simple (tkinter) | Media | Alternativa a CLI |

---

## Historial de Cambios

| Fecha | Cambio |
|-------|--------|
| 2025-12-26 | Documento inicial - Ingeniería inversa |
