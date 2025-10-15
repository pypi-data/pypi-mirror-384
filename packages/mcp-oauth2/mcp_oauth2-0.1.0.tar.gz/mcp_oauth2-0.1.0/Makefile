.PHONY: help dev test lint format type-check clean install build check

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev: ## Install development dependencies
	uv sync --dev

install: ## Install package dependencies
	uv sync

test: ## Run tests with coverage
	uv run pytest

test-unit: ## Run unit tests only
	uv run pytest tests/unit

test-integration: ## Run integration tests only
	uv run pytest tests/integration

lint: ## Run linting checks
	uv run ruff check .

format: ## Format code
	uv run ruff format .

type-check: ## Run type checking
	uv run mypy mcp_oauth2

check: lint type-check test ## Run all checks (lint, type-check, test)

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## Build package
	uv build

build-wheel: ## Build wheel distribution
	uv build --wheel

build-sdist: ## Build source distribution
	uv build --sdist

# Development workflow commands
dev-install: ## Install in development mode
	uv pip install -e .

dev-test: ## Run tests in development mode
	uv run pytest -v

dev-lint: ## Run linting in development mode
	uv run ruff check . --fix

dev-format: ## Format code in development mode
	uv run ruff format . --check

# CI/CD commands
ci-install: ## Install dependencies for CI
	uv sync --dev

ci-test: ## Run tests for CI (with coverage)
	uv run pytest --cov=mcp_oauth2 --cov-report=xml

ci-lint: ## Run linting for CI
	uv run ruff check . --output-format=json

ci-type-check: ## Run type checking for CI
	uv run mypy mcp_oauth2 --junit-xml=typecheck-results.xml

# Performance testing
benchmark: ## Run performance benchmarks
	uv run pytest tests/performance -v

# Documentation
docs: ## Generate documentation
	@echo "Documentation generation not yet implemented"

# Security
security-check: ## Run security checks
	@echo "Security checks not yet implemented"

# Release
release-check: check build ## Run all checks before release
	@echo "All checks passed. Ready for release."

release: release-check ## Create release
	@echo "Release process not yet implemented"
