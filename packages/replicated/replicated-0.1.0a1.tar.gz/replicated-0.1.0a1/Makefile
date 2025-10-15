.PHONY: install dev test lint format clean build upload ci

# Install package
install:
	pip install -e .

# Install development dependencies
dev:
	pip install -e .[dev]

# Run tests
test:
	pytest

# Run linting
lint:
	flake8 replicated tests examples
	mypy replicated

# Format code
format:
	black replicated tests examples
	isort replicated tests examples

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build package
build: clean
	python -m build

# Upload to PyPI (requires twine)
upload: build
	twine check dist/*
	twine upload dist/*

# Run all checks (CI simulation - no formatting, just checking)
ci:
	@echo "🔍 Running all CI checks locally..."
	@echo "📦 Installing dependencies..."
	@python3 -m pip install -e .[dev] > /dev/null 2>&1
	@echo "✅ Dependencies installed"
	@echo "🧪 Running tests..."
	@python3 -m pytest
	@echo "✅ Tests passed"
	@echo "🔍 Running linting..."
	@python3 -m flake8 replicated tests examples
	@python3 -m mypy replicated
	@echo "✅ Linting passed"
	@echo "🎨 Checking formatting..."
	@python3 -m black --check replicated tests examples
	@python3 -m isort --check-only replicated tests examples
	@echo "✅ Formatting passed"
	@echo "🎉 ALL CI CHECKS PASSED! Ready to push! 🎉"

# Run all checks (formats code first)
check: format lint test
	@echo "All checks passed!"