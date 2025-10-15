"""
Entry point para ejecución como módulo.
Permite ejecutar: python -m notes_extractor
"""
from .cli.main import cli

if __name__ == "__main__":
    cli()
