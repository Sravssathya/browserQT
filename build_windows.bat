@echo off
echo ========================================
echo Tele Browser Build System (Windows)
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python from https://www.python.org
    pause
    exit /b 1
)

REM Step 1: Clean previous builds
echo Step 1: Cleaning previous builds...
if exist obfuscated rmdir /s /q obfuscated
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist installer_output rmdir /s /q installer_output
if exist *.spec del /q *.spec
mkdir installer_output

REM Step 2: Install dependencies
echo Step 2: Installing dependencies...
python -m pip install --upgrade pip
python -m pip install PyQt5 PyQtWebEngine pyinstaller psutil

REM Step 3: Copy source files
echo Step 3: Preparing source files...
mkdir obfuscated
copy *.py obfuscated\
if exist browser.ico copy browser.ico obfuscated\

REM Step 4: Build with PyInstaller
echo Step 4: Building executable...
cd obfuscated

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name TeleBrowser ^
    --icon=browser.ico ^
    --hidden-import=PyQt5 ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=PyQt5.QtWebEngineWidgets ^
    --hidden-import=PyQt5.QtWebEngineCore ^
    --hidden-import=PyQt5.QtNetwork ^
    --hidden-import=anti_debug ^
    --hidden-import=psutil ^
    --hidden-import=platform ^
    --hidden-import=threading ^
    --hidden-import=subprocess ^
    --collect-all PyQt5 ^
    --copy-metadata psutil ^
    secure_browser.py

if errorlevel 1 (
    echo Build failed!
    cd ..
    pause
    exit /b 1
)

cd ..

REM Step 5: Copy output
echo Step 5: Organizing output...
copy obfuscated\dist\TeleBrowser.exe installer_output\

echo.
echo ========================================
echo BUILD SUCCESSFUL!
echo ========================================
echo Windows Executable: installer_output\TeleBrowser.exe
echo.
dir installer_output\TeleBrowser.exe
echo.
echo This .exe can run on any Windows 10/11 machine!
echo.
pause