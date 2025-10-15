# 📘 Guía de Uso

## Inicio Rápido

### Extracción Básica

```bash
notes-extractor extract mi_documento.pdf -o resultado.xlsx
```

Este comando:
- Lee `mi_documento.pdf`
- Detecta automáticamente las páginas de índice
- Extrae las entradas de notas
- Genera `resultado.xlsx` con los resultados

## CLI - Interfaz de Línea de Comandos

### Comando `extract`

Extrae el índice de notas de un PDF.

```bash
notes-extractor extract [OPCIONES] PDF_PATH
```

**Opciones principales:**

| Opción | Descripción | Default |
|--------|-------------|---------|
| `-o, --output` | Archivo de salida | `{nombre}_notas.xlsx` |
| `--backend` | Backend (pdfplumber/pymupdf/pypdf2) | `pdfplumber` |
| `--scan-first N` | Limitar a N primeras páginas | Sin límite |
| `--min-note-lines N` | Mínimo de líneas de nota | `3` |
| `--confidence-threshold F` | Umbral de confianza (0-1) | `0.6` |
| `--map-pages` | Activar mapeo de páginas | Activado |
| `--lang` | Idioma (es/en) | `es` |
| `--debug` | Modo debug | Desactivado |
| `--format` | Formato (excel/json) | `excel` |

**Ejemplos:**

```bash
# Extracción con backend específico
notes-extractor extract documento.pdf --backend pymupdf

# Solo escanear primeras 30 páginas
notes-extractor extract documento.pdf --scan-first 30

# Cambiar umbral de confianza
notes-extractor extract documento.pdf --confidence-threshold 0.8

# Desactivar mapeo de páginas
notes-extractor extract documento.pdf --no-map-pages

# Exportar a JSON
notes-extractor extract documento.pdf --format json -o resultado.json

# Modo debug
notes-extractor extract documento.pdf --debug
```

### Comando `validate`

Valida un PDF antes de procesarlo.

```bash
notes-extractor validate documento.pdf
```

Verifica:
- ✓ Archivo válido y accesible
- ✓ Backend disponible
- ✓ Número de páginas
- ✓ Texto extraíble

### Comando `batch`

Procesa múltiples PDFs en un directorio.

```bash
notes-extractor batch input_dir/ -o output_dir/
```

**Opciones:**

| Opción | Descripción | Default |
|--------|-------------|---------|
| `-o, --output-dir` | Directorio de salida | `{input}/output` |
| `--backend` | Backend a usar | `pdfplumber` |
| `--pattern` | Patrón de archivos | `*.pdf` |

**Ejemplo:**

```bash
# Procesar todos los PDFs en un directorio
notes-extractor batch ./pdfs/ -o ./resultados/

# Con patrón específico
notes-extractor batch ./docs/ --pattern "financiero_*.pdf"
```

## Uso como Librería Python

### Ejemplo Básico

```python
from pathlib import Path
from notes_extractor.pipeline.orchestrator import NotesExtractorPipeline
from notes_extractor.config import ExtractorConfig

# Configuración
config = ExtractorConfig(
    backend="pdfplumber",
    min_confidence=0.6
)

# Pipeline
pipeline = NotesExtractorPipeline(config)

# Procesar
result = pipeline.process("documento.pdf", "resultado.xlsx")

# Resultados
if result.success:
    print(f"Notas encontradas: {result.notes_count}")
    for note in result.notes:
        print(f"{note.nota_id}: {note.titulo}")
```

### Configuración Avanzada

```python
config = ExtractorConfig(
    # Backend
    backend="pdfplumber",
    
    # Límites
    scan_first_n=50,  # Solo primeras 50 páginas
    
    # Umbrales
    min_note_lines=5,
    min_score_threshold=8.0,
    min_confidence=0.7,
    
    # Mapeo
    enable_page_mapping=True,
    footer_crop_ratio=0.15,
    
    # Idioma
    language="es",
    
    # Logging
    log_level="DEBUG",
    log_file=Path("proceso.log")
)
```

### Acceder a Resultados Detallados

```python
result = pipeline.process("documento.pdf")

if result.success:
    # Información general
    print(f"PDF: {result.pdf_path.name}")
    print(f"Tiempo: {result.processing_time:.2f}s")
    
    # Notas extraídas
    for note in result.notes:
        print(f"Nota {note.nota_id}:")
        print(f"  Título: {note.titulo}")
        print(f"  Página impresa: {note.pagina_impresa}")
        print(f"  Página PDF: {note.pagina_pdf}")
        print(f"  Confianza: {note.confianza:.2%}")
    
    # Páginas de índice
    for page in result.index_pages:
        print(f"Página {page.page_number}:")
        print(f"  Score: {page.score:.2f}")
        print(f"  Notas: {page.note_count}")
        print(f"  Confianza: {page.confidence:.2%}")
```

### Usar Backends Específicos

```python
from notes_extractor.extractors import get_extractor

# Obtener extractor específico
extractor = get_extractor("pymupdf")

# Verificar disponibilidad
if extractor.is_available():
    pages_text = extractor.extract_text("documento.pdf", max_pages=10)
    print(f"Texto extraído de {len(pages_text)} páginas")
```

### Exportar a JSON

```python
from notes_extractor.exporters import JSONExporter

exporter = JSONExporter()
exporter.export(result, Path("resultado.json"))
```

## Casos de Uso Comunes

### 1. Análisis de Estados Financieros

```bash
# Extraer índice de notas
notes-extractor extract estados_financieros_2023.pdf

# Verificar resultados en Excel
# → Abrir estados_financieros_2023_notas.xlsx
```

### 2. Procesamiento por Lotes

```bash
# Procesar todos los PDFs de una carpeta
notes-extractor batch ./financieros_2023/ -o ./indices_extraidos/

# Ver resumen en consola
```

### 3. Integración en Pipeline de Datos

```python
import pandas as pd
from notes_extractor.pipeline.orchestrator import NotesExtractorPipeline

# Procesar múltiples PDFs
pdfs = ["empresa_a.pdf", "empresa_b.pdf", "empresa_c.pdf"]
all_notes = []

pipeline = NotesExtractorPipeline()

for pdf in pdfs:
    result = pipeline.process(pdf)
    if result.success:
        for note in result.notes:
            all_notes.append({
                "empresa": pdf.stem,
                "nota_id": note.nota_id,
                "titulo": note.titulo,
                "pagina": note.pagina_impresa
            })

# Crear DataFrame consolidado
df = pd.DataFrame(all_notes)
df.to_csv("notas_consolidadas.csv", index=False)
```

### 4. Validación Antes de Procesamiento

```python
from notes_extractor.utils.validators import validate_pdf_path
from notes_extractor.extractors import get_extractor

def can_process_pdf(pdf_path: str) -> bool:
    """Verifica si un PDF es procesable."""
    try:
        # Validar path
        path = validate_pdf_path(pdf_path)
        
        # Verificar backend
        extractor = get_extractor("pdfplumber")
        if not extractor.is_available():
            return False
        
        # Verificar páginas
        page_count = extractor.get_page_count(path)
        return page_count > 0
    
    except Exception:
        return False

# Usar
if can_process_pdf("documento.pdf"):
    # Procesar...
    pass
```

## Formatos de Salida

### Excel (.xlsx)

El archivo Excel contiene 3 hojas:

**1. notas_paginas:**
- `nota_id`: ID de la nota
- `titulo`: Título de la nota
- `pagina_impresa`: Página según índice
- `pagina_pdf`: Página real en PDF (si se mapea)
- `pagina_fuente`: Página del índice donde se encontró
- `confianza`: Score de confianza [0-1]

**2. index_pages:**
- `page_number`: Número de página
- `score`: Score de detección
- `note_count`: Cantidad de notas
- `unique_notes`: Notas únicas
- `has_header`: Si tiene encabezado
- `dot_leaders`: Líneas con puntos líderes
- `confidence`: Confianza [0-1]

**3. resumen:**
- Métricas generales de la extracción

### JSON (.json)

Estructura JSON:

```json
{
  "metadata": {
    "pdf_path": "documento.pdf",
    "notes_count": 25,
    "average_confidence": 0.89,
    "processing_time": 2.34
  },
  "notes": [
    {
      "nota_id": "1",
      "titulo": "Información general",
      "pagina_impresa": 15,
      "pagina_pdf": 17,
      "confianza": 0.95
    }
  ],
  "index_pages": [...]
}
```

## Troubleshooting

### "No se detectaron páginas de índice"

**Causas posibles:**
- El PDF no tiene índice de notas
- El índice tiene formato no estándar
- Umbrales muy estrictos

**Soluciones:**
```bash
# Reducir umbrales
notes-extractor extract documento.pdf --min-note-lines 2 --confidence-threshold 0.5

# Modo debug para ver detalles
notes-extractor extract documento.pdf --debug
```

### "Backend not available"

**Solución:**
```bash
# Instalar backend faltante
pip install pdfplumber  # o PyMuPDF o PyPDF2
```

### Notas duplicadas o incompletas

**Causa:** Formato de índice complejo

**Solución:** Ajustar configuración:
```python
config = ExtractorConfig(
    min_confidence=0.7,  # Más estricto
    enable_page_mapping=False  # Si el mapeo causa problemas
)
```

## Mejores Prácticas

1. **Validar antes de procesar**:
   ```bash
   notes-extractor validate documento.pdf
   ```

2. **Usar modo debug para diagnóstico**:
   ```bash
   notes-extractor extract documento.pdf --debug
   ```

3. **Procesar por lotes eficientemente**:
   ```bash
   notes-extractor batch ./pdfs/ -o ./output/
   ```

4. **Revisar confianza de resultados**:
   - Verde (>0.8): Alta confianza
   - Amarillo (0.6-0.8): Media confianza
   - Rojo (<0.6): Revisar manualmente

## Soporte

- 📖 Documentación: [docs/](docs/)
- 💡 Ejemplos: [examples/](examples/)
- 🐛 Issues: [GitHub Issues](https://github.com/usuario/Table-Detector/issues)
