#!/bin/bash
# Run all linting and formatting checks

set -e

echo "🔍 Running linting and formatting checks..."
echo ""

# Check if in virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "Consider running: source .venv/bin/activate"
    echo ""
fi

echo "1️⃣  isort (import sorting)..."
isort --check-only --diff rebrain/ scripts/ config/ integrations/ || {
    echo "❌ isort found issues. Run 'isort rebrain/ scripts/ config/ integrations/' to fix"
    exit 1
}

echo "✅ isort passed"
echo ""

echo "2️⃣  black (code formatting)..."
black --check rebrain/ scripts/ config/ integrations/ || {
    echo "❌ black found issues. Run 'black rebrain/ scripts/ config/ integrations/' to fix"
    exit 1
}

echo "✅ black passed"
echo ""

echo "3️⃣  ruff (fast linter)..."
ruff check rebrain/ scripts/ config/ integrations/ || {
    echo "❌ ruff found issues. Run 'ruff check --fix rebrain/ scripts/ config/ integrations/' to fix"
    exit 1
}

echo "✅ ruff passed"
echo ""

echo "4️⃣  pylint (comprehensive linting)..."
pylint rebrain/ scripts/ config/ integrations/ --exit-zero || {
    echo "⚠️  pylint found some issues (non-blocking)"
}

echo ""
echo "✅ All critical checks passed!"

