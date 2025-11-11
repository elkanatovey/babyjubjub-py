#!/bin/bash
# Publishing script for babyjubjub-py

set -e

echo "Publishing babyjubjub-py"
echo "======================="
echo

# Check if we're on main branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo "Warning: Not on main branch (current: $BRANCH)"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for uncommitted changes
if [[ $(git status --porcelain) ]]; then
    echo "Error: Uncommitted changes detected"
    git status --short
    exit 1
fi

# Run tests
echo "Running tests..."
python test_basic.py
pytest tests/ -v

# Check Rust formatting
echo "Checking Rust formatting..."
cargo fmt -- --check

# Run clippy
echo "Running clippy..."
cargo clippy -- -D warnings

# Build wheels for current platform
echo "Building wheels..."
maturin build --release

# Optionally build for PyPI (requires API token)
read -p "Upload to PyPI? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Publishing to PyPI..."
    maturin publish
else
    echo "Skipping PyPI upload"
    echo "Wheels available in target/wheels/"
fi

echo
echo "Done!"

