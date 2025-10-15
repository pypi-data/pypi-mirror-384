"""
CLI principal usando Click.
"""
import click
from pathlib import Path

from ..config import ExtractorConfig
from ..pipeline.orchestrator import NotesExtractorPipeline
from ..utils.logger import setup_logger
from .. import __version__


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    PDF Notes Extractor - Extractor automático de índices de notas desde PDFs financieros.
    """
    pass


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option(
    '-o', '--output',
    type=click.Path(),
    help='Ruta del archivo de salida'
)
@click.option(
    '--backend',
    type=click.Choice(['pdfplumber', 'pymupdf', 'pypdf2'], case_sensitive=False),
    default='pdfplumber',
    help='Backend de extracción de PDF'
)
@click.option(
    '--scan-first',
    type=int,
    help='Limitar escaneo a las primeras N páginas'
)
@click.option(
    '--min-note-lines',
    type=int,
    default=3,
    help='Mínimo de líneas de nota para considerar una página como índice'
)
@click.option(
    '--confidence-threshold',
    type=float,
    default=0.6,
    help='Umbral mínimo de confianza para entradas [0-1]'
)
@click.option(
    '--map-pages/--no-map-pages',
    default=True,
    help='Activar/desactivar mapeo de páginas impresas a PDF'
)
@click.option(
    '--lang',
    type=click.Choice(['es', 'en'], case_sensitive=False),
    default='es',
    help='Idioma del documento'
)
@click.option(
    '--debug',
    is_flag=True,
    help='Modo debug con logs detallados'
)
@click.option(
    '--format',
    type=click.Choice(['excel', 'json'], case_sensitive=False),
    default='excel',
    help='Formato de exportación'
)
def extract(
    pdf_path,
    output,
    backend,
    scan_first,
    min_note_lines,
    confidence_threshold,
    map_pages,
    lang,
    debug,
    format
):
    """
    Extrae el índice de notas de un PDF.
    
    Ejemplo:
        notes-extractor extract documento.pdf -o salida.xlsx
    """
    # Configurar logging
    log_level = "DEBUG" if debug else "INFO"
    setup_logger(level=log_level)
    
    # Crear configuración
    config = ExtractorConfig(
        backend=backend,
        scan_first_n=scan_first if scan_first else None,
        min_note_lines=min_note_lines,
        min_confidence=confidence_threshold,
        enable_page_mapping=map_pages,
        language=lang,
        log_level=log_level,
        export_format=format
    )
    
    # Determinar output path
    if not output:
        input_path = Path(pdf_path)
        ext = ".xlsx" if format == "excel" else ".json"
        output = input_path.parent / f"{input_path.stem}_notas{ext}"
    
    click.echo(f"\n📋 Procesando: {pdf_path}")
    click.echo(f"🔧 Backend: {backend}")
    click.echo(f"💾 Salida: {output}\n")
    
    # Ejecutar pipeline
    try:
        pipeline = NotesExtractorPipeline(config)
        result = pipeline.process(pdf_path, output)
        
        if result.success:
            click.secho("\n✅ Extracción completada con éxito!", fg='green', bold=True)
            click.echo(f"\n📊 Resultados:")
            click.echo(f"   • Notas encontradas: {result.notes_count}")
            click.echo(f"   • Páginas de índice: {result.index_pages_count}")
            click.echo(f"   • Confianza promedio: {result.average_confidence:.1%}")
            click.echo(f"   • Tiempo: {result.processing_time:.2f}s")
            click.echo(f"\n💾 Archivo generado: {output}")
        else:
            click.secho(f"\n❌ Error: {result.error_message}", fg='red', bold=True)
            raise click.Abort()
    
    except Exception as e:
        click.secho(f"\n❌ Error: {e}", fg='red', bold=True)
        if debug:
            raise
        raise click.Abort()


@cli.command()
@click.argument('pdf_path', type=click.Path(exists=True))
@click.option(
    '--backend',
    type=click.Choice(['pdfplumber', 'pymupdf', 'pypdf2'], case_sensitive=False),
    default='pdfplumber',
    help='Backend a validar'
)
def validate(pdf_path, backend):
    """
    Valida un PDF y verifica si es procesable.
    
    Ejemplo:
        notes-extractor validate documento.pdf
    """
    from ..utils.validators import validate_pdf_path
    from ..extractors import get_extractor
    
    click.echo(f"\n🔍 Validando: {pdf_path}")
    
    try:
        # Validar path
        path = validate_pdf_path(pdf_path)
        click.secho("✓ Archivo válido", fg='green')
        
        # Verificar backend
        extractor = get_extractor(backend)
        if not extractor.is_available():
            click.secho(f"✗ Backend {backend} no disponible", fg='red')
            click.echo("  Instala las dependencias necesarias")
            raise click.Abort()
        
        click.secho(f"✓ Backend {backend} disponible", fg='green')
        
        # Extraer info básica
        page_count = extractor.get_page_count(path)
        click.secho(f"✓ Páginas: {page_count}", fg='green')
        
        # Extraer primera página como test
        pages_text = extractor.extract_text(path, max_pages=1)
        text_length = len(pages_text.get(1, ""))
        
        if text_length > 0:
            click.secho(f"✓ Texto extraíble (primera página: {text_length} caracteres)", fg='green')
        else:
            click.secho("⚠ Advertencia: No se extrajo texto de la primera página", fg='yellow')
            click.echo("  El PDF podría estar escaneado o no contener texto")
        
        click.secho("\n✅ PDF válido y procesable", fg='green', bold=True)
    
    except Exception as e:
        click.secho(f"\n❌ Error: {e}", fg='red', bold=True)
        raise click.Abort()


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False))
@click.option(
    '-o', '--output-dir',
    type=click.Path(),
    help='Directorio de salida'
)
@click.option(
    '--backend',
    type=click.Choice(['pdfplumber', 'pymupdf', 'pypdf2'], case_sensitive=False),
    default='pdfplumber',
    help='Backend de extracción'
)
@click.option(
    '--pattern',
    default='*.pdf',
    help='Patrón de archivos a procesar'
)
def batch(input_dir, output_dir, backend, pattern):
    """
    Procesa múltiples PDFs en un directorio.
    
    Ejemplo:
        notes-extractor batch ./pdfs/ -o ./outputs/
    """
    from pathlib import Path
    
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path / "output"
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Buscar PDFs
    pdf_files = list(input_path.glob(pattern))
    
    if not pdf_files:
        click.secho(f"No se encontraron PDFs en {input_dir}", fg='yellow')
        return
    
    click.echo(f"\n📁 Procesando {len(pdf_files)} archivos...")
    click.echo(f"📂 Directorio de salida: {output_path}\n")
    
    # Crear configuración
    config = ExtractorConfig(backend=backend)
    pipeline = NotesExtractorPipeline(config)
    
    # Procesar cada archivo
    results = []
    for i, pdf_file in enumerate(pdf_files, 1):
        click.echo(f"[{i}/{len(pdf_files)}] Procesando: {pdf_file.name}")
        
        output_file = output_path / f"{pdf_file.stem}_notas.xlsx"
        
        try:
            result = pipeline.process(pdf_file, output_file)
            results.append((pdf_file.name, result.success, result.notes_count))
            
            if result.success:
                click.secho(f"  ✓ Éxito: {result.notes_count} notas", fg='green')
            else:
                click.secho(f"  ✗ Error: {result.error_message}", fg='red')
        
        except Exception as e:
            results.append((pdf_file.name, False, 0))
            click.secho(f"  ✗ Error: {e}", fg='red')
    
    # Resumen
    successful = sum(1 for _, success, _ in results if success)
    total_notes = sum(notes for _, success, notes in results if success)
    
    click.echo(f"\n{'='*50}")
    click.echo(f"📊 Resumen del procesamiento por lotes:")
    click.echo(f"   • Total procesados: {len(results)}")
    click.echo(f"   • Exitosos: {successful}")
    click.echo(f"   • Fallidos: {len(results) - successful}")
    click.echo(f"   • Total notas extraídas: {total_notes}")
    click.echo(f"{'='*50}\n")


if __name__ == '__main__':
    cli()
