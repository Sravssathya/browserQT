python3 -m venv browser_env

source browser_env/bin/activate

pip install PyQt5 PyQtWebEngine

pip install PyQt5 PyQtWebEngine --only-binary :all:

python3 browser.py


`Option 1: Linux`

Run build_native_linux.sh

`Option 2: Native Windows - MOST RELIABLE`

Copy files to Windows machine:

secure_browser.py
anti_debug.py
browser.ico
build_windows.bat

Run build_windows.bat
Get SecureBrowser.exe


`User Agent Validation`

function isValidTeleBrowser() {
    // Get user agent from request headers
    $userAgent = $_SERVER['HTTP_USER_AGENT'] ?? '';
    
    // Define your custom token/pattern
    $requiredPattern = 'TeleBrowser/1.0';
    $secretToken = 'CustomToken/XYZ123SECRET';
    
    // Check if both pattern and secret token exist
    if (stripos($userAgent, $requiredPattern) !== false && 
        stripos($userAgent, $secretToken) !== false) {
        return true;
    }
    
    return false;
}
if (!isValidTeleBrowser()){

}