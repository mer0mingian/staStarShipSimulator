#!/bin/bash
# Build script for STA Starship Simulator Mac app
#
# Creates a DMG installer with drag-to-Applications layout
#
# Prerequisites:
#   pip install pyinstaller
#   brew install create-dmg  (optional, for nicer DMG)
#
# Usage:
#   ./build_mac.sh          # Build .app and DMG

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  STA Starship Simulator - Mac Build"
echo "========================================"
echo ""

# Check for PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${RED}ERROR: PyInstaller not found${NC}"
    echo ""
    echo "Install it with:"
    echo "  pip install pyinstaller"
    exit 1
fi

# Get version from sta/version.py
VERSION=$(python3 -c "from sta.version import __version__; print(__version__)" 2>/dev/null || echo "0.1.0")
echo -e "${YELLOW}Building version: ${VERSION}${NC}"
echo ""

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf build/ dist/

# Run PyInstaller
echo -e "${YELLOW}Running PyInstaller...${NC}"
pyinstaller STASimulator.spec --noconfirm

# Check if build succeeded
APP_PATH="dist/STA Starship Simulator.app"
if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}ERROR: Build failed - .app bundle not found${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}App bundle created!${NC}"
echo ""

# Create DMG
DMG_NAME="STA-Starship-Simulator-${VERSION}"
DMG_PATH="dist/${DMG_NAME}.dmg"

echo -e "${YELLOW}Creating DMG installer...${NC}"

# Check if create-dmg is available (makes nicer DMGs)
if command -v create-dmg &> /dev/null; then
    echo "Using create-dmg for professional DMG layout..."

    # Remove existing DMG if present
    rm -f "$DMG_PATH"

    create-dmg \
        --volname "STA Starship Simulator" \
        --volicon "AppIcon.icns" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "STA Starship Simulator.app" 150 185 \
        --hide-extension "STA Starship Simulator.app" \
        --app-drop-link 450 185 \
        "$DMG_PATH" \
        "$APP_PATH"
else
    echo "Note: Install 'brew install create-dmg' for a nicer DMG layout"
    echo "Creating basic DMG with hdiutil..."

    # Create a temporary directory for DMG contents
    DMG_TEMP="dist/dmg_temp"
    rm -rf "$DMG_TEMP"
    mkdir -p "$DMG_TEMP"

    # Copy app to temp directory
    cp -R "$APP_PATH" "$DMG_TEMP/"

    # Create Applications symlink
    ln -s /Applications "$DMG_TEMP/Applications"

    # Create the DMG
    rm -f "$DMG_PATH"
    hdiutil create -volname "STA Starship Simulator" \
        -srcfolder "$DMG_TEMP" \
        -ov -format UDZO \
        "$DMG_PATH"

    # Cleanup
    rm -rf "$DMG_TEMP"
fi

# Verify DMG was created
if [ ! -f "$DMG_PATH" ]; then
    echo -e "${RED}ERROR: DMG creation failed${NC}"
    exit 1
fi

# Get DMG size
DMG_SIZE=$(du -h "$DMG_PATH" | cut -f1)

echo ""
echo -e "${GREEN}========================================"
echo "  Build Complete!"
echo "========================================${NC}"
echo ""
echo "DMG Installer: dist/${DMG_NAME}.dmg (${DMG_SIZE})"
echo ""
echo "To install:"
echo "  1. Open the DMG file"
echo "  2. Drag 'STA Starship Simulator' to Applications"
echo "  3. Eject the DMG"
echo "  4. Launch from Applications folder"
echo ""
echo "To distribute:"
echo "  Upload the DMG to GitHub Releases"
echo ""
