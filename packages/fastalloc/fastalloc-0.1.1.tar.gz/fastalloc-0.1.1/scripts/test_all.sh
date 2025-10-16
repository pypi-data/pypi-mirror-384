#!/bin/bash
# run all tests with coverage

set -e

echo "Running all tests..."
pytest tests/ \
    --cov=fastalloc \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml \
    -v

echo ""
echo "Coverage report generated in htmlcov/"
