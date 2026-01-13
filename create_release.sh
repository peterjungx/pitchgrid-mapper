#!/bin/bash
# Create GitHub release script for PG Isomap

set -e

# Load environment variables
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a
fi

APP_NAME="${APP_NAME:-PGIsomap}"
VERSION="${APP_VERSION:-0.1.0}"
DMG_PATH="${APP_NAME}.dmg"

# Check if DMG exists
if [ ! -f "$DMG_PATH" ]; then
    echo "❌ DMG not found. Run ./build_app.sh and ./notarize_app.sh first"
    exit 1
fi

echo "🚀 Creating GitHub release for ${APP_NAME} v${VERSION}..."

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI not found. Install from https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub. Run 'gh auth login'"
    exit 1
fi

# Create release
gh release create "v${VERSION}" \
    --title "PG Isomap v${VERSION}" \
    --notes "Release of PG Isomap macOS application

## Changes
- Initial release

## Installation
1. Download the DMG file
2. Open the DMG
3. Drag PG Isomap to Applications
4. Launch from Applications folder

## Requirements
- macOS 10.15 or later
- PitchGrid VST plugin (for scale sync)" \
    "$DMG_PATH"

echo "✅ Release created successfully!"
echo "📦 Uploaded: $DMG_PATH"
