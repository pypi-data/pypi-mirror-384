# 📦 Guía de Instalación

## Requisitos del Sistema

- **Python**: 3.8 o superior
- **Sistema operativo**: Windows, macOS, o Linux
- **Espacio en disco**: ~100 MB (incluidas dependencias)

## Instalación Básica

### 1. Clonar el repositorio

```bash
git clone <repo-url>
cd Table-Detector
```

### 2. Crear entorno virtual (recomendado)

**En macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar el paquete

**Instalación básica (solo pdfplumber):**
```bash
pip install -e .
```

**Con backends alternativos:**
```bash
pip install -e ".[alternative]"
```

**Para desarrollo (incluye herramientas de testing):**
```bash
pip install -e ".[dev,alternative]"
```

## Verificación de la Instalación

Verifica que la instalación fue exitosa:

```bash
notes-extractor --version
```

Deberías ver la versión instalada (e.g., `1.0.0`).

## Configuración Inicial

### Crear archivo .env (opcional)

Copia el archivo de ejemplo:

```bash
cp .env.example .env
```

Edita `.env` según tus preferencias:

```bash
EXTRACTOR_BACKEND=pdfplumber
SCAN_FIRST_N=0
MIN_NOTE_LINES=3
LANGUAGE=es
LOG_LEVEL=INFO
```

## Instalación de Backends Alternativos

### PyMuPDF (fitz)

```bash
pip install PyMuPDF>=1.24.0
```

### PyPDF2

```bash
pip install PyPDF2>=3.0.0
```

## Verificar Backend

Puedes verificar qué backends están disponibles:

```bash
python -c "
from notes_extractor.extractors import get_extractor

for backend in ['pdfplumber', 'pymupdf', 'pypdf2']:
    try:
        ext = get_extractor(backend)
        status = '✓ Disponible' if ext.is_available() else '✗ No disponible'
        print(f'{backend}: {status}')
    except Exception as e:
        print(f'{backend}: ✗ Error - {e}')
"
```

## Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'pdfplumber'"

**Solución:**
```bash
pip install pdfplumber>=0.11.0
```

### Error: "Backend not available"

**Causa:** El backend seleccionado no está instalado.

**Solución:**
```bash
# Para PyMuPDF
pip install PyMuPDF

# Para PyPDF2
pip install PyPDF2
```

### Error en Windows: "Microsoft Visual C++ 14.0 is required"

**Solución:** Instala las herramientas de compilación:
- Descarga e instala [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### Problemas con permisos en macOS/Linux

**Solución:** Usa `--user` o un entorno virtual:
```bash
pip install --user -e .
```

## Actualización

Para actualizar el paquete:

```bash
git pull
pip install -e . --upgrade
```

## Desinstalación

Para desinstalar:

```bash
pip uninstall pdf-notes-extractor
```

Para limpiar archivos generados:

```bash
make clean  # Si usas Makefile
# o manualmente:
rm -rf build/ dist/ *.egg-info .pytest_cache __pycache__
```

## Instalación en Producción

Para un entorno de producción:

```bash
# 1. Instalar desde git con versión específica
pip install git+https://github.com/usuario/Table-Detector.git@v1.0.0

# 2. O desde un archivo wheel
pip install pdf_notes_extractor-1.0.0-py3-none-any.whl
```

## Docker (Opcional)

Si prefieres usar Docker, puedes crear un Dockerfile:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install -e ".[alternative]"

CMD ["notes-extractor", "--help"]
```

Construir y ejecutar:

```bash
docker build -t notes-extractor .
docker run -v $(pwd):/data notes-extractor extract /data/input.pdf -o /data/output.xlsx
```

## Soporte

Si encuentras problemas durante la instalación:

1. Revisa los [issues en GitHub](https://github.com/usuario/Table-Detector/issues)
2. Crea un nuevo issue con detalles de tu sistema y el error
3. Contacta al mantenedor

## Próximos Pasos

Una vez instalado, consulta:
- [README.md](README.md) - Uso básico
- [examples/](examples/) - Ejemplos de código
- [docs/](docs/) - Documentación completa
