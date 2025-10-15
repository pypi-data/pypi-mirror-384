"""
Clase base abstracta para extractores de PDF.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from pathlib import Path

from ..exceptions import PDFExtractionError, BackendNotAvailableError


class PDFExtractor(ABC):
    """Clase base abstracta para extractores de PDF."""
    
    @abstractmethod
    def extract_text(
        self,
        pdf_path: Path,
        max_pages: Optional[int] = None
    ) -> Dict[int, str]:
        """
        Extrae texto de un PDF.
        
        Args:
            pdf_path: Path al archivo PDF
            max_pages: Número máximo de páginas a procesar (None = todas)
            
        Returns:
            Diccionario {page_number: text} (1-indexed)
            
        Raises:
            PDFExtractionError: Si hay error en la extracción
        """
        pass
    
    @abstractmethod
    def get_page_count(self, pdf_path: Path) -> int:
        """
        Obtiene el número total de páginas del PDF.
        
        Args:
            pdf_path: Path al archivo PDF
            
        Returns:
            Número de páginas
            
        Raises:
            PDFExtractionError: Si hay error al leer el PDF
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica si el backend está disponible (librerías instaladas).
        
        Returns:
            True si está disponible
        """
        pass
    
    def validate_availability(self) -> None:
        """
        Valida que el backend esté disponible.
        
        Raises:
            BackendNotAvailableError: Si el backend no está disponible
        """
        if not self.is_available():
            raise BackendNotAvailableError(
                f"El backend {self.__class__.__name__} no está disponible. "
                f"Instala las dependencias requeridas."
            )
    
    def extract_text_safe(
        self,
        pdf_path: Path,
        max_pages: Optional[int] = None
    ) -> Dict[int, str]:
        """
        Extrae texto de forma segura, validando disponibilidad.
        
        Args:
            pdf_path: Path al archivo PDF
            max_pages: Número máximo de páginas a procesar
            
        Returns:
            Diccionario {page_number: text}
            
        Raises:
            BackendNotAvailableError: Si el backend no está disponible
            PDFExtractionError: Si hay error en la extracción
        """
        self.validate_availability()
        return self.extract_text(pdf_path, max_pages)
