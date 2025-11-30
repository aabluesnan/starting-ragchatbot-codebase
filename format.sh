#!/bin/bash

# Code Formatting Script
# Automatically formats all Python code with Black and fixes import order with Ruff

set -e  # Exit on first error

echo "========================================="
echo "Formatting Code"
echo "========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Run this script from the project root."
    exit 1
fi

# Run Black formatter
echo "1. Formatting with Black..."
uv run black backend/ main.py
echo "✓ Black formatting complete"
echo ""

# Run Ruff auto-fix (fixes import order and simple issues)
echo "2. Fixing imports and simple issues with Ruff..."
uv run ruff check --fix backend/ main.py || true
echo "✓ Ruff auto-fix complete"
echo ""

echo "========================================="
echo "✓ Code formatting complete!"
echo "========================================="
echo ""
echo "Run ./check.sh to verify all quality checks pass."
