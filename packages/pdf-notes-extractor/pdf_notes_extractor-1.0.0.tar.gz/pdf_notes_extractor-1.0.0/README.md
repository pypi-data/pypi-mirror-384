# 📋 PDF Notes Extractor

Extractor automático de índices de notas desde PDFs de estados financieros chilenos (formato NIIF).

## 🎯 Descripción

Este proyecto automatiza la detección y extracción de índices de notas desde PDFs de estados financieros, generando un archivo Excel estructurado con la relación nota-página y métricas de confianza.

### Características principales

- ✅ **Detección automática** de páginas de índice usando heurísticas robustas
- ✅ **Soporte multi-backend**: pdfplumber (default), PyMuPDF, PyPDF2
- ✅ **Parsing inteligente** de múltiples formatos de índice
- ✅ **Mapeo automático** de páginas impresas → páginas PDF
- ✅ **Exportación a Excel** con métricas de confianza
- ✅ **CLI amigable** con múltiples opciones de configuración
- ✅ **Arquitectura extensible** y bien documentada

## 📦 Instalación

### Requisitos

- Python 3.8 o superior
- pip

### Instalación básica

```bash
# Clonar repositorio
git clone <repo-url>
cd Table-Detector

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias básicas
pip install -e .
```

### Instalación con backends alternativos

```bash
# Para PyMuPDF y PyPDF2
pip install -e ".[alternative]"
```

### Instalación para desarrollo

```bash
# Incluye herramientas de testing y linting
pip install -e ".[dev]"
```

## 🚀 Uso

### CLI Básico

```bash
# Extracción básica
notes-extractor extract input.pdf -o output.xlsx

# Con backend específico
notes-extractor extract input.pdf -o output.xlsx --backend pymupdf

# Con límite de páginas a escanear
notes-extractor extract input.pdf -o output.xlsx --scan-first 50

# Con mapeo de páginas
notes-extractor extract input.pdf -o output.xlsx --map-pages

# Modo debug
notes-extractor extract input.pdf -o output.xlsx --debug
```

### Uso como librería

```python
from notes_extractor.pipeline.orchestrator import NotesExtractorPipeline
from notes_extractor.config import ExtractorConfig

# Configurar
config = ExtractorConfig(
    backend="pdfplumber",
    enable_page_mapping=True,
    min_confidence=0.6
)

# Ejecutar pipeline
pipeline = NotesExtractorPipeline(config)
result = pipeline.process("input.pdf", "output.xlsx")

# Acceder a resultados
print(f"Notas encontradas: {len(result.notes)}")
for note in result.notes:
    print(f"{note.nota_id}: {note.titulo} - Pág. {note.pagina_impresa}")
```

## 📊 Formato de Salida

El archivo Excel generado contiene dos hojas:

### Hoja 1: notas_paginas
| nota_id | titulo | pagina_impresa | pagina_pdf | pagina_fuente | confianza |
|---------|--------|----------------|------------|---------------|-----------|
| 1 | Información general | 15 | 17 | 3 | 0.95 |
| 2 | Políticas contables | 18 | 20 | 3 | 0.92 |

### Hoja 2: index_pages
| page_number | score | note_count | has_header | confidence |
|-------------|-------|------------|------------|------------|
| 3 | 25.5 | 15 | True | 0.89 |
| 4 | 22.3 | 12 | False | 0.85 |

## 🏗️ Arquitectura

```
Pipeline de Procesamiento:
PDF → Validación → Extracción de Texto → Detección de Índice → 
Parsing → Normalización → Mapeo (opcional) → Exportación
```

Consulta `Estructura.md` para detalles completos de la arquitectura.

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=src/notes_extractor --cov-report=html

# Solo tests unitarios
pytest tests/unit/

# Solo tests de integración
pytest tests/integration/
```

## 📚 Documentación

- [Arquitectura detallada](docs/architecture.md)
- [Guía de patrones regex](docs/patterns.md)
- [Ejemplos avanzados](docs/examples.md)
- [API Reference](docs/api.md)

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 🐛 Reportar Problemas

Si encuentras un bug o tienes una sugerencia, por favor abre un issue en GitHub.

## 📧 Contacto

Tu Nombre - tu@email.com

Project Link: [https://github.com/tuusuario/Table-Detector](https://github.com/tuusuario/Table-Detector)
