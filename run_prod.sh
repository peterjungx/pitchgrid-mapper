#!/bin/bash
# Production startup script - Desktop app with built frontend

set -e

echo "=== PitchGrid Mapper Production Mode ==="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Build frontend if needed
if [ ! -d "frontend/dist" ] || [ "frontend/src" -nt "frontend/dist" ]; then
    echo "Building frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
    echo "Frontend built successfully"
fi

echo ""
echo "Starting PitchGrid Mapper..."
echo "Virtual MIDI Device: PitchGrid Mapper"
echo ""

# Run desktop app
uv run pg-isomap
