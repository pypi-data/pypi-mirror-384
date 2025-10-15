"""
Pipeline de procesamiento.
"""
from .orchestrator import NotesExtractorPipeline
from .stages import PipelineStage

__all__ = ["NotesExtractorPipeline", "PipelineStage"]
