#!/bin/bash
set -e  # Exit on any error

echo "Installing test dependencies..."
pip install pytest-asyncio pytest-cov pyright

echo "Running tests with coverage..."
pytest --cov=src --cov-report=term-missing

echo "Running type checking..."
pyright src tests

echo "All tests passed!" 