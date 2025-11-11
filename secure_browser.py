# -*- coding: utf-8 -*-
from anti_debug import check_debugger, check_vm, anti_debug_loop
import threading
import sys
import os
import subprocess
import time
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

class ClipboardManager:
    """Manages clipboard to allow internal copy-paste but block external paste"""
    def __init__(self):
        self.internal_texts = []  # Store multiple recent internal copies
        self.max_stored = 10  # Keep last 10 copies
        self.max_chars_url = 500  # Maximum characters for URL bar
    
    def mark_internal_copy(self, text):
        """Mark data as copied from within the application"""
        if text:
            # Add to list of internal copies
            if text not in self.internal_texts:
                self.internal_texts.insert(0, text)
                # Keep only last max_stored items
                self.internal_texts = self.internal_texts[:self.max_stored]
            
            lines = text.split('\n')
            print(f"\n{'='*60}")
            print(f"INTERNAL COPY STORED")
            print(f"{'='*60}")
            print(f"Length: {len(text)} characters")
            print(f"Lines: {len(lines)}")
            print(f"Total stored: {len(self.internal_texts)}")
            for i, line in enumerate(lines, 1):
                if len(line) > 60:
                    print(f"  Line {i}: {line[:60]}...")
                else:
                    print(f"  Line {i}: {line}")
            print(f"{'='*60}\n")
        
    def verify_paste(self, text):
        """Verify if paste is from internal source"""
        if not text:
            print("❌ Paste blocked: No text")
            return False
        
        # Check if text matches any stored internal copy
        is_internal = text in self.internal_texts
        
        lines = text.split('\n')
        print(f"\n{'='*60}")
        print(f"PASTE VERIFICATION")
        print(f"{'='*60}")
        print(f"Paste length: {len(text)} characters")
        print(f"Paste lines: {len(lines)}")
        print(f"Result: {'✅ ALLOWED' if is_internal else '❌ BLOCKED'}")
        
        if not is_internal:
            print(f"\nStored {len(self.internal_texts)} internal copies:")
            for i, stored in enumerate(self.internal_texts, 1):
                stored_lines = stored.split('\n')
                print(f"  {i}. {len(stored)} chars, {len(stored_lines)} lines")
                if text == stored:
                    print(f"     ✓ MATCH!")
                    is_internal = True
                    break
        
        print(f"{'='*60}\n")
        return is_internal
    
    def clear(self):
        """Clear internal tracking"""
        self.internal_texts = []

class SecureWebPage(QWebEnginePage):
    """Custom web page that controls copy-paste operations"""
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.loadFinished.connect(self.inject_security_script)
    
    def inject_security_script(self):
        """Inject JavaScript to control copy/paste in web pages"""
        script = """
        (function() {
            // Store multiple internal clipboard entries
            var internalClipboardData = [];
            var maxStored = 10;
            var lastCopiedTime = null;
            var copyTimeThreshold = 2000; // 2 seconds - consider paste internal if within this time of copy
            
            console.log('Security script loaded');
            
            // Disable right-click
            document.addEventListener('contextmenu', function(e) {
                e.preventDefault();
                return false;
            }, true);
            
            // Track copy events
            document.addEventListener('copy', function(e) {
                var selectedText = window.getSelection().toString();
                if (selectedText) {
                    // Store in internal clipboard array
                    if (internalClipboardData.indexOf(selectedText) === -1) {
                        internalClipboardData.unshift(selectedText);
                        if (internalClipboardData.length > maxStored) {
                            internalClipboardData = internalClipboardData.slice(0, maxStored);
                        }
                    }
                    
                    // Update last copy time
                    lastCopiedTime = Date.now();
                    
                    var lines = selectedText.split('\\n');
                    console.log('✓ Copy tracked:', selectedText.length, 'chars,', lines.length, 'lines');
                    console.log('  Stored copies:', internalClipboardData.length);
                    
                    // Allow the copy
                    return true;
                }
                e.preventDefault();
                return false;
            }, true);
            
            // Disable cut
            document.addEventListener('cut', function(e) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }, true);
            
            // Intercept paste
            document.addEventListener('paste', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                var pasteData = '';
                if (e.clipboardData) {
                    pasteData = e.clipboardData.getData('text');
                }
                
                if (!pasteData) {
                    console.log('✗ No paste data');
                    return false;
                }
                
                var lines = pasteData.split('\\n');
                console.log('Paste attempt:', pasteData.length, 'chars,', lines.length, 'lines');
                
                // Check if it matches any stored internal data
                var isInternal = internalClipboardData.indexOf(pasteData) !== -1;
                
                // If not found in stored data, check if paste is within 2 seconds of a copy
                if (!isInternal && lastCopiedTime !== null) {
                    var timeSinceCopy = Date.now() - lastCopiedTime;
                    console.log('Time since copy:', timeSinceCopy, 'ms');
                    if (timeSinceCopy <= copyTimeThreshold && timeSinceCopy >= 0) {
                        // Likely internal paste happening very soon after copy
                        isInternal = true;
                        console.log('✓ Recognized as internal paste (time-based)');
                    }
                }
                
                if (isInternal) {
                    console.log('✓ Internal paste ALLOWED');
                    
                    // Insert the text at cursor position
                    var target = e.target;
                    if (target.isContentEditable || target.tagName === 'TEXTAREA' || target.tagName === 'INPUT') {
                        if (document.queryCommandSupported('insertText')) {
                            document.execCommand('insertText', false, pasteData);
                        } else {
                            // Fallback
                            var selection = window.getSelection();
                            if (selection.rangeCount > 0) {
                                var range = selection.getRangeAt(0);
                                range.deleteContents();
                                range.insertNode(document.createTextNode(pasteData));
                            }
                        }
                    }
                    return true;
                }
                
                // Block external paste
                console.log('✗ External paste BLOCKED');
                console.log('  Stored', internalClipboardData.length, 'internal copies');
                return false;
            }, true);
            
            // Disable drag
            document.addEventListener('dragstart', function(e) {
                e.preventDefault();
                return false;
            }, true);
            
            // Disable keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                if (e.ctrlKey || e.metaKey) {
                    // Block Ctrl+X, Ctrl+A, Ctrl+S, Ctrl+P
                    if (e.keyCode == 88 || e.keyCode == 65 || 
                        e.keyCode == 83 || e.keyCode == 80) {
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
        })();
        """
        self.runJavaScript(script)
    
    def triggerAction(self, action, checked=False):
        # Block paste and other actions at Qt level
        if action in [QWebEnginePage.Cut, QWebEnginePage.Paste, 
                      QWebEnginePage.SelectAll, QWebEnginePage.Undo, 
                      QWebEnginePage.Redo]:
            return
        
        # Track copy action
        if action == QWebEnginePage.Copy:
            if self.main_window:
                # Get clipboard content after copy with multiple delays to catch it
                QTimer.singleShot(50, self.track_copy)
                QTimer.singleShot(150, self.track_copy)
                QTimer.singleShot(300, self.track_copy)
        
        super().triggerAction(action, checked)
    
    def track_copy(self):
        """Track copied text from web page"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text and self.main_window:
            self.main_window.clipboard_manager.mark_internal_copy(text)
    
    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if url.scheme() == 'javascript':
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)
    
    def createWindow(self, window_type):
        """Handle target="_blank" links by creating new tab"""
        if window_type == QWebEnginePage.WebBrowserTab:
            if self.main_window:
                return self.main_window.create_new_tab_page()
        return None

class SecureLineEdit(QLineEdit):
    """Custom QLineEdit that blocks external paste"""
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.setMaxLength(32767)
    
    def insertFromMimeData(self, source):
        """Override to control paste behavior"""
        if source.hasText():
            text = source.text()
            
            if self.main_window.clipboard_manager.verify_paste(text):
                # Convert newlines to spaces for single-line URL bar
                text_to_insert = text.replace('\n', ' ').replace('\r', ' ')
                
                # Check character limit
                max_chars = self.main_window.clipboard_manager.max_chars_url
                if len(text_to_insert) > max_chars:
                    self.main_window.statusBar().showMessage(
                        f'Text truncated to {max_chars} characters', 2000)
                    text_to_insert = text_to_insert[:max_chars]
                
                # Insert the text
                self.insert(text_to_insert)
                self.main_window.statusBar().showMessage('✓ Internal paste allowed', 1000)
            else:
                self.main_window.statusBar().showMessage('✗ External paste blocked!', 2000)
    
    def keyPressEvent(self, event):
        """Handle copy operations"""
        if event.matches(QKeySequence.Copy):
            super().keyPressEvent(event)
            # Multiple timers to ensure we catch the clipboard
            QTimer.singleShot(50, self.track_copy)
            QTimer.singleShot(150, self.track_copy)
            return
        
        if event.matches(QKeySequence.Paste):
            super().keyPressEvent(event)
            return
        
        super().keyPressEvent(event)
    
    def track_copy(self):
        """Track copy from LineEdit"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.main_window.clipboard_manager.mark_internal_copy(text)

class TeleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initial_network = None
        self.countdown_timer = None
        self.countdown_seconds = 30
        self.warning_dialog = None
        self.network_manager = None
        self.is_closing = False
        self.clipboard_manager = ClipboardManager()
        self.fullscreen_timer = None  # Timer to enforce fullscreen
        self.initUI()
        self.setupShortcuts()
        self.start_fullscreen_monitor()
        
    def initUI(self):
        self.setWindowTitle('Tele Web Browser')
        self.setGeometry(100, 100, 1200, 800)
        
        # Set window to always stay on top and disable minimize button
        self.setWindowFlags(
            Qt.Window | 
            Qt.WindowStaysOnTopHint | 
            Qt.CustomizeWindowHint | 
            Qt.WindowTitleHint | 
            Qt.WindowMaximizeButtonHint | 
            Qt.WindowCloseButtonHint
        )
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation bar with improved button arrangement
        nav_bar = QHBoxLayout()
        nav_bar.setContentsMargins(5, 5, 5, 5)
        nav_bar.setSpacing(3)
        
        # Navigation buttons group (Back, Forward, Refresh, Home)
        self.back_btn = QPushButton('◀')
        self.back_btn.setFixedSize(45, 35)
        self.back_btn.setToolTip('Go Back (Alt+Left)')
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #45a049;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.back_btn.clicked.connect(self.navigate_back)
        nav_bar.addWidget(self.back_btn)
        
        self.forward_btn = QPushButton('▶')
        self.forward_btn.setFixedSize(45, 35)
        self.forward_btn.setToolTip('Go Forward (Alt+Right)')
        self.forward_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #45a049;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.forward_btn.clicked.connect(self.navigate_forward)
        nav_bar.addWidget(self.forward_btn)
        
        self.refresh_btn = QPushButton('⟳')
        self.refresh_btn.setFixedSize(45, 35)
        self.refresh_btn.setToolTip('Refresh (F5)')
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                font-size: 18px;
                border: 1px solid #0b7dda;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0960a5;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_page)
        nav_bar.addWidget(self.refresh_btn)
        
        self.home_btn = QPushButton('⌂')
        self.home_btn.setFixedSize(45, 35)
        self.home_btn.setToolTip('Home (Alt+Home)')
        self.home_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                font-size: 18px;
                border: 1px solid #e68900;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        """)
        self.home_btn.clicked.connect(self.navigate_home)
        nav_bar.addWidget(self.home_btn)
        
        # Add spacing between navigation and tab controls
        nav_bar.addSpacing(15)
        
        # Tab control buttons
        self.new_tab_btn = QPushButton('+ New Tab')
        self.new_tab_btn.setFixedSize(85, 35)
        self.new_tab_btn.setToolTip('New Tab (Ctrl+T)')
        self.new_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #7b1fa2;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7b1fa2;
            }
            QPushButton:pressed {
                background-color: #6a1b9a;
            }
        """)
        self.new_tab_btn.clicked.connect(lambda: self.add_new_tab())
        nav_bar.addWidget(self.new_tab_btn)
        
        # Add stretch to push close button to the right
        nav_bar.addStretch()
        
        # Close button on the far right
        self.close_btn = QPushButton('✕')
        self.close_btn.setFixedSize(35, 35)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #da190b;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c1170a;
            }
        """)
        self.close_btn.setToolTip('Close Browser')
        self.close_btn.clicked.connect(self.close_browser)
        nav_bar.addWidget(self.close_btn)
        
        layout.addLayout(nav_bar)
        
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setMovable(True)
        self.tabs.currentChanged.connect(self.update_url_bar)
        layout.addWidget(self.tabs)
        
        self.add_new_tab(QUrl('https://ksjc.teleuniv.in'), 'Home')
        
        self.setup_downloads()
        self.setup_network_monitoring()
        
        self.statusBar().showMessage('Tele Browser - Copyright©2025 Teleparadigm Networks Ltd')
    
    def navigate_to_url(self):
        """Not used - address bar removed"""
        pass
    
    def update_url_bar(self):
        """Not used - address bar removed"""
        pass
        
    def setup_downloads(self):
        downloads_path = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        
        if not os.path.exists(downloads_path):
            os.makedirs(downloads_path)
        
        profile = QWebEngineProfile.defaultProfile()
        profile.setDownloadPath(downloads_path)
        profile.downloadRequested.connect(self.on_download_requested)
    
    def on_download_requested(self, download):
        filename = download.suggestedFileName()
        downloads_path = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        
        download.setDownloadDirectory(downloads_path)
        download.setDownloadFileName(filename)
        download.accept()
        
        self.statusBar().showMessage('Downloading: {} to Downloads folder'.format(filename), 5000)
        download.finished.connect(lambda: self.on_download_finished(filename))
    
    def on_download_finished(self, filename):
        self.statusBar().showMessage('Download completed: {}'.format(filename), 5000)
    
    def setup_network_monitoring(self):
        self.network_manager = QNetworkConfigurationManager()
        self.initial_network = self.get_current_network_id()
        self.network_manager.configurationChanged.connect(self.on_network_changed)
        print("Initial Network ID: {}".format(self.initial_network))
    
    def get_current_network_id(self):
        try:
            if sys.platform.startswith('linux'):
                result = subprocess.check_output(['ip', 'route', 'get', '8.8.8.8'], 
                                                stderr=subprocess.STDOUT)
                result = result.decode('utf-8')
                if 'dev' in result:
                    interface = result.split('dev')[1].split()[0]
                    return interface
        except:
            pass
        
        active_config = self.network_manager.defaultConfiguration()
        if active_config.isValid():
            return active_config.identifier()
        
        return None
    
    def on_network_changed(self, config):
        current_network = self.get_current_network_id()
        print("Network changed. Current: {}, Initial: {}".format(current_network, self.initial_network))
        
        if current_network != self.initial_network and current_network is not None:
            self.show_network_warning()
    
    def show_network_warning(self):
        if self.warning_dialog is not None:
            return
        
        self.countdown_seconds = 30
        self.warning_dialog = QMessageBox(self)
        self.warning_dialog.setIcon(QMessageBox.Warning)
        self.warning_dialog.setWindowTitle('Network Changed!')
        self.warning_dialog.setText('Network connection has changed!\n\nApplication will close in {} seconds...'.format(self.countdown_seconds))
        
        close_button = self.warning_dialog.addButton('Close Warning', QMessageBox.AcceptRole)
        self.warning_dialog.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)
        
        self.warning_dialog.buttonClicked.connect(self.close_warning_dialog)
        self.warning_dialog.show()
    
    def close_warning_dialog(self):
        if self.countdown_timer:
            self.countdown_timer.stop()
            self.countdown_timer = None
        if self.warning_dialog:
            self.warning_dialog.close()
            self.warning_dialog = None
        self.statusBar().showMessage('Warning dismissed. Browser will continue running.', 3000)
    
    def update_countdown(self):
        self.countdown_seconds -= 1
        
        current_network = self.get_current_network_id()
        if current_network == self.initial_network:
            self.close_warning_dialog()
            self.statusBar().showMessage('Network restored. Continuing...', 3000)
            return
        
        if self.countdown_seconds <= 0:
            if self.countdown_timer:
                self.countdown_timer.stop()
            if self.warning_dialog:
                self.warning_dialog.close()
            QApplication.quit()
        else:
            if self.warning_dialog:
                self.warning_dialog.setText('Network connection has changed!\n\nApplication will close in {} seconds...'.format(self.countdown_seconds))
    
    def add_new_tab(self, qurl=None, label="New Tab"):
        if qurl is None:
            qurl = QUrl('https://ksjc.teleuniv.in')

        browser = QWebEngineView()
        secure_page = SecureWebPage(browser, self)
        browser.setPage(secure_page)
        
        settings = browser.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, False)
        settings.setAttribute(QWebEngineSettings.ShowScrollBars, True)
        
        browser.setUrl(qurl)
        browser.setContextMenuPolicy(Qt.NoContextMenu)
        
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        
        browser.titleChanged.connect(lambda title, browser=browser: self.update_tab_title(browser, title))
        
        return browser
    
    def create_new_tab_page(self):
        browser = self.add_new_tab(QUrl('about:blank'), 'Loading...')
        return browser.page()
    
    def update_tab_title(self, browser, title):
        index = self.tabs.indexOf(browser)
        if index != -1:
            current_url = browser.url().toString()
            if current_url == 'https://ksjc.teleuniv.in' or current_url == 'https://ksjc.teleuniv.in/':
                self.tabs.setTabText(index, 'Home')
            else:
                if title and title.strip() and title != 'about:blank':
                    if len(title) > 20:
                        title = title[:20] + '...'
                    self.tabs.setTabText(index, title)
                else:
                    self.tabs.setTabText(index, 'Tab {}'.format(index + 1))
    
    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            self.statusBar().showMessage('Cannot close the last tab', 2000)
    
    def current_browser(self):
        return self.tabs.currentWidget()
    
    def setupShortcuts(self):
        pass
    
    def start_fullscreen_monitor(self):
        """Start a timer that continuously monitors and enforces fullscreen mode"""
        self.fullscreen_timer = QTimer()
        self.fullscreen_timer.timeout.connect(self.enforce_fullscreen)
        self.fullscreen_timer.start(500)  # Check every 500ms
    
    def enforce_fullscreen(self):
        """Continuously enforce fullscreen mode"""
        if not self.is_closing:
            if not self.isFullScreen():
                self.showFullScreen()
                self.activateWindow()
                self.raise_()
    
    def keyPressEvent(self, event):
        # Block Escape key to prevent exiting fullscreen
        if event.key() == Qt.Key_Escape:
            event.ignore()
            self.statusBar().showMessage('Exit fullscreen is disabled', 2000)
            return
        
        # Block F11 key to prevent toggling fullscreen
        if event.key() == Qt.Key_F11:
            event.ignore()
            self.statusBar().showMessage('Fullscreen toggle is disabled', 2000)
            return
        
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_C:
                # Multiple timers to ensure we catch the clipboard
                QTimer.singleShot(50, self.track_global_copy)
                QTimer.singleShot(150, self.track_global_copy)
                QTimer.singleShot(300, self.track_global_copy)
            
            if event.key() in [Qt.Key_X, Qt.Key_A, Qt.Key_S, Qt.Key_P]:
                event.ignore()
                self.statusBar().showMessage('This operation is DISABLED', 2000)
                return
            
            if event.key() == Qt.Key_T:
                self.add_new_tab()
                return
            
            if event.key() == Qt.Key_W:
                current_index = self.tabs.currentIndex()
                self.close_tab(current_index)
                return
            
            if event.key() == Qt.Key_Tab:
                next_index = (self.tabs.currentIndex() + 1) % self.tabs.count()
                self.tabs.setCurrentIndex(next_index)
                return
            
            if event.key() == Qt.Key_L:
                # Refresh page (Ctrl+L normally opens address bar, which is removed)
                self.refresh_page()
                return
        
        if event.key() == Qt.Key_F12:
            event.ignore()
            self.statusBar().showMessage('Developer tools are disabled', 2000)
            return
        
        if event.key() == Qt.Key_Print:
            event.ignore()
            self.statusBar().showMessage('Screenshot is disabled', 2000)
            return
        
        super().keyPressEvent(event)
    
    def track_global_copy(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.clipboard_manager.mark_internal_copy(text)
    
    def navigate_back(self):
        browser = self.current_browser()
        if browser:
            browser.back()
    
    def navigate_forward(self):
        browser = self.current_browser()
        if browser:
            browser.forward()
    
    def refresh_page(self):
        browser = self.current_browser()
        if browser:
            browser.reload()
    
    def navigate_home(self):
        browser = self.current_browser()
        if browser:
            browser.setUrl(QUrl('https://ksjc.teleuniv.in'))
    
    def close_browser(self):
        self.is_closing = True
        
        reply = QMessageBox.question(self, 'Close Browser', 
                                     'Are you sure you want to close the browser?',
                                     QMessageBox.Yes | QMessageBox.No, 
                                     QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.close()
        else:
            self.is_closing = False
    
    def closeEvent(self, event):
        if self.countdown_timer:
            self.countdown_timer.stop()
        if self.fullscreen_timer:
            self.fullscreen_timer.stop()
        event.accept()
    
    def changeEvent(self, event):
        # Prevent window from being minimized and force back to fullscreen
        if event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                # Force back to fullscreen immediately
                QTimer.singleShot(0, self.force_fullscreen)
                event.ignore()
                return
            elif not (self.windowState() & Qt.WindowFullScreen):
                # If not in fullscreen for any reason, force it back
                QTimer.singleShot(0, self.force_fullscreen)
                event.ignore()
                return
        super().changeEvent(event)
    
    def force_fullscreen(self):
        """Force the window back to fullscreen mode"""
        if not self.is_closing:
            self.setWindowState(Qt.WindowFullScreen)
            self.activateWindow()
            self.raise_()
            self.showFullScreen()
    
    def showEvent(self, event):
        """Ensure fullscreen when window is shown"""
        super().showEvent(event)
        if not self.is_closing:
            QTimer.singleShot(100, self.force_fullscreen)
    
    def focusOutEvent(self, event):
        """Regain focus and fullscreen when focus is lost"""
        super().focusOutEvent(event)
        if not self.is_closing:
            QTimer.singleShot(200, self.force_fullscreen)
    
    def eventFilter(self, obj, event):
        # Monitor for any window state changes globally
        if event.type() == QEvent.WindowStateChange:
            if not self.is_closing and not (self.windowState() & Qt.WindowFullScreen):
                QTimer.singleShot(0, self.force_fullscreen)
        return super().eventFilter(obj, event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Tele Browser')
    
    browser = TeleBrowser()
    browser.showFullScreen()  # Open in full screen mode
    browser.activateWindow()
    browser.raise_()
    
    app.installEventFilter(browser)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()