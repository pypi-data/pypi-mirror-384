"""
Exportador a formato Excel.
"""
from pathlib import Path
from typing import List

import pandas as pd

from .base import Exporter
from ..models.extraction_result import ExtractionResult
from ..models.note_entry import NoteEntry
from ..models.index_page import IndexPage
from ..exceptions import ExportError
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ExcelExporter(Exporter):
    """Exporta resultados a formato Excel (.xlsx)."""
    
    def export(
        self,
        result: ExtractionResult,
        output_path: Path
    ) -> None:
        """
        Exporta a Excel con dos hojas: notas_paginas e index_pages.
        
        Args:
            result: Resultado de la extracción
            output_path: Path del archivo de salida
        """
        logger.info(f"Exportando a Excel: {output_path}")
        
        try:
            # Crear archivo Excel con múltiples hojas
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                # Hoja 1: Notas y páginas
                self._export_notes_sheet(result.notes, writer)
                
                # Hoja 2: Páginas de índice
                self._export_index_pages_sheet(result.index_pages, writer)
                
                # Hoja 3: Resumen
                self._export_summary_sheet(result, writer)
                
                # Aplicar formato
                self._apply_formatting(writer)
            
            logger.info(f"Exportación completada: {output_path}")
        
        except Exception as e:
            raise ExportError(f"Error al exportar a Excel: {e}") from e
    
    def _export_notes_sheet(
        self,
        notes: List[NoteEntry],
        writer: pd.ExcelWriter
    ) -> None:
        """Exporta la hoja de notas."""
        if not notes:
            # Crear hoja vacía
            df = pd.DataFrame(columns=[
                "nota_id", "titulo", "pagina_impresa",
                "pagina_pdf", "pagina_fuente", "confianza"
            ])
        else:
            # Convertir a DataFrame
            data = []
            for note in notes:
                data.append({
                    "nota_id": note.nota_id,
                    "titulo": note.titulo,
                    "pagina_impresa": note.pagina_impresa if note.pagina_impresa > 0 else "",
                    "pagina_pdf": note.pagina_pdf if note.pagina_pdf else "",
                    "pagina_fuente": note.pagina_fuente,
                    "confianza": round(note.confianza, 2)
                })
            
            df = pd.DataFrame(data)
        
        df.to_excel(writer, sheet_name="notas_paginas", index=False)
        
        logger.debug(f"Exportadas {len(notes)} notas")
    
    def _export_index_pages_sheet(
        self,
        index_pages: List[IndexPage],
        writer: pd.ExcelWriter
    ) -> None:
        """Exporta la hoja de páginas de índice."""
        if not index_pages:
            df = pd.DataFrame(columns=[
                "page_number", "score", "note_count",
                "unique_notes", "has_header", "dot_leaders", "confidence"
            ])
        else:
            data = []
            for page in index_pages:
                data.append({
                    "page_number": page.page_number,
                    "score": round(page.score, 2),
                    "note_count": page.note_count,
                    "unique_notes": len(page.unique_notes),
                    "has_header": "Sí" if page.has_header else "No",
                    "dot_leaders": page.dot_leaders_count,
                    "confidence": round(page.confidence, 2)
                })
            
            df = pd.DataFrame(data)
        
        df.to_excel(writer, sheet_name="index_pages", index=False)
        
        logger.debug(f"Exportadas {len(index_pages)} páginas de índice")
    
    def _export_summary_sheet(
        self,
        result: ExtractionResult,
        writer: pd.ExcelWriter
    ) -> None:
        """Exporta la hoja de resumen."""
        summary_data = {
            "Métrica": [
                "Archivo PDF",
                "Notas encontradas",
                "Páginas de índice",
                "Confianza promedio",
                "Tiempo de procesamiento (s)",
                "Fecha de extracción"
            ],
            "Valor": [
                result.pdf_path.name,
                result.notes_count,
                result.index_pages_count,
                f"{result.average_confidence:.2%}",
                f"{result.processing_time:.2f}",
                result.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            ]
        }
        
        df = pd.DataFrame(summary_data)
        df.to_excel(writer, sheet_name="resumen", index=False)
        
        logger.debug("Exportado resumen")
    
    def _apply_formatting(self, writer: pd.ExcelWriter) -> None:
        """Aplica formato al Excel."""
        workbook = writer.book
        
        # Formato para encabezados
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        # Formato para confianza alta (>0.8)
        high_conf_format = workbook.add_format({
            'bg_color': '#C6EFCE',
            'font_color': '#006100'
        })
        
        # Formato para confianza media (0.6-0.8)
        med_conf_format = workbook.add_format({
            'bg_color': '#FFEB9C',
            'font_color': '#9C6500'
        })
        
        # Formato para confianza baja (<0.6)
        low_conf_format = workbook.add_format({
            'bg_color': '#FFC7CE',
            'font_color': '#9C0006'
        })
        
        # Aplicar formato a hojas
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            
            # Ajustar anchos de columna
            worksheet.set_column('A:A', 12)  # nota_id
            worksheet.set_column('B:B', 50)  # titulo
            worksheet.set_column('C:F', 15)  # páginas y confianza
            
            # Congelar primera fila
            worksheet.freeze_panes(1, 0)
