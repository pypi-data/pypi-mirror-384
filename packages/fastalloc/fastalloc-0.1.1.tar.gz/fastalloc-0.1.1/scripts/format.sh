#!/bin/bash
# format code with black and isort

set -e

echo "Formatting code..."
echo ""

echo "=== Black ==="
black src/ tests/ examples/ benchmarks/
echo ""

echo "=== isort ==="
isort src/ tests/ examples/ benchmarks/
echo ""

echo "Code formatted!"
