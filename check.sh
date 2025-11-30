#!/bin/bash

# Code Quality Check Script
# Runs all quality checks: formatting, linting, and type checking

set -e  # Exit on first error

echo "========================================="
echo "Running Code Quality Checks"
echo "========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Run this script from the project root."
    exit 1
fi

# Black formatting check
echo "1. Checking code formatting with Black..."
uv run black --check backend/ main.py || {
    echo "❌ Black formatting check failed. Run ./format.sh to fix."
    exit 1
}
echo "✓ Black formatting check passed"
echo ""

# Ruff linting
echo "2. Running Ruff linter..."
uv run ruff check backend/ main.py || {
    echo "❌ Ruff linting failed. Fix the issues above."
    exit 1
}
echo "✓ Ruff linting passed"
echo ""

# MyPy type checking
echo "3. Running MyPy type checker..."
uv run mypy backend/ main.py || {
    echo "❌ MyPy type checking failed. Fix the issues above."
    exit 1
}
echo "✓ MyPy type checking passed"
echo ""

echo "========================================="
echo "✓ All quality checks passed!"
echo "========================================="
