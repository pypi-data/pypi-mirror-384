#!/bin/bash
# run tests with detailed coverage

set -e

echo "Running tests with coverage..."
pytest tests/ \
    --cov=fastalloc \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-fail-under=95

echo ""
echo "Coverage report: htmlcov/index.html"
