.PHONY: install install-dev test test-cov lint format clean help

help:  ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Instala el paquete
	pip install -e .

install-dev:  ## Instala con dependencias de desarrollo
	pip install -e ".[dev,alternative]"

test:  ## Ejecuta los tests
	pytest tests/

test-cov:  ## Ejecuta tests con cobertura
	pytest --cov=src/notes_extractor --cov-report=html --cov-report=term tests/

test-unit:  ## Solo tests unitarios
	pytest tests/unit/

test-integration:  ## Solo tests de integración
	pytest tests/integration/

lint:  ## Ejecuta linters
	flake8 src/ tests/
	mypy src/

format:  ## Formatea el código
	black src/ tests/
	isort src/ tests/

format-check:  ## Verifica formato sin modificar
	black --check src/ tests/
	isort --check-only src/ tests/

clean:  ## Limpia archivos temporales
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ htmlcov/ .coverage

build:  ## Construye el paquete
	python -m build

example-basic:  ## Ejecuta ejemplo básico
	python examples/basic_usage.py

example-advanced:  ## Ejecuta ejemplo avanzado
	python examples/advanced_config.py
