"""
Interfaz base para exportadores.
"""
from abc import ABC, abstractmethod
from pathlib import Path

from ..models.extraction_result import ExtractionResult


class Exporter(ABC):
    """Clase base abstracta para exportadores."""
    
    @abstractmethod
    def export(
        self,
        result: ExtractionResult,
        output_path: Path
    ) -> None:
        """
        Exporta el resultado a un archivo.
        
        Args:
            result: Resultado de la extracción
            output_path: Path del archivo de salida
            
        Raises:
            ExportError: Si hay error en la exportación
        """
        pass
