"""
Exportadores de resultados.
"""
from .base import Exporter
from .excel_exporter import ExcelExporter
from .json_exporter import JSONExporter

__all__ = ["Exporter", "ExcelExporter", "JSONExporter"]


def get_exporter(format: str = "excel") -> Exporter:
    """
    Factory para obtener un exportador según el formato.
    
    Args:
        format: Formato de exportación ('excel', 'json')
        
    Returns:
        Instancia del exportador
        
    Raises:
        ValueError: Si el formato no es válido
    """
    exporters = {
        "excel": ExcelExporter,
        "json": JSONExporter
    }
    
    exporter_class = exporters.get(format.lower())
    
    if not exporter_class:
        raise ValueError(
            f"Formato inválido: {format}. "
            f"Opciones: {', '.join(exporters.keys())}"
        )
    
    return exporter_class()
