"""
Normalización y consolidación de datos.
"""
from typing import List, Dict
from collections import defaultdict

from ..models.note_entry import NoteEntry
from ..utils.logger import get_logger
from ..utils.text_utils import roman_to_int, normalize_note_id

logger = get_logger(__name__)


class DataNormalizer:
    """Normaliza y consolida entradas de notas."""
    
    def normalize_and_consolidate(self, entries: List[NoteEntry]) -> List[NoteEntry]:
        """
        Normaliza y consolida entradas, eliminando duplicados.
        
        Args:
            entries: Lista de entradas a normalizar
            
        Returns:
            Lista normalizada y consolidada
        """
        logger.info(f"Normalizando {len(entries)} entradas...")
        
        # Normalizar IDs
        for entry in entries:
            entry.nota_id = normalize_note_id(entry.nota_id)
            entry.titulo = entry.titulo.strip()
        
        # Eliminar duplicados
        consolidated = self._remove_duplicates(entries)
        
        # Ordenar
        sorted_entries = self._sort_entries(consolidated)
        
        logger.info(f"Entradas consolidadas: {len(sorted_entries)}")
        
        return sorted_entries
    
    def _remove_duplicates(self, entries: List[NoteEntry]) -> List[NoteEntry]:
        """
        Elimina entradas duplicadas, priorizando por confianza.
        
        Args:
            entries: Lista de entradas
            
        Returns:
            Lista sin duplicados
        """
        # Agrupar por nota_id
        grouped: Dict[str, List[NoteEntry]] = defaultdict(list)
        for entry in entries:
            grouped[entry.nota_id].append(entry)
        
        # Seleccionar la mejor entrada de cada grupo
        consolidated = []
        for nota_id, group in grouped.items():
            if len(group) == 1:
                consolidated.append(group[0])
            else:
                # Priorizar por confianza, luego por título más largo
                best = max(
                    group,
                    key=lambda e: (e.confianza, len(e.titulo), e.pagina_impresa > 0)
                )
                
                logger.debug(
                    f"Consolidando {len(group)} entradas para nota {nota_id}, "
                    f"seleccionada: confianza={best.confianza:.2f}"
                )
                
                consolidated.append(best)
        
        removed = len(entries) - len(consolidated)
        if removed > 0:
            logger.info(f"Eliminados {removed} duplicados")
        
        return consolidated
    
    def _sort_entries(self, entries: List[NoteEntry]) -> List[NoteEntry]:
        """
        Ordena entradas por nota_id.
        
        Args:
            entries: Lista de entradas
            
        Returns:
            Lista ordenada
        """
        def sort_key(entry: NoteEntry):
            """Genera clave de ordenamiento."""
            nota_id = entry.nota_id
            
            # Intentar convertir a número
            try:
                # Manejar subnotas (1.1 -> (1, 1))
                if '.' in nota_id:
                    parts = nota_id.split('.')
                    return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
                else:
                    return (int(nota_id), 0)
            except ValueError:
                pass
            
            # Intentar romano
            roman_value = roman_to_int(nota_id)
            if roman_value:
                return (roman_value, 0)
            
            # Fallback: ordenar alfabéticamente
            return (float('inf'), nota_id)
        
        try:
            return sorted(entries, key=sort_key)
        except Exception as e:
            logger.warning(f"Error al ordenar entradas: {e}, usando orden original")
            return entries
    
    def validate_sequence(self, entries: List[NoteEntry]) -> Dict[str, any]:
        """
        Valida la secuencia de notas y genera estadísticas.
        
        Args:
            entries: Lista de entradas ordenadas
            
        Returns:
            Diccionario con estadísticas de validación
        """
        stats = {
            "total": len(entries),
            "with_page": sum(1 for e in entries if e.pagina_impresa > 0),
            "without_page": sum(1 for e in entries if e.pagina_impresa == 0),
            "avg_confidence": sum(e.confianza for e in entries) / len(entries) if entries else 0,
            "gaps": [],
            "duplicates_in_sequence": []
        }
        
        # Detectar gaps en la secuencia
        numeric_ids = []
        for entry in entries:
            try:
                main_id = entry.nota_id.split('.')[0]
                numeric_ids.append((int(main_id), entry.nota_id))
            except ValueError:
                continue
        
        if len(numeric_ids) > 1:
            numeric_ids.sort()
            for i in range(1, len(numeric_ids)):
                if numeric_ids[i][0] > numeric_ids[i-1][0] + 1:
                    stats["gaps"].append((numeric_ids[i-1][1], numeric_ids[i][1]))
        
        return stats
