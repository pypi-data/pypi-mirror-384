"""
Constantes del sistema - Patrones y configuraciones estáticas.
"""
import re
from typing import List, Pattern

# Palabras clave para detectar encabezados de índice
HEADER_KEYWORDS_ES = [
    r"\bíndice de notas\b",
    r"\bindice de notas\b", 
    r"\bíndice\b",
    r"\bindice\b",
    r"\bnotas a los estados financieros\b",
    r"\bnotas explicativas\b",
    r"\btabla de contenido\b",
    r"\bcontenido\b",
]

HEADER_KEYWORDS_EN = [
    r"\bnotes index\b",
    r"\bindex of notes\b",
    r"\bnotes to financial statements\b",
    r"\bexplanatory notes\b",
    r"\btable of contents\b",
]


class Patterns:
    """Patrones regex centralizados."""
    
    # Detección de encabezados
    HEADER_ES: Pattern = re.compile(
        "|".join(HEADER_KEYWORDS_ES), 
        re.IGNORECASE
    )
    HEADER_EN: Pattern = re.compile(
        "|".join(HEADER_KEYWORDS_EN), 
        re.IGNORECASE
    )
    
    # Línea de nota simple
    NOTE_LINE: Pattern = re.compile(
        r'^\s*(?:nota|notas?|note|notes?)\s+'
        r'([0-9]+(?:[.\-][0-9]+[a-z]?)*|[IVXLC]+)'
        r'\s*[:.\-–—]?\s*(.*)$',
        re.IGNORECASE
    )
    
    # Detección de puntos líderes o espacios con página
    DOT_LEADER_PAGE: Pattern = re.compile(
        r'(?:\.{3,}|\s{5,}|\t+)\s*(\d{1,4})\s*$'
    )
    
    # Entrada completa de índice (nota + título + página)
    FULL_ENTRY: Pattern = re.compile(
        r'^\s*(?:nota|notas?|note|notes?)\s+'
        r'([0-9]+(?:[.\-][0-9]+[a-z]?)*|[IVXLC]+)'
        r'\s*[:.\-–—]?\s*'
        r'(.*?)'
        r'\s*(?:\.{3,}|\s{5,}|\t+)\s*'
        r'(\d{1,4})\s*$',
        re.IGNORECASE | re.MULTILINE
    )
    
    # Subnota (1.1, 1.2, etc.)
    SUBNOTE: Pattern = re.compile(
        r'^(\d+)\.(\d+[a-z]?)$',
        re.IGNORECASE
    )
    
    # Número romano
    ROMAN: Pattern = re.compile(
        r'^[IVXLC]+$',
        re.IGNORECASE
    )
    
    # Página en pie de página
    FOOTER_PAGE: Pattern = re.compile(
        r'(?:página|page|pág\.?)\s*(\d+)',
        re.IGNORECASE
    )


# Mapeo de números romanos
ROMAN_VALUES = {
    'I': 1, 'V': 5, 'X': 10, 'L': 50,
    'C': 100, 'D': 500, 'M': 1000
}
