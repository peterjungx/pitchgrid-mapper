#!/bin/bash
# Create GitHub release script for PitchGrid Mapper

set -e

# Load environment variables
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a
fi

APP_NAME="${APP_NAME:-PitchGrid Mapper}"
VERSION="${APP_VERSION:-0.1.0}"
DMG_PATH="${APP_NAME}-${VERSION}.dmg"

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

# Release notes
RELEASE_NOTES="Release of PitchGrid Mapper application

## Changes
- Initial release

## Installation

### Windows
1. Download the Windows installer (PitchGrid-Mapper-*-Setup.exe)
2. Run the installer
3. Follow the setup wizard
4. Launch PitchGrid Mapper from Start Menu or Desktop

### macOS
1. Download the DMG file
2. Open the DMG
3. Drag PitchGrid Mapper to Applications
4. Launch from Applications folder

## Requirements

### Windows
- Windows 10 or later (64-bit)
- PitchGrid VST plugin (for scale sync)
- Virtual MIDI driver (e.g., loopMIDI) for MIDI routing

### macOS
- macOS 10.15 or later
- PitchGrid VST plugin (for scale sync)

## Notes
- The installer includes all necessary dependencies
- Configure your DAW to send MIDI from PitchGrid to PitchGrid Mapper's virtual MIDI port"

# Check if release already exists
echo "🔍 Checking if release v${VERSION} exists..."

if gh release view "v${VERSION}" &> /dev/null; then
    # Release exists, upload as additional asset
    echo "📦 Release v${VERSION} already exists"
    echo "⬆️  Uploading macOS DMG as additional asset..."

    gh release upload "v${VERSION}" "$DMG_PATH" --clobber

    echo "✅ DMG uploaded successfully!"
    echo "📦 Uploaded: $DMG_PATH"

    # Update release notes to include both platforms
    echo ""
    echo "📝 Updating release notes..."
    gh release edit "v${VERSION}" --notes "$RELEASE_NOTES"
else
    # Release doesn't exist, create it
    echo "🆕 Release v${VERSION} does not exist, creating new release..."

    gh release create "v${VERSION}" \
        --title "PitchGrid Mapper v${VERSION}" \
        --notes "$RELEASE_NOTES" \
        "$DMG_PATH"

    echo "✅ Release created successfully!"
    echo "📦 Uploaded: $DMG_PATH"
fi
