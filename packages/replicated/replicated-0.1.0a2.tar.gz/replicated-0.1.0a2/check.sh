#!/bin/bash

set -e

echo "🔍 Running all CI checks locally..."
echo "=================================="

echo "📦 Installing dependencies..."
python3 -m pip install -e ".[dev]" > /dev/null 2>&1
echo "✅ Dependencies installed"

echo ""
echo "🧪 Running tests..."
python3 -m pytest
echo "✅ Tests passed"

echo ""
echo "🔍 Running linting..."
python3 -m flake8 replicated tests examples
python3 -m mypy replicated
echo "✅ Linting passed"

echo ""
echo "🎨 Checking formatting..."
python3 -m black --check replicated tests examples
python3 -m isort --check-only replicated tests examples
echo "✅ Formatting passed"

echo ""
echo "🎉 ALL CI CHECKS PASSED! Ready to push! 🎉"