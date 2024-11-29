#!/bin/bash
# scripts/test_ci.sh

# Force output to be unbuffered
exec 1> >(exec cat)
exec 2> >(exec cat >&2)

# Only do venv setup if not skipped
if [ -z "$SKIP_VENV" ]; then
    echo "🧹 Cleaning up old venv..."
    rm -rf .venv

    echo "🏗️ Creating fresh venv..."
    uv venv

    echo "🔌 Activating venv..."
    source .venv/bin/activate

    echo "📦 Installing dependencies..."
    uv pip install -r requirements.txt

    echo "📦 Installing development tools..."
    uv pip install mypy ruff pytest pytest-asyncio pytest-cov
fi

echo "🔍 Running type checks..."
mypy . --ignore-missing-imports --follow-imports=silent

echo "🧪 Running linter..."
ruff check .

echo "✨ Checking formatting..."
ruff format --check .

echo "🧪 Running tests..."
pytest
