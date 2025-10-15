#!/bin/bash
# Build script for humalab package

set -e

echo "Cleaning old builds..."
rm -rf dist/ build/ *.egg-info

echo "Building package..."
python -m build

echo "Build complete! Artifacts in dist/"
ls -lh dist/
