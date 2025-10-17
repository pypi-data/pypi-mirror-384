#!/bin/bash

# DcisionAI MCP Server - PyPI Upload Script
# =========================================

echo "🚀 DcisionAI MCP Server - PyPI Upload Script"
echo "============================================="
echo ""

# Check if .pypirc exists and has tokens
if [ ! -f ".pypirc" ]; then
    echo "❌ .pypirc file not found!"
    echo "Please create .pypirc with your PyPI API tokens"
    exit 1
fi

if grep -q "YOUR_PYPI_API_TOKEN_HERE" .pypirc; then
    echo "❌ Please update .pypirc with your actual PyPI API tokens"
    echo ""
    echo "To get your API tokens:"
    echo "1. Go to https://pypi.org/manage/account/token/"
    echo "2. Create a new API token"
    echo "3. Copy the token and replace 'YOUR_PYPI_API_TOKEN_HERE' in .pypirc"
    echo ""
    echo "For TestPyPI:"
    echo "1. Go to https://test.pypi.org/manage/account/token/"
    echo "2. Create a new API token"
    echo "3. Copy the token and replace 'YOUR_TESTPYPI_API_TOKEN_HERE' in .pypirc"
    exit 1
fi

# Check if dist directory exists
if [ ! -d "dist" ]; then
    echo "❌ dist directory not found!"
    echo "Please run 'python -m build' first to build the package"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated"
    echo "Activating test-env..."
    source test-env/bin/activate
fi

echo "📦 Package files found:"
ls -la dist/
echo ""

# Ask user which upload to perform
echo "Choose upload option:"
echo "1) Upload to TestPyPI (recommended first)"
echo "2) Upload to PyPI (production)"
echo "3) Both (TestPyPI first, then PyPI)"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo "🚀 Uploading to TestPyPI..."
        twine upload --repository testpypi dist/*
        if [ $? -eq 0 ]; then
            echo "✅ Successfully uploaded to TestPyPI!"
            echo "Test installation with:"
            echo "pip install --index-url https://test.pypi.org/simple/ dcisionai-optimization"
        else
            echo "❌ Upload to TestPyPI failed"
            exit 1
        fi
        ;;
    2)
        echo "🚀 Uploading to PyPI (production)..."
        twine upload dist/*
        if [ $? -eq 0 ]; then
            echo "✅ Successfully uploaded to PyPI!"
            echo "Install with:"
            echo "pip install dcisionai-optimization"
        else
            echo "❌ Upload to PyPI failed"
            exit 1
        fi
        ;;
    3)
        echo "🚀 Uploading to TestPyPI first..."
        twine upload --repository testpypi dist/*
        if [ $? -eq 0 ]; then
            echo "✅ Successfully uploaded to TestPyPI!"
            echo ""
            read -p "Upload to production PyPI? (y/n): " confirm
            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                echo "🚀 Uploading to PyPI (production)..."
                twine upload dist/*
                if [ $? -eq 0 ]; then
                    echo "✅ Successfully uploaded to PyPI!"
                    echo "Install with:"
                    echo "pip install dcisionai-optimization"
                else
                    echo "❌ Upload to PyPI failed"
                    exit 1
                fi
            fi
        else
            echo "❌ Upload to TestPyPI failed"
            exit 1
        fi
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Upload complete!"
echo ""
echo "Next steps:"
echo "1. Test installation: pip install dcisionai-optimization"
echo "2. Share with developers: https://pypi.org/project/dcisionai-optimization/"
echo "3. Update documentation with installation instructions"
echo "4. Start building your developer community!"
