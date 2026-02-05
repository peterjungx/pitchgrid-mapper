#!/bin/bash
# Create GitHub release script for PitchGrid Mapper
# Uploads all available DMG files for the current version

set -e

# Load environment variables
if [ -f .env ]; then
    set -a  # automatically export all variables
    source .env
    set +a
fi

APP_NAME="${APP_NAME:-PitchGrid Mapper}"
VERSION="${APP_VERSION:-0.1.0}"
DMG_NAME="${APP_NAME// /-}"  # Replace spaces with dashes for DMG filename

# Find all DMGs for this version (arm64, x86_64, or legacy without arch suffix)
DMG_FILES=()
for arch in arm64 x86_64; do
    dmg="${DMG_NAME}-${VERSION}-${arch}.dmg"
    if [ -f "$dmg" ]; then
        DMG_FILES+=("$dmg")
    fi
done

# Also check for legacy DMG without architecture suffix
LEGACY_DMG="${DMG_NAME}-${VERSION}.dmg"
if [ -f "$LEGACY_DMG" ]; then
    DMG_FILES+=("$LEGACY_DMG")
fi

# Check if any DMGs exist
if [ ${#DMG_FILES[@]} -eq 0 ]; then
    echo "❌ No DMG files found for version ${VERSION}"
    echo "Expected files like: ${DMG_NAME}-${VERSION}-arm64.dmg"
    echo "Run ./build_app.sh and ./notarize_app.sh first"
    exit 1
fi

echo "🚀 Creating GitHub release for ${APP_NAME} v${VERSION}..."
echo "📦 Found DMG files:"
for dmg in "${DMG_FILES[@]}"; do
    echo "   - $dmg"
done

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

# Load release notes from file
if [ ! -f "RELEASE_NOTES.md" ]; then
    echo "❌ RELEASE_NOTES.md not found"
    exit 1
fi
RELEASE_NOTES=$(cat RELEASE_NOTES.md)

# Check if release already exists
echo "🔍 Checking if release v${VERSION} exists..."

if gh release view "v${VERSION}" &> /dev/null; then
    # Release exists, upload as additional assets
    echo "📦 Release v${VERSION} already exists"
    echo "⬆️  Uploading macOS DMG(s) as additional assets..."

    for dmg in "${DMG_FILES[@]}"; do
        echo "   Uploading $dmg..."
        gh release upload "v${VERSION}" "$dmg" --clobber
    done

    echo "✅ DMG(s) uploaded successfully!"

    # Update release notes
    echo ""
    echo "📝 Updating release notes..."
    gh release edit "v${VERSION}" --notes "$RELEASE_NOTES"
else
    # Release doesn't exist, create it with all DMGs
    echo "🆕 Release v${VERSION} does not exist, creating new release..."

    gh release create "v${VERSION}" \
        --title "PitchGrid Mapper v${VERSION}" \
        --notes "$RELEASE_NOTES" \
        "${DMG_FILES[@]}"

    echo "✅ Release created successfully!"
fi

echo ""
echo "📦 Uploaded files:"
for dmg in "${DMG_FILES[@]}"; do
    echo "   - $dmg"
done
