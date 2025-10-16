#!/bin/bash
# run benchmarks

set -e

echo "Running benchmarks..."
pytest benchmarks/ \
    --benchmark-only \
    --benchmark-verbose \
    --benchmark-json=.benchmarks/results.json

echo ""
echo "Benchmark results saved to .benchmarks/results.json"
