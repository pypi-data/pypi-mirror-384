"""
Modelo para páginas de índice detectadas.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class IndexPage:
    """Información sobre una página detectada como índice."""
    
    page_number: int
    """Número de página en el PDF (1-indexed)"""
    
    score: float = 0.0
    """Score de detección calculado por heurísticas"""
    
    note_count: int = 0
    """Cantidad de notas detectadas en esta página"""
    
    has_header: bool = False
    """Indica si tiene encabezado de índice"""
    
    dot_leaders_count: int = 0
    """Cantidad de líneas con puntos líderes"""
    
    confidence: float = 0.0
    """Confianza general de la detección [0-1]"""
    
    unique_notes: List[str] = field(default_factory=list)
    """Lista de IDs de notas únicas detectadas"""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Información adicional"""
    
    def __post_init__(self):
        """Validación post-inicialización."""
        if self.page_number < 1:
            raise ValueError("page_number debe ser >= 1")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence debe estar entre 0 y 1")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para exportación."""
        return {
            "page_number": self.page_number,
            "score": round(self.score, 2),
            "note_count": self.note_count,
            "unique_notes": len(self.unique_notes),
            "has_header": self.has_header,
            "dot_leaders": self.dot_leaders_count,
            "confidence": round(self.confidence, 2),
            **self.metadata
        }
