"""
PDF Notes Extractor - Extractor automático de índices de notas desde PDFs financieros.
"""
__version__ = "1.0.0"
__author__ = "Tu Nombre"

from .pipeline.orchestrator import NotesExtractorPipeline
from .models.note_entry import NoteEntry
from .models.extraction_result import ExtractionResult

__all__ = ["NotesExtractorPipeline", "NoteEntry", "ExtractionResult"]
