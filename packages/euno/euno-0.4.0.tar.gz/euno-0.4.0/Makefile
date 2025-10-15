# Makefile for common development tasks

.PHONY: help install install-dev test lint format type-check clean build upload-test upload

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package
	pip install -e .

install-dev:  ## Install development dependencies
	pip install -r requirements-dev.txt
	pip install -e .

test:  ## Run tests
	pytest

lint:  ## Run linting
	flake8 euno tests
	mypy euno

format:  ## Format code
	black euno tests

type-check:  ## Run type checking
	mypy euno

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean  ## Build package
	python -m build

upload-test: build  ## Upload to test PyPI
	python -m twine upload --repository testpypi dist/*

upload: build  ## Upload to PyPI
	python -m twine upload dist/*
