#!/bin/bash
# Auto-format code using isort and black

set -e

echo "🎨 Auto-formatting code..."
echo ""

# Check if in virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "Consider running: source .venv/bin/activate"
    echo ""
fi

echo "1️⃣  isort (sorting imports)..."
isort rebrain/ scripts/ config/ integrations/
echo "✅ isort completed"
echo ""

echo "2️⃣  black (formatting code)..."
black rebrain/ scripts/ config/ integrations/
echo "✅ black completed"
echo ""

echo "3️⃣  ruff (auto-fixing issues)..."
ruff check --fix rebrain/ scripts/ config/ integrations/ || true
echo "✅ ruff completed"
echo ""

echo "✅ All formatting completed!"
echo "💡 Run 'scripts/lint.sh' to verify"

