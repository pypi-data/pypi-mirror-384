"""
Extractor usando pdfplumber.
"""
from typing import Dict, Optional
from pathlib import Path

from .base import PDFExtractor
from ..exceptions import PDFExtractionError
from ..utils.logger import get_logger

logger = get_logger(__name__)

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


class PDFPlumberExtractor(PDFExtractor):
    """Extractor usando pdfplumber (default)."""
    
    def is_available(self) -> bool:
        """Verifica si pdfplumber está disponible."""
        return HAS_PDFPLUMBER
    
    def extract_text(
        self,
        pdf_path: Path,
        max_pages: Optional[int] = None
    ) -> Dict[int, str]:
        """
        Extrae texto usando pdfplumber.
        
        Args:
            pdf_path: Path al archivo PDF
            max_pages: Número máximo de páginas a procesar
            
        Returns:
            Diccionario {page_number: text}
        """
        self.validate_availability()
        
        logger.info(f"Extrayendo texto con pdfplumber: {pdf_path.name}")
        
        pages_text = {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
                
                logger.info(f"Procesando {pages_to_process} de {total_pages} páginas")
                
                for i, page in enumerate(pdf.pages[:pages_to_process], start=1):
                    try:
                        text = page.extract_text() or ""
                        pages_text[i] = text
                        
                        if i % 10 == 0:
                            logger.debug(f"Procesadas {i}/{pages_to_process} páginas")
                    
                    except Exception as e:
                        logger.warning(f"Error extrayendo página {i}: {e}")
                        pages_text[i] = ""
        
        except Exception as e:
            raise PDFExtractionError(
                f"Error al extraer texto con pdfplumber: {e}"
            ) from e
        
        logger.info(f"Extracción completada: {len(pages_text)} páginas")
        
        return pages_text
    
    def get_page_count(self, pdf_path: Path) -> int:
        """Obtiene el número total de páginas."""
        self.validate_availability()
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return len(pdf.pages)
        except Exception as e:
            raise PDFExtractionError(
                f"Error al obtener número de páginas: {e}"
            ) from e
