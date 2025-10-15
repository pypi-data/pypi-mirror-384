.PHONY: help install install-dev test test-cov lint format clean build

help:
	@echo "Available commands:"
	@echo "  install      - Install package dependencies"
	@echo "  install-dev  - Install package with development dependencies"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  lint         - Run linters"
	@echo "  format       - Format code"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build package"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

test:
	pytest

test-cov:
	pytest --cov=polyspark --cov-report=html --cov-report=term

lint:
	ruff check polyspark tests examples
	mypy polyspark

format:
	black polyspark tests examples
	ruff check --fix polyspark tests examples

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

build: clean
	python -m build

