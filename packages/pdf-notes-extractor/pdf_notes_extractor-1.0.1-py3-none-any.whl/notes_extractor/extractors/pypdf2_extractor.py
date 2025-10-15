"""
Extractor usando PyPDF2.
"""
from typing import Dict, Optional
from pathlib import Path

from .base import PDFExtractor
from ..exceptions import PDFExtractionError
from ..utils.logger import get_logger

logger = get_logger(__name__)

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False


class PyPDF2Extractor(PDFExtractor):
    """Extractor usando PyPDF2."""
    
    def is_available(self) -> bool:
        """Verifica si PyPDF2 está disponible."""
        return HAS_PYPDF2
    
    def extract_text(
        self,
        pdf_path: Path,
        max_pages: Optional[int] = None
    ) -> Dict[int, str]:
        """
        Extrae texto usando PyPDF2.
        
        Args:
            pdf_path: Path al archivo PDF
            max_pages: Número máximo de páginas a procesar
            
        Returns:
            Diccionario {page_number: text}
        """
        self.validate_availability()
        
        logger.info(f"Extrayendo texto con PyPDF2: {pdf_path.name}")
        
        pages_text = {}
        
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
            
            logger.info(f"Procesando {pages_to_process} de {total_pages} páginas")
            
            for i in range(pages_to_process):
                try:
                    page = reader.pages[i]
                    text = page.extract_text() or ""
                    pages_text[i + 1] = text  # 1-indexed
                    
                    if (i + 1) % 10 == 0:
                        logger.debug(f"Procesadas {i + 1}/{pages_to_process} páginas")
                
                except Exception as e:
                    logger.warning(f"Error extrayendo página {i + 1}: {e}")
                    pages_text[i + 1] = ""
        
        except Exception as e:
            raise PDFExtractionError(
                f"Error al extraer texto con PyPDF2: {e}"
            ) from e
        
        logger.info(f"Extracción completada: {len(pages_text)} páginas")
        
        return pages_text
    
    def get_page_count(self, pdf_path: Path) -> int:
        """Obtiene el número total de páginas."""
        self.validate_availability()
        
        try:
            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except Exception as e:
            raise PDFExtractionError(
                f"Error al obtener número de páginas: {e}"
            ) from e
