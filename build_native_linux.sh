#!/bin/bash
echo "========================================"
echo "Tele Browser Build System (Native Linux)"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo -e "${YELLOW}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 not found!${NC}"
    exit 1
fi

python3 --version

# Step 1: Clean previous builds
echo -e "${YELLOW}Step 1: Cleaning previous builds...${NC}"
rm -rf obfuscated dist build installer_output *.spec
mkdir -p installer_output

# Step 2: Install dependencies
echo -e "${YELLOW}Step 2: Installing dependencies...${NC}"
pip install --upgrade pip pyarmor pyinstaller PyQt5 PyQtWebEngine psutil

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies!${NC}"
    exit 1
fi

# Step 3: Copy all Python files
echo -e "${YELLOW}Step 3: Preparing source files...${NC}"
mkdir -p obfuscated
cp *.py obfuscated/ 2>/dev/null || true

# Copy any resource files
if [ -d "resources" ]; then
    cp -r resources obfuscated/
fi

# Step 3b: Obfuscate code (optional)
echo -e "${YELLOW}Step 3b: Obfuscating code with PyArmor (optional)...${NC}"

# Try PyArmor 8+ syntax
pyarmor gen --recursive --output obfuscated_temp *.py 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Obfuscation successful, using obfuscated files${NC}"
    rm -rf obfuscated
    mv obfuscated_temp obfuscated
else
    echo -e "${YELLOW}PyArmor not available or failed, using plain files${NC}"
fi

echo -e "${GREEN}Obfuscation complete!${NC}"

# Step 4: Build with PyInstaller
echo -e "${YELLOW}Step 4: Building executable with PyInstaller...${NC}"

cd obfuscated

# Find all Python files to include as hidden imports
HIDDEN_IMPORTS=""
for pyfile in *.py; do
    if [ -f "$pyfile" ] && [ "$pyfile" != "secure_browser.py" ]; then
        module_name="${pyfile%.py}"
        HIDDEN_IMPORTS="$HIDDEN_IMPORTS --hidden-import=$module_name"
    fi
done

pyinstaller \
    --onefile \
    --windowed \
    --name TeleBrowser \
    --hidden-import=PyQt5 \
    --hidden-import=PyQt5.QtCore \
    --hidden-import=PyQt5.QtGui \
    --hidden-import=PyQt5.QtWidgets \
    --hidden-import=PyQt5.QtWebEngineWidgets \
    --hidden-import=PyQt5.QtWebEngineCore \
    --hidden-import=PyQt5.QtNetwork \
    --hidden-import=anti_debug \
    --hidden-import=psutil \
    --hidden-import=platform \
    --hidden-import=threading \
    --hidden-import=subprocess \
    $HIDDEN_IMPORTS \
    --collect-all PyQt5 \
    --copy-metadata psutil \
    secure_browser.py

if [ $? -ne 0 ]; then
    echo -e "${RED}PyInstaller build failed!${NC}"
    cd ..
    exit 1
fi

cd ..

echo -e "${GREEN}Build complete!${NC}"

# Step 5: Compress with UPX (optional)
echo -e "${YELLOW}Step 5: Compressing with UPX...${NC}"
if command -v upx &> /dev/null; then
    upx --best obfuscated/dist/TeleBrowser 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}UPX compression successful${NC}"
    else
        echo -e "${YELLOW}UPX compression skipped${NC}"
    fi
else
    echo -e "${YELLOW}UPX not installed, skipping compression${NC}"
    echo "Install with: sudo apt install upx-ucl"
fi

# Step 6: Copy to output
echo -e "${YELLOW}Step 6: Organizing output...${NC}"
cp obfuscated/dist/TeleBrowser installer_output/
chmod +x installer_output/TeleBrowser

echo ""
echo -e "${GREEN}========================================"
echo "BUILD SUCCESSFUL!"
echo "========================================${NC}"
echo "Executable: installer_output/TeleBrowser"
echo ""
echo "To run: ./installer_output/TeleBrowser"
echo ""
echo "File size:"
ls -lh installer_output/TeleBrowser
echo ""