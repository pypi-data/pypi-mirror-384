"""
Extractor usando PyMuPDF (fitz).
"""
from typing import Dict, Optional
from pathlib import Path

from .base import PDFExtractor
from ..exceptions import PDFExtractionError
from ..utils.logger import get_logger

logger = get_logger(__name__)

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


class PyMuPDFExtractor(PDFExtractor):
    """Extractor usando PyMuPDF."""
    
    def is_available(self) -> bool:
        """Verifica si PyMuPDF está disponible."""
        return HAS_PYMUPDF
    
    def extract_text(
        self,
        pdf_path: Path,
        max_pages: Optional[int] = None
    ) -> Dict[int, str]:
        """
        Extrae texto usando PyMuPDF.
        
        Args:
            pdf_path: Path al archivo PDF
            max_pages: Número máximo de páginas a procesar
            
        Returns:
            Diccionario {page_number: text}
        """
        self.validate_availability()
        
        logger.info(f"Extrayendo texto con PyMuPDF: {pdf_path.name}")
        
        pages_text = {}
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            pages_to_process = min(total_pages, max_pages) if max_pages else total_pages
            
            logger.info(f"Procesando {pages_to_process} de {total_pages} páginas")
            
            for i in range(pages_to_process):
                try:
                    page = doc[i]
                    text = page.get_text() or ""
                    pages_text[i + 1] = text  # 1-indexed
                    
                    if (i + 1) % 10 == 0:
                        logger.debug(f"Procesadas {i + 1}/{pages_to_process} páginas")
                
                except Exception as e:
                    logger.warning(f"Error extrayendo página {i + 1}: {e}")
                    pages_text[i + 1] = ""
            
            doc.close()
        
        except Exception as e:
            raise PDFExtractionError(
                f"Error al extraer texto con PyMuPDF: {e}"
            ) from e
        
        logger.info(f"Extracción completada: {len(pages_text)} páginas")
        
        return pages_text
    
    def get_page_count(self, pdf_path: Path) -> int:
        """Obtiene el número total de páginas."""
        self.validate_availability()
        
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            return page_count
        except Exception as e:
            raise PDFExtractionError(
                f"Error al obtener número de páginas: {e}"
            ) from e
