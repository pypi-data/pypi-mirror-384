#!/bin/bash
# Test script to verify package builds correctly before release

set -e  # Exit on error

echo "================================"
echo "QUTEN Package Build Test"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Clean previous builds
echo "📦 Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/
echo -e "${GREEN}✓ Cleaned${NC}"
echo ""

# 2. Install build tools
echo "🔧 Installing build tools..."
pip install -q build twine
echo -e "${GREEN}✓ Build tools installed${NC}"
echo ""

# 3. Build package
echo "🏗️  Building package..."
python -m build
echo -e "${GREEN}✓ Package built${NC}"
echo ""

# 4. List built files
echo "📋 Built files:"
ls -lh dist/
echo ""

# 5. Check package
echo "✅ Running package checks..."
twine check dist/*
echo -e "${GREEN}✓ Package checks passed${NC}"
echo ""

# 6. Test installation in virtual environment
echo "🧪 Testing installation..."
python -m venv test_env
source test_env/bin/activate
pip install -q dist/*.whl

# 7. Test import
echo "📥 Testing import..."
python -c "
from quten import QUTEN
import torch

print('  ✓ QUTEN imported successfully')

# Test basic functionality
model = torch.nn.Linear(10, 1)
optimizer = QUTEN(model.parameters(), lr=0.001)
print('  ✓ Optimizer created successfully')

# Test one step
x = torch.randn(5, 10)
y = torch.randn(5, 1)
loss = ((model(x) - y) ** 2).mean()
optimizer.zero_grad()
loss.backward()
optimizer.step()
print('  ✓ Optimizer step successful')
"

deactivate
rm -rf test_env

echo -e "${GREEN}✓ Installation test passed${NC}"
echo ""

# 8. Check version
echo "🔢 Checking version..."
VERSION=$(python -c "import setup; print(setup.__version__)")
echo "  Package version: $VERSION"
echo ""

# 9. Summary
echo "================================"
echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
echo "================================"
echo ""
echo "Ready to publish!"
echo ""
echo "Next steps:"
echo "  1. Test on TestPyPI:"
echo "     gh workflow run publish.yml --field test_pypi=true"
echo ""
echo "  2. Create release:"
echo "     git tag -a v$VERSION -m 'Release v$VERSION'"
echo "     git push origin v$VERSION"
echo "     gh release create v$VERSION"
echo ""
