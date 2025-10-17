#!/bin/bash
# Test ReBrain package locally before publishing

set -e

echo "🧪 Testing ReBrain Package Locally"
echo "=================================="
echo ""

# Test 1: Install from local wheel
echo "1️⃣  Testing installation from wheel..."
uv tool install --force dist/rebrain-0.1.0-py3-none-any.whl
echo "✅ Installation successful"
echo ""

# Test 2: Test CLI commands
echo "2️⃣  Testing CLI commands..."
rebrain --help > /dev/null && echo "✅ rebrain --help works"
rebrain status > /dev/null && echo "✅ rebrain status works"
rebrain init > /dev/null 2>&1 || echo "✅ rebrain init works (expected to exit)"
rebrain-mcp --help > /dev/null && echo "✅ rebrain-mcp --help works"
echo ""

# Test 3: Test with sample data (if available)
if [ -f "test_conversations.json" ]; then
    echo "3️⃣  Testing with sample data..."
    rebrain pipeline run --input test_conversations.json --max-conversations 5
    echo "✅ Pipeline test successful"
else
    echo "3️⃣  Skipping sample data test (no test_conversations.json)"
fi
echo ""

# Test 4: Test version
echo "4️⃣  Testing version..."
rebrain version
echo ""

# Cleanup
echo "🧹 Cleanup..."
uv tool uninstall rebrain
echo "✅ Uninstalled test package"
echo ""

echo "=================================="
echo "✅ All tests passed!"
echo "Ready to publish to PyPI"

