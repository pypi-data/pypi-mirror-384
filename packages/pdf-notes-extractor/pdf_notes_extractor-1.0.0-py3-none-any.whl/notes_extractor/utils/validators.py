"""
Validadores de entrada.
"""
from pathlib import Path
from typing import Union

from ..exceptions import InvalidPDFError
from ..config import ExtractorConfig


def validate_pdf_path(pdf_path: Union[str, Path]) -> Path:
    """
    Valida que el path del PDF sea válido y exista.
    
    Args:
        pdf_path: Path al archivo PDF
        
    Returns:
        Path validado
        
    Raises:
        InvalidPDFError: Si el path es inválido
    """
    path = Path(pdf_path)
    
    if not path.exists():
        raise InvalidPDFError(f"El archivo no existe: {path}")
    
    if not path.is_file():
        raise InvalidPDFError(f"El path no es un archivo: {path}")
    
    if path.suffix.lower() != '.pdf':
        raise InvalidPDFError(f"El archivo no es un PDF: {path}")
    
    # Verificar que sea legible
    if not path.stat().st_size > 0:
        raise InvalidPDFError(f"El archivo está vacío: {path}")
    
    return path


def validate_config(config: ExtractorConfig) -> None:
    """
    Valida la configuración del extractor.
    
    Args:
        config: Configuración a validar
        
    Raises:
        ValueError: Si la configuración es inválida
    """
    # Validar backend
    valid_backends = ["pdfplumber", "pymupdf", "pypdf2"]
    if config.backend not in valid_backends:
        raise ValueError(
            f"Backend inválido: {config.backend}. "
            f"Opciones válidas: {', '.join(valid_backends)}"
        )
    
    # Validar umbrales
    if config.min_note_lines < 1:
        raise ValueError("min_note_lines debe ser >= 1")
    
    if not 0 <= config.min_confidence <= 1:
        raise ValueError("min_confidence debe estar entre 0 y 1")
    
    if config.min_score_threshold < 0:
        raise ValueError("min_score_threshold debe ser >= 0")
    
    if not 0 <= config.expansion_threshold_ratio <= 1:
        raise ValueError("expansion_threshold_ratio debe estar entre 0 y 1")
    
    # Validar idioma
    valid_languages = ["es", "en"]
    if config.language not in valid_languages:
        raise ValueError(
            f"Idioma inválido: {config.language}. "
            f"Opciones válidas: {', '.join(valid_languages)}"
        )
