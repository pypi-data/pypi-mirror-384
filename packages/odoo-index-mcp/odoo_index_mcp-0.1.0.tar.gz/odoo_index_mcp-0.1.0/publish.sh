#!/bin/bash
set -e

echo "🔨 Building package..."
rm -rf dist/ build/ *.egg-info
uv build

echo ""
echo "📦 Package built successfully!"
echo ""
echo "Files in dist/:"
ls -lh dist/

echo ""
echo "📤 Ready to publish!"
echo ""
echo "To publish to TestPyPI (recommended first):"
echo "  uv tool run twine upload --repository testpypi dist/*"
echo ""
echo "To publish to PyPI:"
echo "  uv tool run twine upload dist/*"
