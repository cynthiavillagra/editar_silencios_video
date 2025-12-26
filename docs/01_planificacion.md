# 01 - Planificación del Proyecto

## Información General

| Campo | Valor |
|-------|-------|
| **Nombre del Proyecto** | SilenceCutter |
| **Versión** | 3.0 |
| **Fecha de Inicio** | 2025-12-24 |
| **Fecha de Formalización** | 2025-12-26 |
| **Autor** | Cynthia Villagra |
| **Licencia** | MIT |

---

## 1. Objetivo del Proyecto

### 1.1 Objetivo General
Desarrollar una aplicación web local que permita a educadores y creadores de contenido **recortar automáticamente silencios prolongados** en videos de clases grabadas, reduciendo el tiempo de edición manual de horas a minutos.

### 1.2 Objetivos Específicos

1. **Detección Inteligente**: Implementar un algoritmo de detección de silencios basado en análisis RMS del audio, configurado por el usuario.

2. **Recorte No Destructivo**: Los silencios mayores al umbral se **acortan** (no se eliminan completamente), preservando pausas naturales.

3. **Procesamiento de Videos Largos**: Dividir automáticamente videos >30 minutos en partes manejables para evitar problemas de memoria.

4. **Procesamiento por Lotes**: Permitir procesar múltiples videos de una carpeta de forma secuencial.

5. **Retroalimentación en Tiempo Real**: Mostrar progreso detallado mediante Server-Sent Events (SSE).

6. **Flexibilidad de Salida**: Ofrecer múltiples opciones de descarga (unido, por partes, ZIP) o guardado directo en carpeta.

---

## 2. Alcance del Proyecto

### 2.1 Dentro del Alcance (In-Scope)

| ID | Funcionalidad | Prioridad |
|----|---------------|-----------|
| F01 | Subida de videos (drag & drop o selector) | Alta |
| F02 | Configuración de umbral de silencio (0.5s - 10s) | Alta |
| F03 | Configuración de sensibilidad (1-10, -25dB a -55dB) | Alta |
| F04 | Detección de silencios con NumPy/SciPy | Alta |
| F05 | Recorte de silencios (acortar, no eliminar) | Alta |
| F06 | División automática de videos largos | Alta |
| F07 | Progreso en tiempo real (SSE) | Alta |
| F08 | Descarga de videos procesados | Alta |
| F09 | Procesamiento por lotes (batch) | Media |
| F10 | Guardado directo en carpeta especificada | Media |
| F11 | Resume de procesos interrumpidos | Media |
| F12 | Scripts CLI auxiliares (duración, unir) | Baja |

### 2.2 Fuera del Alcance (Out-of-Scope)

| Funcionalidad | Razón de Exclusión |
|---------------|-------------------|
| Edición manual de video | Complejidad excesiva, existen herramientas especializadas |
| Transcodificación de formatos | Fuera del objetivo principal |
| Procesamiento en la nube | Requiere infraestructura adicional |
| Autenticación de usuarios | App de uso local/personal |
| Base de datos persistente | Innecesario para el caso de uso |

---

## 3. Análisis de Riesgos

### 3.1 Riesgos Técnicos

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R01 | **Memoria Volátil/Stateless**: Al reiniciar el servidor se pierden los jobs en progreso | Alta | Medio | Implementado guardado de estado en JSON + localStorage |
| R02 | **Videos muy largos agotan RAM** | Alta | Alto | Implementada división automática en chunks de 30 min |
| R03 | **FFmpeg no instalado** | Media | Alto | Verificación al inicio + mensaje de error claro |
| R04 | **Formatos no soportados** | Media | Bajo | Lista blanca de extensiones + mensaje descriptivo |
| R05 | **Timeout en procesamiento largo** | Media | Medio | Procesamiento asíncrono con threading |

### 3.2 Riesgos de Usabilidad

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R06 | Usuario no entiende dB/sensibilidad | Alta | Bajo | Descripción visual + tabla de referencia |
| R07 | No sabe dónde se guardaron archivos | Media | Medio | Mensaje claro post-proceso + opción de carpeta |
| R08 | Interfaz confusa para batch | Media | Bajo | Modo switch claro Single/Batch |

### 3.3 Riesgos de Seguridad

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R09 | Inyección de rutas maliciosas | Baja | Alto | `secure_filename()` de Werkzeug |
| R10 | Acceso no autorizado a archivos | Baja | Medio | App diseñada para uso local únicamente |

---

## 4. Stakeholders

| Rol | Interés | Nivel de Influencia |
|-----|---------|---------------------|
| **Docente/Educador** | Usuario principal, necesita ahorrar tiempo de edición | Alto |
| **Creador de Contenido** | Usuario secundario, podcasts y tutoriales | Medio |
| **Desarrollador** | Mantenimiento y mejoras futuras | Alto |

---

## 5. Restricciones Técnicas

| Restricción | Justificación |
|-------------|---------------|
| Python 3.13+ | Compatibilidad con dependencias modernas |
| FFmpeg requerido | Backend de MoviePy para procesamiento de video |
| Navegador moderno | SSE, File System Access API |
| Uso local | Sin infraestructura de servidor público |

---

## 6. Criterios de Éxito

| Criterio | Métrica | Estado |
|----------|---------|--------|
| Video de 1 hora procesado sin errores | Completo en <5 min | ✅ |
| Reducción de tiempo en videos de clase | >20% de duración eliminada | ✅ |
| Silencios recortados, no eliminados | Pausas naturales preservadas | ✅ |
| Progreso visible en tiempo real | SSE actualiza cada 300ms | ✅ |
| Batch de 10 videos procesados | Cola secuencial funcional | ✅ |

---

## Historial de Cambios

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2025-12-24 | 1.0 | Prototipo inicial |
| 2025-12-25 | 2.0 | División de videos largos, opciones de descarga |
| 2025-12-25 | 3.0 | Batch processing, SSE, resume, carpeta de salida |
| 2025-12-26 | 3.0 | Formalización de documentación |
