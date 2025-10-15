"""
Sistema de detección de patrones con regex.
"""
import re
from typing import Optional, Tuple, List
from dataclasses import dataclass

from ..constants import Patterns
from ..utils.text_utils import clean_text


@dataclass
class PatternMatch:
    """Resultado de un match de patrón."""
    matched: bool
    nota_id: Optional[str] = None
    titulo: Optional[str] = None
    pagina: Optional[int] = None
    confidence: float = 0.0


class PatternMatcher:
    """Motor de matching de patrones regex para índices de notas."""
    
    def __init__(self, language: str = "es"):
        """
        Inicializa el matcher de patrones.
        
        Args:
            language: Idioma para patrones ('es' o 'en')
        """
        self.language = language
        self.header_pattern = Patterns.HEADER_ES if language == "es" else Patterns.HEADER_EN
    
    def match_header(self, text: str) -> bool:
        """
        Detecta si el texto contiene un encabezado de índice.
        
        Args:
            text: Texto a analizar
            
        Returns:
            True si se detecta encabezado
        """
        text = clean_text(text).lower()
        return bool(self.header_pattern.search(text))
    
    def match_note_line(self, line: str) -> PatternMatch:
        """
        Intenta hacer match de una línea como entrada de nota simple.
        
        Args:
            line: Línea de texto
            
        Returns:
            PatternMatch con resultado
        """
        line = clean_text(line)
        
        match = Patterns.NOTE_LINE.match(line)
        if not match:
            return PatternMatch(matched=False)
        
        nota_id = match.group(1)
        titulo = match.group(2).strip() if len(match.groups()) > 1 else ""
        
        return PatternMatch(
            matched=True,
            nota_id=nota_id,
            titulo=titulo,
            confidence=0.7  # Match básico
        )
    
    def match_full_entry(self, line: str) -> PatternMatch:
        """
        Intenta hacer match de una entrada completa (nota + título + página).
        
        Args:
            line: Línea de texto
            
        Returns:
            PatternMatch con resultado completo
        """
        line = clean_text(line)
        
        match = Patterns.FULL_ENTRY.match(line)
        if not match:
            return PatternMatch(matched=False)
        
        nota_id = match.group(1)
        titulo = match.group(2).strip()
        
        try:
            pagina = int(match.group(3))
            
            # Validar rango razonable
            if not 1 <= pagina <= 9999:
                return PatternMatch(matched=False)
            
            return PatternMatch(
                matched=True,
                nota_id=nota_id,
                titulo=titulo,
                pagina=pagina,
                confidence=1.0  # Match completo
            )
        except (ValueError, IndexError):
            return PatternMatch(matched=False)
    
    def extract_page_from_line(self, line: str) -> Optional[int]:
        """
        Extrae un número de página de una línea.
        
        Args:
            line: Línea de texto
            
        Returns:
            Número de página o None
        """
        match = Patterns.DOT_LEADER_PAGE.search(line)
        if match:
            try:
                page = int(match.group(1))
                if 1 <= page <= 9999:
                    return page
            except (ValueError, IndexError):
                pass
        
        return None
    
    def has_dot_leaders(self, line: str) -> bool:
        """
        Detecta si una línea tiene puntos líderes.
        
        Args:
            line: Línea de texto
            
        Returns:
            True si tiene puntos líderes
        """
        return bool(Patterns.DOT_LEADER_PAGE.search(line))
    
    def is_subnote(self, nota_id: str) -> bool:
        """
        Determina si un ID de nota es una subnota.
        
        Args:
            nota_id: ID de nota
            
        Returns:
            True si es subnota
        """
        return bool(Patterns.SUBNOTE.match(nota_id))
    
    def is_roman(self, nota_id: str) -> bool:
        """
        Determina si un ID usa numeración romana.
        
        Args:
            nota_id: ID de nota
            
        Returns:
            True si es romano
        """
        return bool(Patterns.ROMAN.match(nota_id.strip()))
    
    def match_footer_page(self, text: str) -> Optional[int]:
        """
        Extrae número de página de un pie de página.
        
        Args:
            text: Texto del pie de página
            
        Returns:
            Número de página o None
        """
        match = Patterns.FOOTER_PAGE.search(text.lower())
        if match:
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                pass
        
        return None
