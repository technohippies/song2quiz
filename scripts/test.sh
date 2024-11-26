#!/bin/bash
set -e  # Exit on any error

echo "Running tests with coverage..."
pytest --cov=src --cov-report=term-missing

echo "Running type checking..."
pyright src tests

echo "All tests passed!" 