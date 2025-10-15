"""
Mapeo de páginas impresas a páginas PDF reales.
"""
from typing import Dict, List, Optional, Tuple
from collections import Counter

from ..models.note_entry import NoteEntry
from ..config import ExtractorConfig
from ..utils.logger import get_logger
from .patterns import PatternMatcher

logger = get_logger(__name__)


class PageMapper:
    """Mapea páginas impresas a páginas PDF reales."""
    
    def __init__(self, config: ExtractorConfig):
        """
        Inicializa el mapper.
        
        Args:
            config: Configuración del sistema
        """
        self.config = config
        self.pattern_matcher = PatternMatcher(config.language)
    
    def map_pages(
        self,
        entries: List[NoteEntry],
        pages_text: Dict[int, str]
    ) -> List[NoteEntry]:
        """
        Intenta mapear páginas impresas a páginas PDF reales.
        
        Args:
            entries: Lista de entradas con páginas impresas
            pages_text: Diccionario {page_number: text}
            
        Returns:
            Lista de entradas con páginas PDF mapeadas
        """
        if not self.config.enable_page_mapping:
            logger.info("Mapeo de páginas deshabilitado")
            return entries
        
        logger.info("Intentando mapear páginas impresas a páginas PDF...")
        
        # Extraer numeración de pies de página
        footer_mappings = self._extract_footer_numbers(pages_text)
        
        if not footer_mappings:
            logger.warning("No se pudieron extraer números de pie de página")
            return entries
        
        # Calcular offset
        offset = self._calculate_offset(footer_mappings)
        
        if offset is None:
            logger.warning("No se pudo calcular offset de páginas")
            return entries
        
        logger.info(f"Offset calculado: {offset}")
        
        # Aplicar mapeo
        mapped_count = 0
        for entry in entries:
            if entry.pagina_impresa > 0:
                entry.pagina_pdf = entry.pagina_impresa + offset
                
                # Validar que esté en rango
                if 1 <= entry.pagina_pdf <= len(pages_text):
                    mapped_count += 1
                else:
                    entry.pagina_pdf = None
        
        logger.info(
            f"Páginas mapeadas: {mapped_count} de {len([e for e in entries if e.pagina_impresa > 0])}"
        )
        
        return entries
    
    def _extract_footer_numbers(
        self,
        pages_text: Dict[int, str]
    ) -> Dict[int, int]:
        """
        Extrae números de página de los pies de página.
        
        Args:
            pages_text: Diccionario {page_number: text}
            
        Returns:
            Diccionario {pdf_page: printed_page}
        """
        mappings = {}
        crop_ratio = self.config.footer_crop_ratio
        
        for pdf_page, text in pages_text.items():
            # Extraer zona de pie de página (últimas líneas)
            lines = text.split('\n')
            footer_lines_count = max(1, int(len(lines) * crop_ratio))
            footer_text = ' '.join(lines[-footer_lines_count:])
            
            # Buscar número de página
            printed_page = self.pattern_matcher.match_footer_page(footer_text)
            
            if printed_page:
                mappings[pdf_page] = printed_page
                logger.debug(f"Página PDF {pdf_page} -> Impresa {printed_page}")
        
        logger.info(f"Extraídos {len(mappings)} números de pie de página")
        
        return mappings
    
    def _calculate_offset(
        self,
        mappings: Dict[int, int]
    ) -> Optional[int]:
        """
        Calcula el offset entre páginas PDF e impresas.
        
        Args:
            mappings: Diccionario {pdf_page: printed_page}
            
        Returns:
            Offset calculado o None si no es consistente
        """
        if len(mappings) < 2:
            logger.warning("Insuficientes muestras para calcular offset")
            return None
        
        # Calcular todos los offsets
        offsets = []
        for pdf_page, printed_page in mappings.items():
            offset = pdf_page - printed_page
            offsets.append(offset)
        
        # Encontrar el offset más común
        offset_counts = Counter(offsets)
        most_common_offset, count = offset_counts.most_common(1)[0]
        
        # Verificar consistencia (al menos 70% de las muestras)
        consistency_ratio = count / len(offsets)
        
        if consistency_ratio < 0.7:
            logger.warning(
                f"Offset inconsistente: {consistency_ratio:.1%} de consistencia"
            )
            return None
        
        logger.info(
            f"Offset más común: {most_common_offset} "
            f"({consistency_ratio:.1%} de consistencia)"
        )
        
        return most_common_offset
    
    def validate_mapping(
        self,
        entries: List[NoteEntry],
        pages_text: Dict[int, str]
    ) -> Dict[str, any]:
        """
        Valida el mapeo de páginas.
        
        Args:
            entries: Lista de entradas mapeadas
            pages_text: Diccionario {page_number: text}
            
        Returns:
            Diccionario con estadísticas de validación
        """
        stats = {
            "total_entries": len(entries),
            "with_pdf_page": 0,
            "valid_mappings": 0,
            "out_of_range": 0
        }
        
        max_pdf_page = max(pages_text.keys()) if pages_text else 0
        
        for entry in entries:
            if entry.pagina_pdf is not None:
                stats["with_pdf_page"] += 1
                
                if 1 <= entry.pagina_pdf <= max_pdf_page:
                    stats["valid_mappings"] += 1
                else:
                    stats["out_of_range"] += 1
        
        if stats["with_pdf_page"] > 0:
            stats["success_rate"] = stats["valid_mappings"] / stats["with_pdf_page"]
        else:
            stats["success_rate"] = 0.0
        
        return stats
