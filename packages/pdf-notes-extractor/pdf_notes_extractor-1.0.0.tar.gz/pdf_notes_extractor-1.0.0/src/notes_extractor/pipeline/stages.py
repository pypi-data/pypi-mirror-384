"""
Etapas del pipeline de procesamiento.
"""
from enum import Enum
from typing import Dict, Any


class PipelineStage(Enum):
    """Etapas del pipeline."""
    VALIDATION = "validation"
    EXTRACTION = "extraction"
    DETECTION = "detection"
    PARSING = "parsing"
    NORMALIZATION = "normalization"
    MAPPING = "mapping"
    EXPORT = "export"
    COMPLETED = "completed"


class PipelineContext:
    """Contexto compartido entre etapas del pipeline."""
    
    def __init__(self):
        self.stage = PipelineStage.VALIDATION
        self.data: Dict[str, Any] = {}
        self.errors: list = []
        self.warnings: list = []
    
    def set_data(self, key: str, value: Any) -> None:
        """Establece un valor en el contexto."""
        self.data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor del contexto."""
        return self.data.get(key, default)
    
    def add_error(self, message: str) -> None:
        """Añade un error al contexto."""
        self.errors.append(message)
    
    def add_warning(self, message: str) -> None:
        """Añade un warning al contexto."""
        self.warnings.append(message)
    
    def has_errors(self) -> bool:
        """Verifica si hay errores."""
        return len(self.errors) > 0
