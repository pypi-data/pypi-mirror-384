"""
Modelo de datos para entradas de notas.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class NoteEntry:
    """Representa una entrada de nota del índice."""
    
    nota_id: str
    """Identificador de la nota (e.g., '1', '1.1', 'II')"""
    
    titulo: str = ""
    """Título o descripción de la nota"""
    
    pagina_impresa: int = 0
    """Número de página según aparece en el índice"""
    
    pagina_pdf: Optional[int] = None
    """Número de página real en el PDF (si se mapea)"""
    
    pagina_fuente: int = 0
    """Página del PDF donde se encontró esta entrada"""
    
    confianza: float = 0.0
    """Score de confianza de la extracción [0-1]"""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Metadata adicional"""
    
    timestamp: datetime = field(default_factory=datetime.now)
    """Timestamp de extracción"""
    
    def __post_init__(self):
        """Validación post-inicialización."""
        if not self.nota_id:
            raise ValueError("nota_id no puede estar vacío")
        if not 0 <= self.confianza <= 1:
            raise ValueError("confianza debe estar entre 0 y 1")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para exportación."""
        return {
            "nota_id": self.nota_id,
            "titulo": self.titulo,
            "pagina_impresa": self.pagina_impresa,
            "pagina_pdf": self.pagina_pdf,
            "pagina_fuente": self.pagina_fuente,
            "confianza": round(self.confianza, 2),
            **self.metadata
        }
    
    @property
    def is_subnote(self) -> bool:
        """Verifica si es una subnota (e.g., 1.1)."""
        return "." in self.nota_id or "-" in self.nota_id
    
    @property
    def is_roman(self) -> bool:
        """Verifica si usa numeración romana."""
        return all(c in "IVXLC" for c in self.nota_id.upper())
