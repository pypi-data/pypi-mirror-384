"""
Excepciones personalizadas del sistema.
"""


class NotesExtractorError(Exception):
    """Excepción base para el extractor de notas."""
    pass


class PDFExtractionError(NotesExtractorError):
    """Error durante la extracción de texto del PDF."""
    pass


class IndexNotFoundError(NotesExtractorError):
    """No se encontró índice de notas en el PDF."""
    pass


class InvalidPDFError(NotesExtractorError):
    """El archivo PDF es inválido o está corrupto."""
    pass


class BackendNotAvailableError(NotesExtractorError):
    """El backend seleccionado no está disponible."""
    pass


class ParsingError(NotesExtractorError):
    """Error durante el parsing de entradas del índice."""
    pass


class ExportError(NotesExtractorError):
    """Error durante la exportación de resultados."""
    pass
