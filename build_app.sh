#!/bin/bash
# Build script for PG Isomap macOS app

set -e  # Exit on any error

# Load environment variables
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a
fi

APP_NAME="${APP_NAME:-PGIsomap}"
echo "Building ${APP_NAME} macOS application..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Generate fresh icons from icon_app.svg
echo "🎨 Generating app icons..."
./generate_icons.sh

# Build frontend
echo "🌐 Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Install/sync Python dependencies including build extras
echo "📦 Syncing Python dependencies..."
uv sync --extra build

# Clean previous builds
rm -rf build/ dist/

# Build the application
echo "🔨 Building application with PyInstaller..."
uv run pyinstaller pg_isomap.spec

# Sign the app
echo ""
echo "🔐 Signing the application..."
./sign_app.sh

echo ""
echo "✓ Build completed successfully!"
echo "✓ App location: dist/${APP_NAME}.app"
echo ""
echo "To test the app:"
echo "  open dist/${APP_NAME}.app"
echo ""
echo "To create a DMG for distribution:"
echo "  ./notarize_app.sh"
