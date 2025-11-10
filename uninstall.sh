#!/bin/bash

# Tele Browser Uninstallation Script for Linux

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================"
echo "Tele Browser - Uninstaller"
echo "========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    SUDO=""
else
    SUDO="sudo"
fi

# Variables
INSTALL_DIR="/opt/telebrowser"
BIN_LINK="/usr/local/bin/telebrowser"
DESKTOP_FILE="/usr/share/applications/telebrowser.desktop"
ICON_FILE="/usr/share/icons/hicolor/256x256/apps/telebrowser.png"

echo -e "${YELLOW}This will remove Tele Browser from your system.${NC}"
read -p "Are you sure? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Removing Tele Browser...${NC}"

# Remove installation directory
if [ -d "$INSTALL_DIR" ]; then
    echo "Removing: $INSTALL_DIR"
    $SUDO rm -rf "$INSTALL_DIR"
fi

# Remove symbolic link
if [ -L "$BIN_LINK" ] || [ -f "$BIN_LINK" ]; then
    echo "Removing: $BIN_LINK"
    $SUDO rm -f "$BIN_LINK"
fi

# Remove desktop entry
if [ -f "$DESKTOP_FILE" ]; then
    echo "Removing: $DESKTOP_FILE"
    $SUDO rm -f "$DESKTOP_FILE"
fi

# Remove icon
if [ -f "$ICON_FILE" ]; then
    echo "Removing: $ICON_FILE"
    $SUDO rm -f "$ICON_FILE"
fi

# Update databases
echo "Updating system databases..."
$SUDO update-desktop-database /usr/share/applications 2>/dev/null || true
$SUDO gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

echo ""
echo -e "${GREEN}========================================"
echo "Uninstallation Complete!"
echo "========================================${NC}"
echo ""
echo "Tele Browser has been removed from your system."
echo ""