"""
Modelo para resultados de extracción.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .note_entry import NoteEntry
from .index_page import IndexPage


@dataclass
class ExtractionResult:
    """Resultado completo de la extracción."""
    
    pdf_path: Path
    """Ruta del PDF procesado"""
    
    notes: List[NoteEntry] = field(default_factory=list)
    """Lista de notas extraídas"""
    
    index_pages: List[IndexPage] = field(default_factory=list)
    """Páginas detectadas como índice"""
    
    success: bool = True
    """Indica si la extracción fue exitosa"""
    
    error_message: Optional[str] = None
    """Mensaje de error si la extracción falló"""
    
    processing_time: float = 0.0
    """Tiempo de procesamiento en segundos"""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Metadata adicional del proceso"""
    
    timestamp: datetime = field(default_factory=datetime.now)
    """Timestamp del proceso"""
    
    @property
    def notes_count(self) -> int:
        """Cantidad de notas extraídas."""
        return len(self.notes)
    
    @property
    def index_pages_count(self) -> int:
        """Cantidad de páginas de índice detectadas."""
        return len(self.index_pages)
    
    @property
    def average_confidence(self) -> float:
        """Confianza promedio de las notas extraídas."""
        if not self.notes:
            return 0.0
        return sum(n.confianza for n in self.notes) / len(self.notes)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para exportación."""
        return {
            "pdf_path": str(self.pdf_path),
            "notes_count": self.notes_count,
            "index_pages_count": self.index_pages_count,
            "average_confidence": round(self.average_confidence, 2),
            "success": self.success,
            "error_message": self.error_message,
            "processing_time": round(self.processing_time, 2),
            "timestamp": self.timestamp.isoformat(),
            **self.metadata
        }
    
    def get_summary(self) -> str:
        """Genera un resumen legible del resultado."""
        if not self.success:
            return f"❌ Error: {self.error_message}"
        
        summary = [
            f"✅ Extracción exitosa",
            f"📄 PDF: {self.pdf_path.name}",
            f"📝 Notas encontradas: {self.notes_count}",
            f"📑 Páginas de índice: {self.index_pages_count}",
            f"⭐ Confianza promedio: {self.average_confidence:.2%}",
            f"⏱️  Tiempo: {self.processing_time:.2f}s"
        ]
        return "\n".join(summary)
