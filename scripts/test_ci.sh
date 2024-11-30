#!/bin/bash
# scripts/test_ci.sh

set -e  # Exit on error

# Force output to be unbuffered
exec 1> >(exec cat)
exec 2> >(exec cat >&2)

# Only do venv setup if not skipped
if [ -z "$SKIP_VENV" ]; then
    echo "🧹 Cleaning up old venv..."
    # Force remove with sudo if normal remove fails
    if ! rm -rf .venv 2>/dev/null; then
        echo "⚠️  Normal cleanup failed, trying with sudo..."
        sudo rm -rf .venv
    fi

    echo "🏗️ Creating fresh venv..."
    # Ensure python3 is available
    if ! command -v python3 &> /dev/null; then
        echo "❌ python3 not found! Please install Python 3"
        exit 1
    fi

    # Create venv using python3 if uv fails
    if ! uv venv 2>/dev/null; then
        echo "⚠️  uv venv failed, falling back to python3 -m venv..."
        python3 -m venv .venv
    fi

    echo "🔌 Activating venv..."
    source .venv/bin/activate || {
        echo "❌ Failed to activate venv"
        exit 1
    }

    echo "📦 Installing dependencies..."
    if command -v uv &> /dev/null; then
        uv pip install -r requirements.txt
    else
        pip install -r requirements.txt
    fi

    echo "📦 Installing development tools..."
    if command -v uv &> /dev/null; then
        uv pip install mypy ruff pytest pytest-asyncio pytest-cov
    else
        pip install mypy ruff pytest pytest-asyncio pytest-cov
    fi
fi

echo "🔍 Running type checks..."
mypy . --ignore-missing-imports --follow-imports=silent

echo "🧪 Running linter..."
ruff check .

echo "✨ Checking formatting..."
ruff format --check .

echo "🧪 Running tests..."
pytest
