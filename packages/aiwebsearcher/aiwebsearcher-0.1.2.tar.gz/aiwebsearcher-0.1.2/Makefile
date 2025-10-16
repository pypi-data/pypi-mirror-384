.PHONY: help install install-dev clean test lint format check run examples

# Default target
help:
	@echo "Search MCP Server - Available Commands:"
	@echo ""
	@echo "  make install          Install production dependencies"
	@echo "  make install-dev      Install development dependencies"
	@echo "  make clean            Remove build artifacts and caches"
	@echo "  make test             Run tests"
	@echo "  make test-cov         Run tests with coverage"
	@echo "  make lint             Run linters (ruff, pylint)"
	@echo "  make format           Format code (black, isort)"
	@echo "  make check            Run all checks (format, lint, type)"
	@echo "  make typecheck        Run type checking (mypy)"
	@echo "  make run              Run MCP server"
	@echo "  make examples         Run example scripts"
	@echo "  make build            Build distribution packages"
	@echo "  make docs             Build documentation"
	@echo "  make publish-test     Publish to TestPyPI"
	@echo "  make publish          Publish to PyPI"
	@echo ""

# Installation
install:
	@echo "📦 Installing production dependencies..."
	uv pip install -e .

install-dev:
	@echo "📦 Installing development dependencies..."
	uv pip install -e ".[dev]"
	uv pip install -r requirements-dev.txt

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -name ".DS_Store" -delete
	@rm -rf build/ dist/ *.egg-info .eggs/
	@rm -rf .pytest_cache/ .coverage htmlcov/ .tox/
	@rm -rf .mypy_cache/ .pytype/ .ruff_cache/
	@echo "✅ Cleanup complete!"

# Testing
test:
	@echo "🧪 Running tests..."
	pytest

test-cov:
	@echo "🧪 Running tests with coverage..."
	pytest --cov=searcher --cov-report=html --cov-report=term

# Code quality
lint:
	@echo "🔍 Running linters..."
	ruff check searcher/
	pylint searcher/

format:
	@echo "🎨 Formatting code..."
	black searcher/ examples/ tests/
	isort searcher/ examples/ tests/

typecheck:
	@echo "🔎 Type checking..."
	mypy searcher/

check: format lint typecheck test
	@echo "✅ All checks passed!"

# Running
run:
	@echo "🚀 Starting MCP server..."
	cd searcher/src && python server.py

# Examples
examples:
	@echo "📚 Running examples..."
	@echo "\n=== Basic Search ==="
	python examples/basic_search.py
	@echo "\n=== Content Extraction ==="
	python examples/content_extraction.py

# Building
build:
	@echo "📦 Building distribution packages..."
	uv build
	@echo "✅ Build complete! Check dist/ directory"

# Documentation
docs:
	@echo "📚 Building documentation..."
	mkdocs build
	@echo "✅ Documentation built! Check site/ directory"

docs-serve:
	@echo "📚 Serving documentation..."
	mkdocs serve

# Publishing
publish-test:
	@echo "📤 Publishing to TestPyPI..."
	uv publish --repository testpypi

publish:
	@echo "📤 Publishing to PyPI..."
	@echo "⚠️  This will publish to production PyPI!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		uv publish; \
		echo "✅ Published to PyPI!"; \
	else \
		echo "❌ Cancelled."; \
	fi

# Git helpers
tag:
	@echo "🏷️  Creating version tag..."
	@read -p "Enter version (e.g., v0.1.0): " version; \
	git tag -a $$version -m "Release $$version"; \
	git push origin $$version; \
	echo "✅ Tag $$version created and pushed!"

# Development helpers
dev-setup: install-dev
	@echo "⚙️  Setting up development environment..."
	@cp .env.example .env
	@echo "✅ Development environment ready!"
	@echo "📝 Don't forget to edit .env with your API keys!"

# Project info
info:
	@echo "📊 Project Information"
	@echo "====================="
	@echo "Python version: $$(python --version)"
	@echo "Package version: $$(grep 'version =' pyproject.toml | cut -d'"' -f2)"
	@echo "Dependencies:"
	@uv pip list | grep -E "(fastmcp|agno|requests|baidusearch)" || pip list | grep -E "(fastmcp|agno|requests|baidusearch)"
