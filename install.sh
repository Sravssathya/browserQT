#!/bin/bash

# Tele Browser Installation Script for Linux
# This script installs the Tele Browser application system-wide

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================"
echo "Tele Browser - Linux Installer"
echo "========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}Running as root...${NC}"
    SUDO=""
else
    echo -e "${YELLOW}This script requires sudo privileges${NC}"
    SUDO="sudo"
fi

# Variables
APP_NAME="TeleBrowser"
INSTALL_DIR="/opt/telebrowser"
BIN_DIR="/usr/local/bin"
DESKTOP_DIR="/usr/share/applications"
ICON_DIR="/usr/share/icons/hicolor/256x256/apps"

# Step 1: Check if executable exists
echo -e "${YELLOW}Step 1: Checking installation files...${NC}"

if [ ! -f "installer_output/TeleBrowser" ]; then
    echo -e "${RED}Error: TeleBrowser executable not found!${NC}"
    echo "Please run ./build_native_linux.sh first"
    exit 1
fi

if [ ! -f "browser.ico" ]; then
    echo -e "${YELLOW}Warning: browser.ico not found, creating placeholder icon${NC}"
else
    echo -e "${GREEN}Found browser.ico${NC}"
fi

# Step 2: Install dependencies
echo -e "${YELLOW}Step 2: Installing system dependencies...${NC}"
$SUDO apt update
$SUDO apt install -y libxcb-xinerama0 libxcb-cursor0 libxcb-icccm4 \
    libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
    libxcb-shape0 libxkbcommon-x11-0 imagemagick

# Step 3: Create installation directory
echo -e "${YELLOW}Step 3: Creating installation directory...${NC}"
$SUDO mkdir -p "$INSTALL_DIR"
$SUDO mkdir -p "$ICON_DIR"

# Step 4: Copy executable
echo -e "${YELLOW}Step 4: Installing executable...${NC}"
$SUDO cp installer_output/TeleBrowser "$INSTALL_DIR/"
$SUDO chmod +x "$INSTALL_DIR/TeleBrowser"

# Step 5: Convert and install icon
echo -e "${YELLOW}Step 5: Installing icon...${NC}"
if [ -f "browser.ico" ]; then
    # Convert .ico to .png using ImageMagick
    convert browser.ico[0] /tmp/telebrowser.png 2>/dev/null || {
        echo -e "${YELLOW}Conversion failed, copying .ico directly${NC}"
        $SUDO cp browser.ico "$ICON_DIR/telebrowser.png"
    }
    
    if [ -f "/tmp/telebrowser.png" ]; then
        $SUDO cp /tmp/telebrowser.png "$ICON_DIR/telebrowser.png"
        rm /tmp/telebrowser.png
    fi
else
    # Create a simple placeholder icon
    echo -e "${YELLOW}Creating placeholder icon${NC}"
fi

# Step 6: Create symbolic link
echo -e "${YELLOW}Step 6: Creating command-line shortcut...${NC}"
$SUDO ln -sf "$INSTALL_DIR/TeleBrowser" "$BIN_DIR/telebrowser"

# Step 7: Create desktop entry
echo -e "${YELLOW}Step 7: Creating desktop entry...${NC}"
$SUDO tee "$DESKTOP_DIR/telebrowser.desktop" > /dev/null << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Tele Browser
Comment=A secure web browser with enhanced privacy features
Exec=$INSTALL_DIR/TeleBrowser
Icon=telebrowser
Terminal=false
Categories=Network;WebBrowser;
Keywords=browser;web;internet;
StartupNotify=true
StartupWMClass=TeleBrowser
EOF

$SUDO chmod 644 "$DESKTOP_DIR/telebrowser.desktop"

# Step 8: Update desktop database
echo -e "${YELLOW}Step 8: Updating system databases...${NC}"
$SUDO update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
$SUDO gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

# Step 9: Set permissions
echo -e "${YELLOW}Step 9: Setting permissions...${NC}"
$SUDO chown -R root:root "$INSTALL_DIR"
$SUDO chmod 755 "$INSTALL_DIR"

echo ""
echo -e "${GREEN}========================================"
echo "Installation Complete!"
echo "========================================${NC}"
echo ""
echo "Tele Browser has been installed to: $INSTALL_DIR"
echo ""
echo "You can now:"
echo "  • Run from terminal: telebrowser"
echo "  • Find it in your application menu"
echo "  • Search for 'Tele Browser' in your desktop environment"
echo ""