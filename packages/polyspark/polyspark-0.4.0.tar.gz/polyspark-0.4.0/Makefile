.PHONY: help install install-dev install-hooks test test-fast test-cov test-integration lint format clean build release

help:
	@echo "Available commands:"
	@echo "  install         - Install package dependencies"
	@echo "  install-dev     - Install package with development dependencies"
	@echo "  install-hooks   - Install pre-commit hooks"
	@echo "  test            - Run all tests"
	@echo "  test-fast       - Run fast tests only (skip slow tests)"
	@echo "  test-cov        - Run tests with coverage report"
	@echo "  test-integration - Run integration tests only"
	@echo "  lint            - Run linters"
	@echo "  format          - Format code"
	@echo "  clean           - Clean build artifacts"
	@echo "  build           - Build package"
	@echo "  release         - Build and check package for release"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

install-hooks:
	pip install pre-commit
	pre-commit install
	@echo "Pre-commit hooks installed successfully!"

test:
	pytest

test-fast:
	pytest -x --tb=short -m "not slow"

test-cov:
	pytest --cov=polyspark --cov-report=html --cov-report=term --cov-report=xml --cov-fail-under=65

test-integration:
	pytest tests/test_integration.py -v

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
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

build: clean
	python -m build

release: clean lint test-cov
	python -m build
	twine check dist/*
	@echo "Package is ready for release!"
	@echo "To upload to PyPI, run: twine upload dist/*"

