#!/bin/bash
# Notarization script for PitchGrid Mapper
# Requires: Apple Developer account with notarization enabled
# Usage: ./notarize_app.sh [--arch arm64|x86_64]

set -e

# Parse arguments
ARCH=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --arch)
            ARCH="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./notarize_app.sh [--arch arm64|x86_64]"
            exit 1
            ;;
    esac
done

# Default to native architecture if not specified
if [ -z "$ARCH" ]; then
    ARCH="${BUILD_ARCH:-$(uname -m)}"
fi

# Load environment variables
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a
fi

# Get configuration from environment
APP_NAME="${APP_NAME:-PitchGrid Mapper}"
APP_VERSION="${APP_VERSION:-0.1.0}"
APP_PATH="dist/${APP_NAME}.app"
DMG_NAME="${APP_NAME// /-}"  # Replace spaces with dashes for DMG filename
DMG_PATH="${DMG_NAME}-${APP_VERSION}-${ARCH}.dmg"

# Configuration from environment
APPLE_ID="${APPLE_ID:-your-apple-id@email.com}"
TEAM_ID="${TEAM_ID:-YOUR_TEAM_ID}"
APP_PASSWORD="${APP_PASSWORD:-your-app-specific-password}"  # Create at appleid.apple.com

# Check if credentials are set
if [[ "$APPLE_ID" == "your-apple-id@email.com" ]] || [[ "$APP_PASSWORD" == "your-app-specific-password" ]]; then
    echo "❌ Please set your Apple ID credentials in .env:"
    echo "   APPLE_ID='your@email.com'"
    echo "   APP_PASSWORD='your-app-specific-password'"
    echo ""
    echo "Create app-specific password at: https://appleid.apple.com/"
    exit 1
fi

echo "🚀 Starting notarization process for ${ARCH}..."

if [ ! -d "$APP_PATH" ]; then
    echo "❌ App not found. Run ./build_app.sh first"
    exit 1
fi

# Create DMG for notarization
echo "📦 Creating DMG..."
rm -f "$DMG_PATH"
hdiutil create -volname "$APP_NAME" -srcfolder "$APP_PATH" -ov -format UDZO "$DMG_PATH"

# Submit for notarization
echo "📤 Submitting for notarization..."
echo "This will take a few minutes..."

xcrun notarytool submit "$DMG_PATH" \
    --apple-id "$APPLE_ID" \
    --password "$APP_PASSWORD" \
    --team-id "$TEAM_ID" \
    --wait

# Check if successful
if [ $? -eq 0 ]; then
    echo "✅ Notarization successful!"

    # Staple the ticket
    echo "🎫 Stapling notarization ticket..."
    xcrun stapler staple "$DMG_PATH"
    xcrun stapler staple "$APP_PATH"

    echo "🎉 App is now signed and notarized!"
    echo "✅ Ready for distribution without warnings"

    # Test final result
    spctl -a -t exec -vv "$APP_PATH" && echo "✅ Gatekeeper check passed!"

else
    echo "❌ Notarization failed"
    echo "Check your Apple ID, password, and team ID"
fi
