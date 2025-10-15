"""
Exportador a formato JSON.
"""
import json
from pathlib import Path

from .base import Exporter
from ..models.extraction_result import ExtractionResult
from ..exceptions import ExportError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class JSONExporter(Exporter):
    """Exporta resultados a formato JSON."""
    
    def export(
        self,
        result: ExtractionResult,
        output_path: Path
    ) -> None:
        """
        Exporta a JSON.
        
        Args:
            result: Resultado de la extracción
            output_path: Path del archivo de salida
        """
        logger.info(f"Exportando a JSON: {output_path}")
        
        try:
            # Construir estructura JSON
            data = {
                "metadata": result.to_dict(),
                "notes": [note.to_dict() for note in result.notes],
                "index_pages": [page.to_dict() for page in result.index_pages]
            }
            
            # Escribir archivo
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exportación completada: {output_path}")
        
        except Exception as e:
            raise ExportError(f"Error al exportar a JSON: {e}") from e
