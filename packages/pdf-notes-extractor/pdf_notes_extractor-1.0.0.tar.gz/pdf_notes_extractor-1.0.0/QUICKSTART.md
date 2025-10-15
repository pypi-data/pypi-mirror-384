# ⚡ Quick Start - PDF Notes Extractor

## 🚀 Instalación Rápida (5 minutos)

```bash
# 1. Navega al directorio del proyecto
cd Table-Detector

# 2. Crea un entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instala el paquete
pip install -e .

# 4. Verifica la instalación
notes-extractor --version
```

## 💡 Primer Uso

### Opción 1: CLI (Más Fácil)

```bash
# Extrae el índice de notas de un PDF
notes-extractor extract mi_documento.pdf -o resultado.xlsx

# Verifica el archivo Excel generado
open resultado.xlsx  # macOS
# xdg-open resultado.xlsx  # Linux
# start resultado.xlsx  # Windows
```

### Opción 2: Python Script

Crea un archivo `test.py`:

```python
from notes_extractor import NotesExtractorPipeline

# Procesar PDF
pipeline = NotesExtractorPipeline()
result = pipeline.process("mi_documento.pdf", "resultado.xlsx")

# Ver resultados
if result.success:
    print(f"✅ Éxito! {result.notes_count} notas encontradas")
    for note in result.notes[:5]:
        print(f"  {note.nota_id}: {note.titulo}")
else:
    print(f"❌ Error: {result.error_message}")
```

Ejecuta:
```bash
python test.py
```

## 📊 Resultado Esperado

El Excel generado contendrá:

**Hoja 1: notas_paginas**
```
nota_id | titulo                    | pagina_impresa | pagina_pdf | confianza
--------|---------------------------|----------------|------------|----------
1       | Información general       | 15             | 17         | 0.95
2       | Políticas contables       | 18             | 20         | 0.92
...
```

## 🎯 Comandos Útiles

```bash
# Validar PDF antes de procesar
notes-extractor validate documento.pdf

# Procesar con opciones específicas
notes-extractor extract documento.pdf \
  --backend pymupdf \
  --confidence-threshold 0.8 \
  --debug

# Procesar múltiples PDFs
notes-extractor batch ./pdfs/ -o ./output/

# Ver ayuda
notes-extractor --help
notes-extractor extract --help
```

## 🔧 Configuración Personalizada

Crea un archivo `.env`:

```bash
cp .env.example .env
```

Edita `.env`:
```
EXTRACTOR_BACKEND=pdfplumber
MIN_NOTE_LINES=3
LANGUAGE=es
LOG_LEVEL=INFO
```

## 🧪 Ejecutar Tests

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Ejecutar tests
pytest tests/

# Con cobertura
pytest --cov=src/notes_extractor tests/
```

## 📚 Próximos Pasos

1. **Leer documentación completa**: `README.md`
2. **Ver guía de uso detallada**: `USAGE.md`
3. **Explorar ejemplos**: `examples/`
4. **Revisar arquitectura**: `Estructura.md`

## ❓ Problemas Comunes

### "No se detectaron páginas de índice"

**Solución**: Reduce umbrales
```bash
notes-extractor extract documento.pdf \
  --min-note-lines 2 \
  --confidence-threshold 0.5
```

### "Backend not available"

**Solución**: Instala backend faltante
```bash
pip install pdfplumber  # o PyMuPDF o PyPDF2
```

### Error de permisos

**Solución**: Usa entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## 🎓 Ejemplos Listos para Ejecutar

```bash
# Ejemplo básico
python examples/basic_usage.py

# Ejemplo avanzado
python examples/advanced_config.py

# Script de validación
python scripts/validate_pdf.py documento.pdf

# Procesamiento por lotes
python scripts/batch_process.py ./pdfs/ ./output/
```

## 📞 Soporte

- 📖 Documentación: Ver archivos `.md` en el proyecto
- 🐛 Problemas: Crear issue en GitHub
- 💬 Preguntas: Consultar `USAGE.md`

---

**¡Ya estás listo para extraer índices de notas!** 🎉

Para más información: `cat README.md` o `cat USAGE.md`
