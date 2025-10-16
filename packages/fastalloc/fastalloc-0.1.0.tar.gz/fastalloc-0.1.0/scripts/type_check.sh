#!/bin/bash
# run mypy type checking

set -e

echo "Running mypy type checking..."
mypy src/fastalloc/

echo ""
echo "Type checking passed!"
