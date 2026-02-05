#!/bin/bash
# Setup script for x86_64 cross-compilation on Apple Silicon Macs
# Run this once before building for Intel Macs

set -e

echo "Setting up x86_64 build environment for Apple Silicon..."
echo ""

# Check if running on Apple Silicon
if [[ "$(uname -m)" != "arm64" ]]; then
    echo "This script is only needed on Apple Silicon Macs."
    echo "Your machine is $(uname -m), no setup needed."
    exit 0
fi

# Check if Rosetta is installed
if ! /usr/bin/pgrep -q oahd; then
    echo "Installing Rosetta 2..."
    softwareupdate --install-rosetta --agree-to-license
fi

# Check if x86_64 Homebrew exists
if [ ! -f /usr/local/bin/brew ]; then
    echo "Installing x86_64 Homebrew under /usr/local..."
    arch -x86_64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "x86_64 Homebrew already installed at /usr/local/bin/brew"
fi

# Install x86_64 Python
echo ""
echo "Installing x86_64 Python 3.12..."
arch -x86_64 /usr/local/bin/brew install python@3.12

# Verify installation
X86_PYTHON="/usr/local/bin/python3.12"
if [ -f "$X86_PYTHON" ]; then
    echo ""
    echo "Verifying x86_64 Python..."
    ARCH=$(file "$X86_PYTHON" | grep -o "x86_64" || echo "")
    if [ -n "$ARCH" ]; then
        echo "x86_64 Python installed successfully!"
        echo ""
        echo "Python location: $X86_PYTHON"
        echo "Python version: $($X86_PYTHON --version)"
    else
        echo "Warning: Python may not be x86_64. Check with: file $X86_PYTHON"
    fi
else
    echo "Error: Python installation failed"
    exit 1
fi

echo ""
echo "Setup complete!"
echo ""
echo "To build for Intel Macs, run:"
echo "  ./build_app.sh --arch x86_64"
echo ""
echo "To build for both architectures:"
echo "  ./build_app.sh --arch arm64"
echo "  ./notarize_app.sh --arch arm64"
echo "  ./build_app.sh --arch x86_64"
echo "  ./notarize_app.sh --arch x86_64"
echo "  ./create_release.sh  # uploads both DMGs"
