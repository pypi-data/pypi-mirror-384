"""
PDF Notes Extractor - Extractor automático de índices de notas desde PDFs financieros.
"""
__version__ = "1.0.1"
__author__ = "Diego Jiménez"

from .pipeline.orchestrator import NotesExtractorPipeline
from .models.note_entry import NoteEntry
from .models.extraction_result import ExtractionResult

__all__ = ["NotesExtractorPipeline", "NoteEntry", "ExtractionResult"]
