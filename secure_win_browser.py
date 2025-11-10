# -*- coding: utf-8 -*-
from anti_debug import check_debugger, check_vm, anti_debug_loop
import threading
import sys
import os
import subprocess
from PyQt5.QtCore import QUrl, Qt, QEvent, QStandardPaths, QTimer
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QWidget, QLineEdit, QPushButton, 
                             QToolBar, QAction, QMessageBox, QTabWidget, QTabBar)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings, QWebEngineProfile
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtNetwork import QNetworkConfigurationManager

# Before class definitions
check_debugger()
check_vm()

# Start anti-debug thread
debug_thread = threading.Thread(target=anti_debug_loop, daemon=True)
debug_thread.start()

class SecureWebPage(QWebEnginePage):
    """Custom web page that disables copy-paste operations"""
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window

        # Inject JavaScript to disable copy/paste in web content
        self.loadFinished.connect(self.inject_security_script)
    
    def inject_security_script(self):
        """Inject JavaScript to disable copy/paste/select in web pages"""
        script = """
        (function() {
            // Disable right-click
            document.addEventListener('contextmenu', function(e) {
                e.preventDefault();
                return false;
            }, true);
            
            // Disable copy
            document.addEventListener('copy', function(e) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }, true);
            
            // Disable cut
            document.addEventListener('cut', function(e) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }, true);
            
            // Disable paste
            document.addEventListener('paste', function(e) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }, true);
            
            // Disable text selection
            document.addEventListener('selectstart', function(e) {
                e.preventDefault();
                return false;
            }, true);
            
            // Disable drag
            document.addEventListener('dragstart', function(e) {
                e.preventDefault();
                return false;
            }, true);
            
            // Disable keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                // Block Ctrl+C, Ctrl+X, Ctrl+V, Ctrl+A, Ctrl+S, Ctrl+P
                if (e.ctrlKey || e.metaKey) {
                    if (e.keyCode == 67 || e.keyCode == 86 || e.keyCode == 88 || 
                        e.keyCode == 65 || e.keyCode == 83 || e.keyCode == 80) {
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    }
                }
                // Block F12 (DevTools)
                if (e.keyCode == 123) {
                    e.preventDefault();
                    return false;
                }
            }, true);
            
            // Apply CSS to disable selection
            var style = document.createElement('style');
            style.textContent = '* { -webkit-user-select: none !important; -moz-user-select: none !important; -ms-user-select: none !important; user-select: none !important; }';
            document.head.appendChild(style);
        })();
        """
        self.runJavaScript(script)
    
    def triggerAction(self, action, checked=False):
        # Block copy and paste actions at Qt level
        if action in [QWebEnginePage.Copy, QWebEnginePage.Cut, 
                      QWebEnginePage.Paste, QWebEnginePage.SelectAll,
                      QWebEnginePage.Undo, QWebEnginePage.Redo]:
            return
        super().triggerAction(action, checked)
    
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        # Block JavaScript URLs that might bypass restrictions
        if url.scheme() == 'javascript':
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)
    
    def createWindow(self, window_type):
        """Handle target="_blank" links by creating new tab"""
        if window_type == QWebEnginePage.WebBrowserTab:
            # Return a new page that will be added as a tab
            if self.main_window:
                return self.main_window.create_new_tab_page()
        return None

class TeleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initial_network = None
        self.countdown_timer = None
        self.countdown_seconds = 30
        self.warning_dialog = None
        self.network_manager = None
        self.is_closing = False  # Add flag to track closing state
        self.allow_deactivate = False  # Flag to allow window deactivation
        self.initUI()
        self.setupShortcuts()
        
    def initUI(self):
        self.setWindowTitle('Tele Web Browser')
        self.setGeometry(100, 100, 1200, 800)
        
        # Make window stay on top and disable minimize button
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.Window | 
            Qt.CustomizeWindowHint | 
            Qt.WindowTitleHint |
            Qt.WindowMaximizeButtonHint 
        )
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create navigation bar (no URL bar, just navigation buttons)
        nav_bar = QHBoxLayout()
        nav_bar.setContentsMargins(5, 5, 5, 5)
        
        # Back button
        self.back_btn = QPushButton('< Back')
        self.back_btn.setFixedSize(80, 30)
        self.back_btn.setToolTip('Go Back')
        self.back_btn.clicked.connect(self.navigate_back)
        nav_bar.addWidget(self.back_btn)
        
        # Forward button
        self.forward_btn = QPushButton('Forward >')
        self.forward_btn.setFixedSize(80, 30)
        self.forward_btn.setToolTip('Go Forward')
        self.forward_btn.clicked.connect(self.navigate_forward)
        nav_bar.addWidget(self.forward_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton('Refresh')
        self.refresh_btn.setFixedSize(80, 30)
        self.refresh_btn.setToolTip('Refresh')
        self.refresh_btn.clicked.connect(self.refresh_page)
        nav_bar.addWidget(self.refresh_btn)
        
        # Home button
        self.home_btn = QPushButton('Home')
        self.home_btn.setFixedSize(80, 30)
        self.home_btn.setToolTip('Home')
        self.home_btn.clicked.connect(self.navigate_home)
        nav_bar.addWidget(self.home_btn)
        
        # Add stretch to push close button to the right
        nav_bar.addStretch()
        
        # Close button
        self.close_btn = QPushButton('X Close')
        self.close_btn.setFixedSize(120, 30)
        self.close_btn.setStyleSheet('background-color: #ff4444; color: white; font-weight: bold;')
        self.close_btn.clicked.connect(self.close_browser)
        nav_bar.addWidget(self.close_btn)
        
        layout.addLayout(nav_bar)
        
        # Create tab widget for multiple tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setMovable(True)
        layout.addWidget(self.tabs)
        
        # Create first tab
        self.add_new_tab(QUrl('http://172.168.15.213/toofan'), 'Home')
        
        # Setup download handling
        self.setup_downloads()
        
        # Setup network monitoring
        self.setup_network_monitoring()
        
        # Status message
        self.statusBar().showMessage('Tele Browser - Copyright©2025 Teleparadigm Networks Ltd')
        
    def setup_downloads(self):
        """Setup download handling to Downloads folder"""
        # Get the default download path
        downloads_path = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        
        # If Downloads folder doesn't exist, create it
        if not os.path.exists(downloads_path):
            os.makedirs(downloads_path)
        
        # Get the default profile and set download path
        profile = QWebEngineProfile.defaultProfile()
        profile.setDownloadPath(downloads_path)
        profile.downloadRequested.connect(self.on_download_requested)
    
    def on_download_requested(self, download):
        """Handle download requests"""
        # Get the suggested filename
        filename = download.suggestedFileName()
        
        # Set the download path
        downloads_path = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        download_file_path = os.path.join(downloads_path, filename)
        
        # Set the path and accept the download
        download.setDownloadDirectory(downloads_path)
        download.setDownloadFileName(filename)
        download.accept()
        
        # Show status message
        self.statusBar().showMessage('Downloading: {} to Downloads folder'.format(filename), 5000)
        
        # Connect to finished signal to show completion
        download.finished.connect(lambda: self.on_download_finished(filename))
    
    def on_download_finished(self, filename):
        """Show message when download completes"""
        self.statusBar().showMessage('Download completed: {}'.format(filename), 5000)
    
    def setup_network_monitoring(self):
        """Setup network change monitoring"""
        self.network_manager = QNetworkConfigurationManager()
        
        # Store initial network configuration
        self.initial_network = self.get_current_network_id()
        
        # Connect to multiple signals for better detection
        self.network_manager.configurationChanged.connect(self.on_network_changed)
        self.network_manager.onlineStateChanged.connect(self.on_online_state_changed)
        self.network_manager.updateCompleted.connect(self.on_network_update)
        
        print("Initial Network ID: {}".format(self.initial_network))
        print("Platform: {}".format(sys.platform))
    
    def get_current_network_id(self):
        """Get current network identifier"""
        try:
            if sys.platform.startswith('linux'):
                # Try to get network interface info on Linux
                result = subprocess.check_output(['ip', 'route', 'get', '8.8.8.8'], 
                                                stderr=subprocess.STDOUT)
                result = result.decode('utf-8')
                # Extract interface name
                if 'dev' in result:
                    interface = result.split('dev')[1].split()[0]
                    return interface
        except:
            pass
        
        # Fallback: use Qt network manager
        active_config = self.network_manager.defaultConfiguration()
        if active_config.isValid():
            return active_config.identifier()
        
        return None
    
    def on_network_changed(self, config):
        """Handle network configuration changes"""
        current_network = self.get_current_network_id()
        
        print("Network changed. Current: {}, Initial: {}".format(current_network, self.initial_network))
        
        # Check if network has changed from initial
        if current_network != self.initial_network and current_network is not None:
            self.show_network_warning()
    
    def show_network_warning(self):
        """Show warning dialog when network changes"""
        if self.warning_dialog is not None:
            return  # Dialog already showing
        
        self.countdown_seconds = 30
        
        # Create warning dialog
        self.warning_dialog = QMessageBox(self)
        self.warning_dialog.setIcon(QMessageBox.Warning)
        self.warning_dialog.setWindowTitle('Network Changed!')
        self.warning_dialog.setText('Network connection has changed!\n\nApplication will close in {} seconds...'.format(self.countdown_seconds))
        self.warning_dialog.setStandardButtons(QMessageBox.NoButton)
        self.warning_dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Dialog)
        
        # Start countdown timer
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)  # Update every second
        
        self.warning_dialog.show()
    
    def update_countdown(self):
        """Update countdown and close app when it reaches 0"""
        self.countdown_seconds -= 1
        
        # Check if network has been restored
        current_network = self.get_current_network_id()
        if current_network == self.initial_network:
            # Network restored, cancel shutdown
            if self.countdown_timer:
                self.countdown_timer.stop()
                self.countdown_timer = None
            if self.warning_dialog:
                self.warning_dialog.close()
                self.warning_dialog = None
            self.statusBar().showMessage('Network restored. Continuing...', 3000)
            return
        
        if self.countdown_seconds <= 0:
            # Time's up, close the application
            if self.countdown_timer:
                self.countdown_timer.stop()
            if self.warning_dialog:
                self.warning_dialog.close()
            QApplication.quit()
        else:
            # Update dialog text
            if self.warning_dialog:
                self.warning_dialog.setText('Network connection has changed!\n\nApplication will close in {} seconds...'.format(self.countdown_seconds))
    
    def add_new_tab(self, qurl=None, label="New Tab"):
        """Add a new tab with a browser view"""
        if qurl is None:
            qurl = QUrl('http://172.168.15.213/toofan')

        # Create web view with custom page
        browser = QWebEngineView()
        secure_page = SecureWebPage(browser, self)
        browser.setPage(secure_page)
        
        # Disable developer tools and other features
        settings = browser.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, False)
        settings.setAttribute(QWebEngineSettings.ShowScrollBars, True)
        
        browser.setUrl(qurl)
        
        # Disable context menu on browser
        browser.setContextMenuPolicy(Qt.NoContextMenu)
        
        # Add tab
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        
        # Update tab title when page title changes
        browser.titleChanged.connect(lambda title, browser=browser: self.update_tab_title(browser, title))
        
        return browser
    
    def create_new_tab_page(self):
        """Create a new tab and return its page (for target="_blank" links)"""
        browser = self.add_new_tab(QUrl('about:blank'), 'Loading...')
        return browser.page()
    
    def update_tab_title(self, browser, title):
        """Update tab title when page title changes"""
        index = self.tabs.indexOf(browser)
        if index != -1:
            # Check if it's the home page
            current_url = browser.url().toString()
            if current_url == 'http://172.168.15.213/toofan' or current_url == 'http://172.168.15.213/toofan/':
                self.tabs.setTabText(index, 'Home')
            else:
                # Show page title if available, otherwise show "Tab"
                if title and title.strip() and title != 'about:blank':
                    # Limit title length for other pages
                    if len(title) > 20:
                        title = title[:20] + '...'
                    self.tabs.setTabText(index, title)
                else:
                    # If no title, just show generic tab name
                    self.tabs.setTabText(index, 'Tab {}'.format(index + 1))
    
    def close_tab(self, index):
        """Close a tab"""
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            # If it's the last tab, don't close it
            self.statusBar().showMessage('Cannot close the last tab', 2000)
    
    def current_browser(self):
        """Get the current active browser widget"""
        return self.tabs.currentWidget()
    
    def setupShortcuts(self):
        """Block common keyboard shortcuts"""
        pass
    
    def keyPressEvent(self, event):
        """Override key press events to block certain shortcuts"""
        # Block Alt+Tab, Alt+F4
        if event.modifiers() == Qt.AltModifier:
            if event.key() in [Qt.Key_Tab, Qt.Key_F4]:
                event.ignore()
                self.statusBar().showMessage('Alt+Tab and Alt+F4 are blocked', 2000)
                return
        
        # Block Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A, Ctrl+S, Ctrl+P
        if event.modifiers() == Qt.ControlModifier:
            if event.key() in [Qt.Key_C, Qt.Key_V, Qt.Key_X, Qt.Key_A, Qt.Key_S, Qt.Key_P]:
                event.ignore()
                self.statusBar().showMessage('Copy/Paste/Save operations are DISABLED', 2000)
                return
            
            # Ctrl+T for new tab
            if event.key() == Qt.Key_T:
                self.add_new_tab()
                return
            
            # Ctrl+W to close current tab
            if event.key() == Qt.Key_W:
                current_index = self.tabs.currentIndex()
                self.close_tab(current_index)
                return
            
            # Ctrl+Tab to switch to next tab
            if event.key() == Qt.Key_Tab:
                next_index = (self.tabs.currentIndex() + 1) % self.tabs.count()
                self.tabs.setCurrentIndex(next_index)
                return
        
        # Block F12 (Developer Tools)
        if event.key() == Qt.Key_F12:
            event.ignore()
            self.statusBar().showMessage('Developer tools are disabled', 2000)
            return
        
        # Block PrintScreen
        if event.key() == Qt.Key_Print:
            event.ignore()
            self.statusBar().showMessage('Screenshot is disabled', 2000)
            return
        
        super().keyPressEvent(event)
    
    def navigate_back(self):
        """Navigate to previous page"""
        browser = self.current_browser()
        if browser:
            browser.back()
    
    def navigate_forward(self):
        """Navigate to next page"""
        browser = self.current_browser()
        if browser:
            browser.forward()
    
    def refresh_page(self):
        """Refresh current page"""
        browser = self.current_browser()
        if browser:
            browser.reload()
    
    def navigate_home(self):
        """Navigate to home page"""
        browser = self.current_browser()
        if browser:
            browser.setUrl(QUrl('http://172.168.15.213/toofan'))
    
    def close_browser(self):
        """Close the browser"""
        # Set flags to allow proper closing
        self.is_closing = True
        self.allow_deactivate = True
        
        reply = QMessageBox.question(self, 'Close Browser', 
                                     'Are you sure you want to close the browser?',
                                     QMessageBox.Yes | QMessageBox.No, 
                                     QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.close()
        else:
            # User cancelled, reset flags
            self.is_closing = False
            self.allow_deactivate = False
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop timers if running
        if self.countdown_timer:
            self.countdown_timer.stop()
        event.accept()
    
    def changeEvent(self, event):
        """Prevent minimizing and losing focus"""
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                # Force window back to normal state
                event.ignore()
                self.setWindowState(Qt.WindowNoState)
                self.showNormal()
                self.activateWindow()
                self.raise_()
                self.statusBar().showMessage('Minimizing is disabled', 2000)
                return
        super().changeEvent(event)
    
    def eventFilter(self, obj, event):
        """Filter events to prevent focus loss and stay on top"""
        # Don't interfere if we're in the closing process or allowing deactivation
        if self.is_closing or self.allow_deactivate:
            return super().eventFilter(obj, event)
        
        # Removed the WindowDeactivate event handler to prevent blinking
        # The window will still stay on top due to WindowStaysOnTopHint flag
        return super().eventFilter(obj, event)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Tele Browser')
    
    # Disable clipboard access globally
    clipboard = app.clipboard()
    clipboard.blockSignals(True)
    
    # Create and show browser
    browser = TeleBrowser()
    browser.showMaximized()
    browser.activateWindow()
    browser.raise_()
    
    # Don't install event filter - it was causing the blinking issue
    # The WindowStaysOnTopHint flag is sufficient to keep window on top
    # app.installEventFilter(browser)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()