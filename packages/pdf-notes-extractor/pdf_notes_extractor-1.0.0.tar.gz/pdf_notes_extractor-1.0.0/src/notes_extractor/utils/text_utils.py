"""
Utilidades para procesamiento de texto.
"""
import re
from typing import Optional

from ..constants import ROMAN_VALUES, Patterns


def clean_text(text: str) -> str:
    """
    Limpia y normaliza texto.
    
    Args:
        text: Texto a limpiar
        
    Returns:
        Texto limpio
    """
    if not text:
        return ""
    
    # Normalizar espacios
    text = re.sub(r'\s+', ' ', text)
    
    # Remover caracteres especiales de control
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # Trim
    text = text.strip()
    
    return text


def roman_to_int(roman: str) -> Optional[int]:
    """
    Convierte un número romano a entero.
    
    Args:
        roman: Número romano (e.g., 'IV', 'XII')
        
    Returns:
        Entero correspondiente o None si no es válido
    """
    roman = roman.upper().strip()
    
    if not Patterns.ROMAN.match(roman):
        return None
    
    result = 0
    prev_value = 0
    
    for char in reversed(roman):
        value = ROMAN_VALUES.get(char, 0)
        
        if value < prev_value:
            result -= value
        else:
            result += value
        
        prev_value = value
    
    return result if result > 0 else None


def extract_page_number(text: str) -> Optional[int]:
    """
    Extrae un número de página de una línea de texto.
    
    Args:
        text: Texto que contiene un número de página
        
    Returns:
        Número de página o None si no se encuentra
    """
    # Buscar patrón de puntos líderes + número
    match = Patterns.DOT_LEADER_PAGE.search(text)
    if match:
        try:
            return int(match.group(1))
        except (ValueError, IndexError):
            pass
    
    # Buscar último número en la línea
    numbers = re.findall(r'\d+', text)
    if numbers:
        try:
            page_num = int(numbers[-1])
            # Validar rango razonable
            if 1 <= page_num <= 9999:
                return page_num
        except ValueError:
            pass
    
    return None


def normalize_note_id(note_id: str) -> str:
    """
    Normaliza un ID de nota para comparación.
    
    Args:
        note_id: ID de nota original
        
    Returns:
        ID normalizado
    """
    # Remover espacios
    note_id = note_id.strip()
    
    # Normalizar separadores (convertir - a .)
    note_id = note_id.replace('-', '.')
    
    return note_id


def is_likely_note_line(line: str) -> bool:
    """
    Determina si una línea probablemente contiene una nota.
    
    Args:
        line: Línea de texto
        
    Returns:
        True si parece ser una línea de nota
    """
    line = line.strip().lower()
    
    # Debe comenzar con 'nota' o 'note'
    if not (line.startswith('nota') or line.startswith('note')):
        return False
    
    # Debe tener un número o romano cerca del inicio
    first_part = line[:50]  # Primeros 50 caracteres
    
    # Buscar número
    if re.search(r'\d+', first_part):
        return True
    
    # Buscar romano
    if re.search(r'\b[IVXLC]+\b', first_part, re.IGNORECASE):
        return True
    
    return False
