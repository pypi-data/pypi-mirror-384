"""
Extractores de texto de PDFs.
"""
from .base import PDFExtractor
from .pdfplumber_extractor import PDFPlumberExtractor
from .pymupdf_extractor import PyMuPDFExtractor
from .pypdf2_extractor import PyPDF2Extractor

__all__ = [
    "PDFExtractor",
    "PDFPlumberExtractor",
    "PyMuPDFExtractor",
    "PyPDF2Extractor"
]


def get_extractor(backend: str = "pdfplumber") -> PDFExtractor:
    """
    Factory para obtener un extractor según el backend.
    
    Args:
        backend: Nombre del backend ('pdfplumber', 'pymupdf', 'pypdf2')
        
    Returns:
        Instancia del extractor
        
    Raises:
        ValueError: Si el backend no es válido
    """
    extractors = {
        "pdfplumber": PDFPlumberExtractor,
        "pymupdf": PyMuPDFExtractor,
        "pypdf2": PyPDF2Extractor
    }
    
    extractor_class = extractors.get(backend.lower())
    
    if not extractor_class:
        raise ValueError(
            f"Backend inválido: {backend}. "
            f"Opciones: {', '.join(extractors.keys())}"
        )
    
    return extractor_class()
