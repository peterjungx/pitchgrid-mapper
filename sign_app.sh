#!/bin/bash
# Code signing script for PG Isomap
# Usage: ./sign_app.sh [identity]

set -e

# Load environment variables
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a
fi

IDENTITY="${1:-$CODESIGN_IDENTITY}"
APP_NAME="${APP_NAME:-PGIsomap}"
APP_PATH="dist/${APP_NAME}.app"

if [ ! -d "$APP_PATH" ]; then
    echo "❌ App not found at $APP_PATH"
    echo "Run ./build_app.sh first"
    exit 1
fi

if [ -z "$IDENTITY" ]; then
    echo "⚠️  No code signing identity specified"
    echo "Set CODESIGN_IDENTITY in .env or pass as argument"
    echo "Skipping code signing..."
    exit 0
fi

echo "🔐 Signing ${APP_NAME}.app with identity: $IDENTITY"

# Remove extended attributes that can interfere with signing
echo "  Removing extended attributes..."
# Use xattr -rc (recursive, clear) and also explicitly try to remove common problematic attributes
xattr -rc "$APP_PATH" 2>/dev/null || true
# Find and remove quarantine and provenance attributes specifically
find "$APP_PATH" -type f -exec xattr -d com.apple.quarantine {} \; 2>/dev/null || true
find "$APP_PATH" -type f -exec xattr -d com.apple.provenance {} \; 2>/dev/null || true

# Remove any existing signatures and CodeResources first
echo "  Removing existing signatures..."
find "$APP_PATH" -name "_CodeSignature" -type d -exec rm -rf {} + 2>/dev/null || true

# Get the Team ID from the .env file
TEAM_ID="${TEAM_ID:-LYMCTRRY76}"

# Sign all binaries using --deep first pass, then re-sign the bundle
# The --deep flag handles the nested structure correctly
echo "  Signing entire app bundle with --deep..."
codesign --deep --force --sign "$IDENTITY" --options runtime --timestamp --entitlements entitlements.plist "$APP_PATH"

# Sign Python.framework explicitly to ensure it's properly sealed
if [ -d "$APP_PATH/Contents/Frameworks/Python.framework" ]; then
    echo "  Re-signing Python.framework..."
    codesign --force --sign "$IDENTITY" --options runtime --timestamp "$APP_PATH/Contents/Frameworks/Python.framework"
fi

# Re-sign the main executable to ensure entitlements are applied
echo "  Re-signing main executable..."
codesign --force --sign "$IDENTITY" --options runtime --timestamp --entitlements entitlements.plist "$APP_PATH/Contents/MacOS/$APP_NAME"

# Finally sign the app bundle (recreates the seal)
echo "  Signing app bundle..."
codesign --force --sign "$IDENTITY" --options runtime --timestamp --entitlements entitlements.plist "$APP_PATH"

# Verify signature (deep strict verification)
echo "✅ Verifying signature..."
if codesign --verify --deep --strict "$APP_PATH" 2>&1; then
    echo "🎉 ${APP_NAME}.app signature verified (deep strict)!"
else
    echo "⚠️  Signature verification failed"
    exit 1
fi

# Check signature details
echo "📋 Signature details:"
codesign -d --verbose=2 "$APP_PATH" 2>&1 | grep -E "(Authority|TeamIdentifier|Timestamp)" || true

# Test with spctl
echo ""
echo "🧪 Testing Gatekeeper assessment..."
if spctl --assess --type execute -v "$APP_PATH" 2>&1; then
    echo "✅ App passes Gatekeeper assessment"
else
    echo "⚠️  Gatekeeper assessment requires notarization for distribution"
    echo "   Run ./notarize_app.sh to notarize the app"
fi
