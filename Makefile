# Makefile for CodeTruth

.PHONY: help install dev-install test test-cov lint format clean build serve docs

help: ## Show this help message
	@echo 'CodeTruth - AI Code Trust & Verification Platform'
	@echo ''
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

dev-install: ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

test: ## Run unit tests
	python -m pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage
	python -m pytest tests/ -v --tb=short --cov=codetruth --cov-report=term --cov-report=html

lint: ## Run linters
	ruff check codetruth/ tests/
	mypy codetruth/ --ignore-missing-imports

format: ## Format code
	black codetruth/ tests/
	ruff check --fix codetruth/ tests/

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

build: ## Build distribution packages
	python -m build

serve: ## Start API server
	python -m codetruth.cli serve --reload

docs: ## Generate API documentation
	@echo "Documentation available at:"
	@echo "  README.md          - English"
	@echo "  README_CN.md       - Chinese"
	@echo "  ARCHITECTURE.md    - Architecture"
	@echo "  docs/              - Detailed docs"