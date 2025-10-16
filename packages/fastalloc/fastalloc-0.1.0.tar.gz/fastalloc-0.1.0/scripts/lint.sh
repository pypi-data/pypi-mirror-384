#!/bin/bash
# run all linters

set -e

echo "Running linters..."
echo ""

echo "=== Black ==="
black --check src/ tests/ examples/ benchmarks/
echo ""

echo "=== isort ==="
isort --check src/ tests/ examples/ benchmarks/
echo ""

echo "=== flake8 ==="
flake8 src/ tests/ examples/ benchmarks/
echo ""

echo "=== pylint ==="
pylint src/fastalloc/
echo ""

echo "All linters passed!"
