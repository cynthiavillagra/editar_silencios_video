# 02 - Análisis de Requisitos

## 1. Requisitos Funcionales (MoSCoW)

### 1.1 MUST HAVE (Debe tener)

| ID | Requisito | Descripción | Estado |
|----|-----------|-------------|--------|
| RF01 | Subida de video | El usuario debe poder subir un archivo de video arrastrando o seleccionando | ✅ Implementado |
| RF02 | Configurar umbral de silencio | Slider de 0.5s a 10s para definir duración máxima de silencio | ✅ Implementado |
| RF03 | Configurar sensibilidad | Slider de 1-10 con equivalencia en dB mostrada | ✅ Implementado |
| RF04 | Procesar video | Detectar y recortar silencios automáticamente | ✅ Implementado |
| RF05 | Mostrar progreso | Barra de progreso con porcentaje y mensaje de estado | ✅ Implementado |
| RF06 | Descargar resultado | Botón para descargar el video procesado | ✅ Implementado |
| RF07 | Sin límite de tamaño | Aceptar videos de cualquier tamaño | ✅ Implementado |

### 1.2 SHOULD HAVE (Debería tener)

| ID | Requisito | Descripción | Estado |
|----|-----------|-------------|--------|
| RF08 | División automática | Videos >30 min se dividen en partes | ✅ Implementado |
| RF09 | Múltiples opciones de descarga | Todo junto, por partes, o ZIP | ✅ Implementado |
| RF10 | Progreso en tiempo real (SSE) | Actualizaciones cada 300ms sin polling | ✅ Implementado |
| RF11 | Procesamiento por lotes | Procesar múltiples videos secuencialmente | ✅ Implementado |
| RF12 | Carpeta de salida personalizada | Elegir dónde guardar los archivos | ✅ Implementado |

### 1.3 COULD HAVE (Podría tener)

| ID | Requisito | Descripción | Estado |
|----|-----------|-------------|--------|
| RF13 | Resume de procesos | Continuar un batch interrumpido | ✅ Implementado |
| RF14 | Selección de archivos en batch | Checkboxes para incluir/excluir archivos | ✅ Implementado |
| RF15 | Scripts CLI auxiliares | Calcular duración total, unir videos | ✅ Implementado |
| RF16 | Selector de carpeta visual | Botón para navegar carpetas | ✅ Implementado |

### 1.4 WON'T HAVE (No tendrá - esta versión)

| ID | Requisito | Razón |
|----|-----------|-------|
| RF-X1 | Edición manual de timeline | Fuera del alcance |
| RF-X2 | Transcodificación de formatos | Complejidad innecesaria |
| RF-X3 | Procesamiento en la nube | Requiere infraestructura |
| RF-X4 | Múltiples usuarios | App de uso personal |

---

## 2. Requisitos No Funcionales

| ID | Categoría | Requisito | Métrica | Estado |
|----|-----------|-----------|---------|--------|
| RNF01 | Rendimiento | Procesar 1 hora de video | <5 minutos | ✅ |
| RNF02 | Usabilidad | Interfaz intuitiva | Sin manual requerido | ✅ |
| RNF03 | Compatibilidad | Formatos soportados | MP4, AVI, MOV, MKV, WebM, WMV | ✅ |
| RNF04 | Disponibilidad | Funciona sin internet | 100% offline | ✅ |
| RNF05 | Mantenibilidad | Código documentado | Comentarios en funciones clave | ✅ |
| RNF06 | Portabilidad | Multiplataforma | Windows, Linux, macOS | ✅ |

---

## 3. Historias de Usuario

### HU-01: Procesar Video Individual
```
COMO docente
QUIERO subir un video de mi clase grabada
PARA eliminar los silencios largos y reducir su duración
```

**Criterios de Aceptación:**
- [x] Puedo arrastrar un archivo de video al área de subida
- [x] Puedo hacer clic para seleccionar un archivo
- [x] Se valida que el formato sea soportado
- [x] Veo una vista previa con nombre y tamaño del archivo
- [x] Puedo eliminar el archivo seleccionado y elegir otro

---

### HU-02: Configurar Parámetros de Recorte
```
COMO usuario
QUIERO configurar la duración máxima de silencio y la sensibilidad
PARA ajustar el recorte a mis necesidades específicas
```

**Criterios de Aceptación:**
- [x] Slider de duración muestra el valor actual (ej: "3.0s")
- [x] Slider de sensibilidad muestra valor y equivalencia en dB (ej: "5 (-38 dB)")
- [x] Descripción explica qué significa cada extremo
- [x] Los valores por defecto son razonables (3s, sensibilidad 5)

---

### HU-03: Ver Progreso en Tiempo Real
```
COMO usuario
QUIERO ver el progreso del procesamiento en tiempo real
PARA saber cuánto falta y qué está haciendo la aplicación
```

**Criterios de Aceptación:**
- [x] Barra de progreso visual con porcentaje
- [x] Mensaje descriptivo de la etapa actual (subiendo, analizando, recortando, renderizando)
- [x] Si el video se divide en partes, muestra qué parte se está procesando
- [x] Al completar, muestra mensaje de éxito

---

### HU-04: Descargar Video Procesado
```
COMO usuario
QUIERO descargar el video procesado
PARA usarlo en mis clases o contenido
```

**Criterios de Aceptación:**
- [x] Botón de descarga claro y visible
- [x] Si hay múltiples partes, opciones: todo junto, ZIP, o partes individuales
- [x] El nombre del archivo incluye sufijo "_editado"
- [x] Se muestra estadística de tiempo ahorrado

---

### HU-05: Procesar Múltiples Videos
```
COMO docente con muchas clases grabadas
QUIERO procesar varios videos de una carpeta
PARA ahorrar tiempo procesándolos uno por uno
```

**Criterios de Aceptación:**
- [x] Puedo cambiar a modo "Múltiples Videos"
- [x] Puedo seleccionar archivos individuales o una carpeta completa
- [x] Veo lista de archivos con checkboxes para incluir/excluir
- [x] Los videos se procesan secuencialmente
- [x] Puedo ver el progreso global del batch

---

### HU-06: Guardar Directamente en Carpeta
```
COMO usuario
QUIERO que los videos se guarden directamente en una carpeta de mi elección
PARA no tener que descargarlos y moverlos manualmente
```

**Criterios de Aceptación:**
- [x] Campo de texto para ingresar ruta de carpeta
- [x] Botón para navegar y seleccionar carpeta
- [x] Si la carpeta no existe, se crea automáticamente
- [x] Al terminar, muestra la ruta donde se guardaron los archivos

---

### HU-07: Calcular Duración de Videos (CLI)
```
COMO usuario avanzado
QUIERO calcular la duración total de videos en una carpeta
PARA planificar mis tiempos de edición
```

**Criterios de Aceptación:**
- [x] Script ejecutable desde terminal
- [x] Acepta ruta como argumento o la pide interactivamente
- [x] Lista cada video con su duración
- [x] Muestra suma total en formato legible (HH:MM:SS)

---

### HU-08: Unir Videos (CLI)
```
COMO usuario
QUIERO unir varios videos de una carpeta en uno solo
PARA tener un archivo consolidado
```

**Criterios de Aceptación:**
- [x] Script ejecutable desde terminal
- [x] Muestra lista de videos en orden y pide confirmación
- [x] Permite especificar nombre de salida
- [x] Muestra progreso del proceso de unión

---

## 4. Casos de Uso

### CU-01: Procesar Video Individual

```
Nombre: Procesar Video Individual
Actor: Usuario
Precondición: FFmpeg instalado, servidor corriendo
Flujo Principal:
    1. Usuario accede a la aplicación en localhost:5000
    2. Sistema muestra interfaz de subida
    3. Usuario arrastra un video al área de subida
    4. Sistema valida formato y muestra preview
    5. Usuario ajusta configuración (opcional)
    6. Usuario hace clic en "Procesar"
    7. Sistema inicia procesamiento y muestra progreso via SSE
    8. Sistema completa y muestra opciones de descarga
    9. Usuario descarga el video procesado
Flujo Alternativo:
    4a. Formato no soportado → Sistema muestra error
    7a. Video muy largo → Sistema divide automáticamente
Postcondición: Video procesado disponible para descarga
```

### CU-02: Procesar Batch de Videos

```
Nombre: Procesar Batch de Videos
Actor: Usuario
Precondición: FFmpeg instalado, servidor corriendo
Flujo Principal:
    1. Usuario cambia a modo "Múltiples Videos"
    2. Usuario selecciona carpeta o archivos
    3. Sistema muestra lista con checkboxes
    4. Usuario marca/desmarca videos a procesar
    5. Usuario hace clic en "Procesar"
    6. Sistema procesa videos secuencialmente
    7. Sistema muestra progreso por archivo y global
    8. Al completar, muestra resumen de resultados
Flujo Alternativo:
    6a. Error en un video → Se marca como fallido, continúa con el siguiente
    6b. Usuario cierra navegador → Estado guardado para resume
Postcondición: Todos los videos marcados procesados o marcados como fallidos
```

---

## 5. Matriz de Trazabilidad

| Requisito | Historia de Usuario | Caso de Uso | Archivo(s) |
|-----------|---------------------|-------------|------------|
| RF01 | HU-01 | CU-01 | index.html, app.js |
| RF02 | HU-02 | CU-01 | index.html, app.js |
| RF03 | HU-02 | CU-01 | index.html, app.js |
| RF04 | HU-01 | CU-01 | app.py |
| RF05 | HU-03 | CU-01, CU-02 | app.py, app.js |
| RF06 | HU-04 | CU-01 | app.py, app.js |
| RF08 | HU-03 | CU-01 | app.py |
| RF09 | HU-04 | CU-01 | app.py, app.js |
| RF10 | HU-03 | CU-01, CU-02 | app.py, app.js |
| RF11 | HU-05 | CU-02 | app.py, app.js |
| RF12 | HU-06 | CU-01 | app.py, index.html, app.js |
| RF15 | HU-07, HU-08 | N/A | duracion_videos.py, unir_videos.py |

---

## Historial de Cambios

| Fecha | Cambio |
|-------|--------|
| 2025-12-26 | Documento inicial - Ingeniería inversa del código existente |
