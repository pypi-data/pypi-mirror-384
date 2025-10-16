#!/bin/bash

# C2i Athena MCP - Local Build and Test Script

set -e

echo "🔧 Setting up C2i Athena MCP for publishing..."

# Check if we're in the right directory
if [ ! -f "src/c2i_athena_mcp/pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the c2i_alg_mcp_clean directory"
    exit 1
fi

# Install build dependencies
echo "📦 Installing build dependencies..."
python -m pip install --upgrade pip
pip install build twine

# Build the package
echo "🏗️ Building package..."
cd src/c2i_athena_mcp
python -m build

# Check the package
echo "✅ Checking package integrity..."
twine check dist/*

echo "📋 Package files created:"
ls -la dist/

echo ""
echo "🎉 Package built successfully!"
echo ""
echo "📤 Next steps:"
echo "1. Test the package locally:"
echo "   pip install dist/c2i_athena_mcp-1.0.0-py3-none-any.whl"
echo ""
echo "2. Upload to PyPI (you'll need a PyPI token):"
echo "   twine upload dist/*"
echo ""
echo "3. Test installation from PyPI:"
echo "   uvx install c2i-athena-mcp"
echo ""

# Test basic import
echo "🧪 Testing basic import..."
cd ../..
python -c "
import sys
sys.path.insert(0, 'src')
try:
    from c2i_athena_mcp import __version__
    print(f'✅ Package version: {__version__}')
except Exception as e:
    print(f'❌ Import error: {e}')
"

echo ""
echo "🔐 PyPI Setup Instructions:"
echo "1. Create PyPI account: https://pypi.org/account/register/"
echo "2. Generate API token: https://pypi.org/manage/account/token/"
echo "3. Configure twine: echo '[pypi]' > ~/.pypirc && echo 'username = __token__' >> ~/.pypirc && echo 'password = YOUR_TOKEN_HERE' >> ~/.pypirc"