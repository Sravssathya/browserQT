@echo off
REM Secure Browser Windows Installer
REM Run this as Administrator

echo ========================================
echo Secure Browser - Windows Installer
echo ========================================
echo.

REM Check for Administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This installer must be run as Administrator!
    echo Right-click install.bat and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Variables
set INSTALL_DIR=%ProgramFiles%\TeleBrowser
set START_MENU=%ProgramData%\Microsoft\Windows\Start Menu\Programs
set DESKTOP=%Public%\Desktop

REM Step 1: Check if files exist
echo Step 1: Checking installation files...

if not exist "TeleBrowser.exe" (
    echo ERROR: TeleBrowser.exe not found in current directory!
    pause
    exit /b 1
)
echo   Found: TeleBrowser.exe

if exist "browser.ico" (
    echo   Found: browser.ico
    set HAS_ICON=1
) else (
    echo   Warning: browser.ico not found (using default icon)
    set HAS_ICON=0
)

REM Step 2: Create installation directory
echo.
echo Step 2: Creating installation directory...

if exist "%INSTALL_DIR%" (
    echo   Removing old installation...
    rmdir /s /q "%INSTALL_DIR%"
)

mkdir "%INSTALL_DIR%"
echo   Created: %INSTALL_DIR%

REM Step 3: Copy files
echo.
echo Step 3: Installing files...

copy /Y "TeleBrowser.exe" "%INSTALL_DIR%\"
echo   Installed: TeleBrowser.exe

if %HAS_ICON%==1 (
    copy /Y "browser.ico" "%INSTALL_DIR%\"
    echo   Installed: browser.ico
    set ICON_PATH=%INSTALL_DIR%\browser.ico
) else (
    set ICON_PATH=%INSTALL_DIR%\TeleBrowser.exe
)

REM Step 4: Create Start Menu shortcut
echo.
echo Step 4: Creating Start Menu shortcut...

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU%\Secure Browser.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\TeleBrowser.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%ICON_PATH%'; $Shortcut.Description = 'Secure Web Browser'; $Shortcut.Save()"

echo   Created Start Menu shortcut

REM Step 5: Create Desktop shortcut
echo.
echo Step 5: Creating Desktop shortcut...

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Secure Browser.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\TeleBrowser.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%ICON_PATH%'; $Shortcut.Description = 'Secure Web Browser'; $Shortcut.Save()"

echo   Created Desktop shortcut

REM Step 6: Add to PATH
echo.
echo Step 6: Adding to system PATH...

setx /M PATH "%PATH%;%INSTALL_DIR%" >nul 2>&1
echo   Added to PATH

REM Step 7: Create uninstaller
echo.
echo Step 7: Creating uninstaller...

(
echo @echo off
echo echo Uninstalling Secure Browser...
echo.
echo rmdir /s /q "%INSTALL_DIR%"
echo del /f /q "%START_MENU%\Secure Browser.lnk"
echo del /f /q "%DESKTOP%\Secure Browser.lnk"
echo.
echo echo Secure Browser has been uninstalled.
echo pause
) > "%INSTALL_DIR%\uninstall.bat"

echo   Created uninstaller

REM Step 8: Register in Programs and Features
echo.
echo Step 8: Registering in Programs and Features...

reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\TeleBrowser" /v "DisplayName" /t REG_SZ /d "Secure Browser" /f >nul
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\TeleBrowser" /v "DisplayIcon" /t REG_SZ /d "%ICON_PATH%" /f >nul
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\TeleBrowser" /v "UninstallString" /t REG_SZ /d "\"%INSTALL_DIR%\uninstall.bat\"" /f >nul
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\TeleBrowser" /v "InstallLocation" /t REG_SZ /d "%INSTALL_DIR%" /f >nul
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\TeleBrowser" /v "Publisher" /t REG_SZ /d "Secure Browser" /f >nul
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\TeleBrowser" /v "DisplayVersion" /t REG_SZ /d "1.0.0" /f >nul
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\TeleBrowser" /v "NoModify" /t REG_DWORD /d 1 /f >nul
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\TeleBrowser" /v "NoRepair" /t REG_DWORD /d 1 /f >nul

echo   Registered in Programs and Features

REM Completion
echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Secure Browser has been installed to:
echo   %INSTALL_DIR%
echo.
echo You can now:
echo   - Launch from Desktop shortcut
echo   - Find it in Start Menu
echo   - Run 'TeleBrowser.exe' from command line
echo.
echo To uninstall:
echo   - Use Programs and Features in Control Panel
echo   - Or run: %INSTALL_DIR%\uninstall.bat
echo.
echo.

set /p LAUNCH="Would you like to launch Secure Browser now? (Y/N): "
if /i "%LAUNCH%"=="Y" (
    start "" "%INSTALL_DIR%\TeleBrowser.exe"
    echo Launching Secure Browser...
)

echo.
pause