"""
Motor de heurísticas para detección de índices.
"""
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass

from ..models.index_page import IndexPage
from ..config import ExtractorConfig
from ..utils.logger import get_logger
from .patterns import PatternMatcher

logger = get_logger(__name__)


@dataclass
class PageAnalysis:
    """Análisis de una página."""
    page_number: int
    lines: List[str]
    note_lines: int = 0
    dot_leader_lines: int = 0
    has_header: bool = False
    unique_notes: Set[str] = None
    score: float = 0.0
    
    def __post_init__(self):
        if self.unique_notes is None:
            self.unique_notes = set()


class IndexDetector:
    """Detector de páginas de índice usando heurísticas."""
    
    # Pesos para el sistema de scoring
    WEIGHT_NOTE_LINES = 3.0
    WEIGHT_DOT_LEADERS = 2.0
    WEIGHT_HEADER = 3.0
    WEIGHT_UNIQUE_NOTES = 1.0
    WEIGHT_CONSECUTIVENESS = 0.5
    WEIGHT_DENSITY = 1.5
    
    def __init__(self, config: ExtractorConfig):
        """
        Inicializa el detector.
        
        Args:
            config: Configuración del sistema
        """
        self.config = config
        self.pattern_matcher = PatternMatcher(config.language)
    
    def detect_index_pages(
        self,
        pages_text: Dict[int, str]
    ) -> List[IndexPage]:
        """
        Detecta páginas de índice en un conjunto de páginas.
        
        Args:
            pages_text: Diccionario {page_number: text}
            
        Returns:
            Lista de páginas detectadas como índice
        """
        logger.info(f"Analizando {len(pages_text)} páginas...")
        
        # Analizar cada página
        analyses = []
        for page_num, text in pages_text.items():
            analysis = self._analyze_page(page_num, text)
            analyses.append(analysis)
        
        # Calcular scores
        scored_pages = []
        for analysis in analyses:
            score = self._calculate_score(analysis)
            analysis.score = score
            
            if score >= self.config.min_score_threshold:
                index_page = self._create_index_page(analysis)
                scored_pages.append(index_page)
        
        # Ordenar por score
        scored_pages.sort(key=lambda p: p.score, reverse=True)
        
        logger.info(
            f"Detectadas {len(scored_pages)} páginas candidatas "
            f"(umbral: {self.config.min_score_threshold})"
        )
        
        # Expandir a bloques consecutivos si es necesario
        if scored_pages:
            scored_pages = self._expand_consecutive_pages(scored_pages, analyses)
        
        return scored_pages
    
    def _analyze_page(self, page_number: int, text: str) -> PageAnalysis:
        """
        Analiza una página individual.
        
        Args:
            page_number: Número de página
            text: Texto de la página
            
        Returns:
            PageAnalysis con resultados
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        analysis = PageAnalysis(
            page_number=page_number,
            lines=lines,
            unique_notes=set()
        )
        
        # Detectar header
        full_text = ' '.join(lines[:5])  # Revisar primeras 5 líneas
        analysis.has_header = self.pattern_matcher.match_header(full_text)
        
        # Analizar cada línea
        for line in lines:
            # Línea de nota
            match = self.pattern_matcher.match_note_line(line)
            if match.matched:
                analysis.note_lines += 1
                if match.nota_id:
                    analysis.unique_notes.add(match.nota_id)
            
            # Puntos líderes
            if self.pattern_matcher.has_dot_leaders(line):
                analysis.dot_leader_lines += 1
        
        return analysis
    
    def _calculate_score(self, analysis: PageAnalysis) -> float:
        """
        Calcula el score de una página basado en heurísticas.
        
        Args:
            analysis: Análisis de la página
            
        Returns:
            Score calculado
        """
        score = 0.0
        
        # Líneas de nota
        score += analysis.note_lines * self.WEIGHT_NOTE_LINES
        
        # Puntos líderes
        score += analysis.dot_leader_lines * self.WEIGHT_DOT_LEADERS
        
        # Header presente
        if analysis.has_header:
            score += self.WEIGHT_HEADER
        
        # Notas únicas
        score += len(analysis.unique_notes) * self.WEIGHT_UNIQUE_NOTES
        
        # Bonus por consecutividad
        if self._has_consecutive_notes(analysis.unique_notes):
            score += self.WEIGHT_CONSECUTIVENESS * len(analysis.unique_notes)
        
        # Densidad de notas
        if analysis.lines:
            density = analysis.note_lines / len(analysis.lines)
            score += density * self.WEIGHT_DENSITY
        
        return score
    
    def _has_consecutive_notes(self, note_ids: Set[str]) -> bool:
        """
        Verifica si las notas son consecutivas (1, 2, 3...).
        
        Args:
            note_ids: Conjunto de IDs de notas
            
        Returns:
            True si son consecutivas
        """
        if len(note_ids) < 3:
            return False
        
        # Intentar convertir a números
        numbers = []
        for note_id in note_ids:
            try:
                # Manejar subnotas (tomar solo el primer número)
                main_id = note_id.split('.')[0].split('-')[0]
                numbers.append(int(main_id))
            except ValueError:
                continue
        
        if len(numbers) < 3:
            return False
        
        numbers.sort()
        
        # Verificar consecutividad
        consecutive_count = 1
        for i in range(1, len(numbers)):
            if numbers[i] == numbers[i-1] + 1:
                consecutive_count += 1
                if consecutive_count >= 3:
                    return True
            else:
                consecutive_count = 1
        
        return False
    
    def _create_index_page(self, analysis: PageAnalysis) -> IndexPage:
        """
        Crea un IndexPage desde un PageAnalysis.
        
        Args:
            analysis: Análisis de la página
            
        Returns:
            IndexPage
        """
        # Calcular confianza normalizada
        max_expected_score = 30.0  # Score máximo esperado
        confidence = min(analysis.score / max_expected_score, 1.0)
        
        return IndexPage(
            page_number=analysis.page_number,
            score=analysis.score,
            note_count=analysis.note_lines,
            has_header=analysis.has_header,
            dot_leaders_count=analysis.dot_leader_lines,
            confidence=confidence,
            unique_notes=list(analysis.unique_notes),
            metadata={
                "total_lines": len(analysis.lines),
                "density": analysis.note_lines / len(analysis.lines) if analysis.lines else 0
            }
        )
    
    def _expand_consecutive_pages(
        self,
        candidate_pages: List[IndexPage],
        all_analyses: List[PageAnalysis]
    ) -> List[IndexPage]:
        """
        Expande las páginas detectadas a bloques consecutivos si aplica.
        
        Args:
            candidate_pages: Páginas candidatas detectadas
            all_analyses: Análisis de todas las páginas
            
        Returns:
            Lista expandida de páginas
        """
        if not candidate_pages:
            return []
        
        # Ordenar por número de página
        candidate_pages.sort(key=lambda p: p.page_number)
        
        # Encontrar páginas adyacentes que también parezcan índices
        expanded = list(candidate_pages)
        threshold = self.config.min_score_threshold * self.config.expansion_threshold_ratio
        
        for candidate in candidate_pages:
            # Revisar página siguiente
            next_page_num = candidate.page_number + 1
            next_analysis = next(
                (a for a in all_analyses if a.page_number == next_page_num),
                None
            )
            
            if next_analysis and next_analysis.score >= threshold:
                # Verificar si ya está en la lista
                if not any(p.page_number == next_page_num for p in expanded):
                    expanded.append(self._create_index_page(next_analysis))
        
        # Ordenar y retornar
        expanded.sort(key=lambda p: p.page_number)
        
        return expanded
