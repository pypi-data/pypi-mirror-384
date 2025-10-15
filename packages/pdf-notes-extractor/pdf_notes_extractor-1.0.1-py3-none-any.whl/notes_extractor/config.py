"""
Configuración centralizada del sistema.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ExtractorConfig:
    """Configuración para el sistema de extracción."""
    
    # Backend por defecto
    backend: str = "pdfplumber"
    
    # Límites de escaneo
    scan_first_n: Optional[int] = None
    max_pages_to_process: int = 100
    
    # Umbrales de detección
    min_note_lines: int = 3
    min_score_threshold: float = 5.0
    expansion_threshold_ratio: float = 0.35
    
    # Confianza
    min_confidence: float = 0.6
    
    # Mapeo de páginas
    enable_page_mapping: bool = True
    footer_crop_ratio: float = 0.15
    
    # Idioma
    language: str = "es"
    
    # Paths
    temp_dir: Path = field(default_factory=lambda: Path("./temp"))
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[Path] = None
    
    # Export
    export_format: str = "excel"
    include_metadata: bool = True
    
    @classmethod
    def from_env(cls) -> "ExtractorConfig":
        """Crea configuración desde variables de entorno."""
        return cls(
            backend=os.getenv("EXTRACTOR_BACKEND", "pdfplumber"),
            scan_first_n=int(os.getenv("SCAN_FIRST_N", "0")) or None,
            min_note_lines=int(os.getenv("MIN_NOTE_LINES", "3")),
            language=os.getenv("LANGUAGE", "es"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
