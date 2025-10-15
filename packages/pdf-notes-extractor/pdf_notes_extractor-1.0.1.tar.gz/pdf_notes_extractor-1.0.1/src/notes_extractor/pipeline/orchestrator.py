"""
Orquestador principal del pipeline.
"""
import time
from pathlib import Path
from typing import Optional, Union

from ..config import ExtractorConfig
from ..models.extraction_result import ExtractionResult
from ..models.note_entry import NoteEntry
from ..models.index_page import IndexPage
from ..extractors import get_extractor
from ..exporters import get_exporter
from ..core.heuristics import IndexDetector
from ..core.parser import IndexParser
from ..core.normalizer import DataNormalizer
from ..core.mapper import PageMapper
from ..utils.logger import get_logger, setup_logger
from ..utils.validators import validate_pdf_path, validate_config
from ..utils.file_utils import get_output_path
from ..exceptions import (
    IndexNotFoundError,
    PDFExtractionError,
    NotesExtractorError
)
from .stages import PipelineStage, PipelineContext

logger = get_logger(__name__)


class NotesExtractorPipeline:
    """Pipeline principal de extracción de notas."""
    
    def __init__(self, config: Optional[ExtractorConfig] = None):
        """
        Inicializa el pipeline.
        
        Args:
            config: Configuración del sistema (opcional)
        """
        self.config = config or ExtractorConfig()
        
        # Configurar logging
        setup_logger(
            level=self.config.log_level,
            log_file=self.config.log_file
        )
        
        # Validar configuración
        validate_config(self.config)
        
        logger.info(f"Pipeline inicializado con backend: {self.config.backend}")
    
    def process(
        self,
        pdf_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None
    ) -> ExtractionResult:
        """
        Procesa un PDF y extrae el índice de notas.
        
        Args:
            pdf_path: Path al archivo PDF
            output_path: Path de salida (opcional)
            
        Returns:
            ExtractionResult con los resultados
        """
        start_time = time.time()
        context = PipelineContext()
        
        try:
            # Validación
            pdf_path = self._stage_validation(pdf_path, context)
            
            # Extracción de texto
            pages_text = self._stage_extraction(pdf_path, context)
            
            # Detección de índices
            index_pages = self._stage_detection(pages_text, context)
            
            # Parsing de entradas
            entries = self._stage_parsing(index_pages, pages_text, context)
            
            # Normalización
            normalized_entries = self._stage_normalization(entries, context)
            
            # Mapeo de páginas (opcional)
            mapped_entries = self._stage_mapping(normalized_entries, pages_text, context)
            
            # Crear resultado
            processing_time = time.time() - start_time
            result = ExtractionResult(
                pdf_path=pdf_path,
                notes=mapped_entries,
                index_pages=index_pages,
                success=True,
                processing_time=processing_time,
                metadata={
                    "backend": self.config.backend,
                    "pages_processed": len(pages_text),
                    "warnings": context.warnings
                }
            )
            
            # Exportación
            if output_path:
                self._stage_export(result, output_path, context)
            
            logger.info(f"✅ Procesamiento completado en {processing_time:.2f}s")
            logger.info(result.get_summary())
            
            return result
        
        except Exception as e:
            processing_time = time.time() - start_time
            
            logger.error(f"❌ Error en el procesamiento: {e}")
            
            return ExtractionResult(
                pdf_path=Path(pdf_path) if isinstance(pdf_path, str) else pdf_path,
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )
    
    def _stage_validation(
        self,
        pdf_path: Union[str, Path],
        context: PipelineContext
    ) -> Path:
        """Etapa de validación."""
        context.stage = PipelineStage.VALIDATION
        logger.info(f"📋 Etapa: Validación")
        
        validated_path = validate_pdf_path(pdf_path)
        
        logger.info(f"✓ PDF válido: {validated_path.name}")
        
        return validated_path
    
    def _stage_extraction(
        self,
        pdf_path: Path,
        context: PipelineContext
    ) -> dict:
        """Etapa de extracción de texto."""
        context.stage = PipelineStage.EXTRACTION
        logger.info(f"📄 Etapa: Extracción de texto")
        
        extractor = get_extractor(self.config.backend)
        
        # Obtener número total de páginas
        total_pages = extractor.get_page_count(pdf_path)
        logger.info(f"Total de páginas en PDF: {total_pages}")
        
        # Extraer texto
        max_pages = self.config.scan_first_n
        if max_pages:
            logger.info(f"Limitando escaneo a primeras {max_pages} páginas")
        
        pages_text = extractor.extract_text_safe(pdf_path, max_pages)
        
        if not pages_text:
            raise PDFExtractionError("No se pudo extraer texto del PDF")
        
        logger.info(f"✓ Texto extraído de {len(pages_text)} páginas")
        
        return pages_text
    
    def _stage_detection(
        self,
        pages_text: dict,
        context: PipelineContext
    ) -> list:
        """Etapa de detección de índices."""
        context.stage = PipelineStage.DETECTION
        logger.info(f"🔍 Etapa: Detección de índices")
        
        detector = IndexDetector(self.config)
        index_pages = detector.detect_index_pages(pages_text)
        
        if not index_pages:
            raise IndexNotFoundError(
                "No se detectaron páginas de índice en el PDF. "
                "Intenta ajustar los umbrales de configuración."
            )
        
        logger.info(f"✓ Detectadas {len(index_pages)} páginas de índice")
        
        return index_pages
    
    def _stage_parsing(
        self,
        index_pages: list,
        pages_text: dict,
        context: PipelineContext
    ) -> list:
        """Etapa de parsing de entradas."""
        context.stage = PipelineStage.PARSING
        logger.info(f"🔧 Etapa: Parsing de entradas")
        
        parser = IndexParser(self.config)
        entries = parser.parse_index_pages(index_pages, pages_text)
        
        if not entries:
            raise NotesExtractorError("No se pudieron extraer entradas del índice")
        
        # Filtrar entradas válidas
        valid_entries = parser.filter_valid_entries(entries)
        
        if not valid_entries:
            raise NotesExtractorError(
                "No se encontraron entradas válidas después del filtrado"
            )
        
        logger.info(f"✓ Parseadas {len(valid_entries)} entradas válidas")
        
        return valid_entries
    
    def _stage_normalization(
        self,
        entries: list,
        context: PipelineContext
    ) -> list:
        """Etapa de normalización."""
        context.stage = PipelineStage.NORMALIZATION
        logger.info(f"🔄 Etapa: Normalización")
        
        normalizer = DataNormalizer()
        normalized = normalizer.normalize_and_consolidate(entries)
        
        # Validar secuencia
        stats = normalizer.validate_sequence(normalized)
        
        if stats["gaps"]:
            context.add_warning(
                f"Se detectaron {len(stats['gaps'])} gaps en la secuencia de notas"
            )
        
        logger.info(f"✓ Normalizadas {len(normalized)} entradas")
        
        return normalized
    
    def _stage_mapping(
        self,
        entries: list,
        pages_text: dict,
        context: PipelineContext
    ) -> list:
        """Etapa de mapeo de páginas."""
        context.stage = PipelineStage.MAPPING
        
        if not self.config.enable_page_mapping:
            logger.info("⏭️  Etapa: Mapeo de páginas (deshabilitado)")
            return entries
        
        logger.info(f"🗺️  Etapa: Mapeo de páginas")
        
        mapper = PageMapper(self.config)
        mapped = mapper.map_pages(entries, pages_text)
        
        # Validar mapeo
        stats = mapper.validate_mapping(mapped, pages_text)
        
        if stats["success_rate"] < 0.5:
            context.add_warning(
                f"Tasa de éxito de mapeo baja: {stats['success_rate']:.1%}"
            )
        
        logger.info(f"✓ Mapeadas {stats['valid_mappings']} páginas")
        
        return mapped
    
    def _stage_export(
        self,
        result: ExtractionResult,
        output_path: Union[str, Path],
        context: PipelineContext
    ) -> None:
        """Etapa de exportación."""
        context.stage = PipelineStage.EXPORT
        logger.info(f"💾 Etapa: Exportación")
        
        output_path = Path(output_path)
        
        # Si no se especificó extensión, usar la configuración
        if not output_path.suffix:
            ext = ".xlsx" if self.config.export_format == "excel" else ".json"
            output_path = output_path.with_suffix(ext)
        
        # Determinar formato por extensión
        format = "excel" if output_path.suffix == ".xlsx" else "json"
        
        exporter = get_exporter(format)
        exporter.export(result, output_path)
        
        logger.info(f"✓ Exportado a: {output_path}")
