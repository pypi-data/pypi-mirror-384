#!/bin/bash
# release checklist - run all checks before release

set -e

echo "================================"
echo "   Release Checklist"
echo "================================"
echo ""

echo "1. Running linters..."
./scripts/lint.sh

echo ""
echo "2. Running type checks..."
./scripts/type_check.sh

echo ""
echo "3. Running tests..."
./scripts/test_all.sh

echo ""
echo "4. Running benchmarks..."
./scripts/benchmark.sh

echo ""
echo "5. Building package..."
python -m build

echo ""
echo "6. Checking package..."
twine check dist/*

echo ""
echo "================================"
echo "   All checks passed!"
echo "================================"
echo ""
echo "Ready to release!"
