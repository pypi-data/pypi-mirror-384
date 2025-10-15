"""
Parser principal de índices de notas.
"""
from typing import List, Dict
from dataclasses import dataclass

from ..models.note_entry import NoteEntry
from ..models.index_page import IndexPage
from ..config import ExtractorConfig
from ..utils.logger import get_logger
from ..utils.text_utils import clean_text, extract_page_number
from .patterns import PatternMatcher

logger = get_logger(__name__)


class IndexParser:
    """Parser de índices de notas."""
    
    def __init__(self, config: ExtractorConfig):
        """
        Inicializa el parser.
        
        Args:
            config: Configuración del sistema
        """
        self.config = config
        self.pattern_matcher = PatternMatcher(config.language)
    
    def parse_index_pages(
        self,
        index_pages: List[IndexPage],
        pages_text: Dict[int, str]
    ) -> List[NoteEntry]:
        """
        Parsea las páginas de índice para extraer entradas de notas.
        
        Args:
            index_pages: Páginas detectadas como índice
            pages_text: Diccionario {page_number: text}
            
        Returns:
            Lista de entradas de notas extraídas
        """
        logger.info(f"Parseando {len(index_pages)} páginas de índice...")
        
        all_entries = []
        
        for index_page in index_pages:
            page_text = pages_text.get(index_page.page_number, "")
            entries = self._parse_page(index_page.page_number, page_text)
            all_entries.extend(entries)
        
        logger.info(f"Extraídas {len(all_entries)} entradas de notas")
        
        return all_entries
    
    def _parse_page(self, page_number: int, text: str) -> List[NoteEntry]:
        """
        Parsea una página individual.
        
        Args:
            page_number: Número de página
            text: Texto de la página
            
        Returns:
            Lista de entradas encontradas
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        entries = []
        
        for line in lines:
            entry = self._parse_line(line, page_number)
            if entry:
                entries.append(entry)
        
        return entries
    
    def _parse_line(self, line: str, source_page: int) -> NoteEntry:
        """
        Parsea una línea individual.
        
        Args:
            line: Línea de texto
            source_page: Página fuente
            
        Returns:
            NoteEntry si se parsea correctamente, None en caso contrario
        """
        line = clean_text(line)
        
        # Intentar match completo primero
        full_match = self.pattern_matcher.match_full_entry(line)
        if full_match.matched:
            return NoteEntry(
                nota_id=full_match.nota_id,
                titulo=full_match.titulo,
                pagina_impresa=full_match.pagina,
                pagina_fuente=source_page,
                confianza=full_match.confidence,
                metadata={"pattern": "full_entry"}
            )
        
        # Intentar match de línea de nota + extracción de página
        note_match = self.pattern_matcher.match_note_line(line)
        if note_match.matched:
            # Intentar extraer página de la misma línea
            page_num = self.pattern_matcher.extract_page_from_line(line)
            
            if page_num:
                return NoteEntry(
                    nota_id=note_match.nota_id,
                    titulo=note_match.titulo,
                    pagina_impresa=page_num,
                    pagina_fuente=source_page,
                    confianza=0.85,  # Alta confianza
                    metadata={"pattern": "note_line_with_page"}
                )
            else:
                # Nota sin página (confianza menor)
                return NoteEntry(
                    nota_id=note_match.nota_id,
                    titulo=note_match.titulo,
                    pagina_impresa=0,  # Página desconocida
                    pagina_fuente=source_page,
                    confianza=0.5,  # Baja confianza
                    metadata={"pattern": "note_line_no_page"}
                )
        
        return None
    
    def filter_valid_entries(self, entries: List[NoteEntry]) -> List[NoteEntry]:
        """
        Filtra entradas válidas basándose en criterios de calidad.
        
        Args:
            entries: Lista de entradas a filtrar
            
        Returns:
            Lista filtrada
        """
        valid_entries = []
        
        for entry in entries:
            # Filtrar por confianza mínima
            if entry.confianza < self.config.min_confidence:
                logger.debug(
                    f"Descartando entrada {entry.nota_id} por baja confianza: "
                    f"{entry.confianza:.2f}"
                )
                continue
            
            # Filtrar páginas inválidas (si tenemos página)
            if entry.pagina_impresa > 0:
                if not 1 <= entry.pagina_impresa <= 9999:
                    logger.debug(
                        f"Descartando entrada {entry.nota_id} por página inválida: "
                        f"{entry.pagina_impresa}"
                    )
                    continue
            
            valid_entries.append(entry)
        
        logger.info(
            f"Entradas válidas: {len(valid_entries)} de {len(entries)} "
            f"({len(valid_entries)/len(entries)*100:.1f}%)"
        )
        
        return valid_entries
