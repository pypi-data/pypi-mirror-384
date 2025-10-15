"""
Utilidades para manejo de archivos.
"""
import re
from pathlib import Path
from typing import Union


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Asegura que un directorio existe, creándolo si es necesario.
    
    Args:
        path: Path del directorio
        
    Returns:
        Path del directorio
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def safe_filename(filename: str, max_length: int = 255) -> str:
    """
    Convierte un string en un nombre de archivo seguro.
    
    Args:
        filename: Nombre de archivo original
        max_length: Longitud máxima del nombre
        
    Returns:
        Nombre de archivo seguro
    """
    # Remover caracteres no seguros
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remover espacios múltiples y al inicio/fin
    safe_name = re.sub(r'\s+', ' ', safe_name).strip()
    
    # Limitar longitud
    if len(safe_name) > max_length:
        name, ext = safe_name.rsplit('.', 1) if '.' in safe_name else (safe_name, '')
        max_name_length = max_length - len(ext) - 1 if ext else max_length
        safe_name = f"{name[:max_name_length]}.{ext}" if ext else name[:max_length]
    
    return safe_name


def get_output_path(
    input_path: Path,
    output_dir: Path,
    suffix: str = "_notas",
    extension: str = ".xlsx"
) -> Path:
    """
    Genera un path de salida basado en el archivo de entrada.
    
    Args:
        input_path: Path del archivo de entrada
        output_dir: Directorio de salida
        suffix: Sufijo a añadir al nombre
        extension: Extensión del archivo de salida
        
    Returns:
        Path del archivo de salida
    """
    ensure_directory(output_dir)
    
    base_name = input_path.stem
    safe_name = safe_filename(f"{base_name}{suffix}{extension}")
    
    return output_dir / safe_name
