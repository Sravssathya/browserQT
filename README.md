# Secure Browser

A lightweight custom secure browser built with **PyQt5** and **PyQtWebEngine**, featuring anti-debugging and custom user-agent validation.

---

## 🧰 Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git (optional, for cloning)
- Windows or Linux system

---

## 🚀 Setup Instructions

### Option 1: Linux

```bash
# Create a virtual environment
python3 -m venv browser_env

# Activate the environment
source browser_env/bin/activate

# Install dependencies
pip install PyQt5 PyQtWebEngine
# or for binary-only installs
pip install PyQt5 PyQtWebEngine --only-binary :all:

# Run the browser
python3 secure_browser.py


Option 2: Native Windows (Most Reliable)

Copy the following files to a Windows machine:

secure_browser.py

anti_debug.py

browser.ico

build_windows.bat

Run the build script:

build_windows.bat


Output will be generated as:

SecureBrowser.exe

User-Agent Validation (Server Side)

function isValidTeleBrowser() {
    // Get user agent from request headers
    $userAgent = $_SERVER['HTTP_USER_AGENT'] ?? '';
    
    // Define custom token/pattern
    $requiredPattern = 'TeleBrowser/1.0';
    $secretToken = 'CustomToken/XYZ123SECRET';
    
    // Validate both pattern and token
    if (stripos($userAgent, $requiredPattern) !== false && 
        stripos($userAgent, $secretToken) !== false) {
        return true;
    }
    return false;
}

// Block unauthorized access
if (!isValidTeleBrowser()) {
    http_response_code(403);
    exit('Access denied.');
}
