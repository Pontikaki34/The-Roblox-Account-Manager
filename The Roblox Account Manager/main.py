import sys
import json
import os
import subprocess
import webbrowser
import tempfile
import shutil
import time
import urllib.request
import sqlite3
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets


if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))



try:
    from roblox_login import RobloxLogin
    from roblox_launcher import RobloxLauncher
    ROBLOX_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Roblox modules not available - {e}")
    print("Install with: pip install selenium webdriver-manager")
    ROBLOX_MODULES_AVAILABLE = False
    RobloxLogin = None
    RobloxLauncher = None


try:
    import win32api
    import win32event
    import winerror
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False
    print("Warning: pywin32 not available - Multi-Roblox feature disabled")
    print("Install with: pip install pywin32")


try:
    from settings import SettingsDialog
except Exception:
    class SettingsDialog(QtWidgets.QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Settings")
            layout = QtWidgets.QVBoxLayout(self)
            layout.addWidget(QtWidgets.QLabel("Settings file missing."))
            btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
            btns.accepted.connect(self.accept)
            layout.addWidget(btns)


from security import SecurityDialog


def create_dark_palette():
    pal = QtGui.QPalette()
    base = QtGui.QColor(30, 32, 36)
    mid = QtGui.QColor(40, 44, 50)
    light = QtGui.QColor(220, 220, 220)
    accent = QtGui.QColor(60, 150, 200)

    pal.setColor(QtGui.QPalette.Window, base)
    pal.setColor(QtGui.QPalette.WindowText, light)
    pal.setColor(QtGui.QPalette.Base, mid)
    pal.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(36, 38, 42))
    pal.setColor(QtGui.QPalette.Text, light)
    pal.setColor(QtGui.QPalette.Button, mid)
    pal.setColor(QtGui.QPalette.ButtonText, light)
    pal.setColor(QtGui.QPalette.Highlight, accent)
    pal.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255, 255, 255))
    return pal


class MultiRobloxManager:
    

    def __init__(self, base_dir=None, settings_file="Jsons/settings.json"):
        self.process = None
        self.enabled = False
        self.base_dir = base_dir or os.path.abspath(".")
     ute
        if not os.path.isabs(settings_file):
            self.settings_file = os.path.join(self.base_dir, settings_file)
        else:
            self.settings_file = settings_file

    def start(self):
        
        if not PYWIN32_AVAILABLE:
            print("Cannot start Multi-Roblox: pywin32 not available")
            return False

        if self.process and self.process.poll() is None:
            print("Multi-Roblox already running")
            return True

        try:
         
            multiroblox_path = os.path.join(self.base_dir, "multiroblox.py")
            if not os.path.exists(multiroblox_path):
                print(f"multiroblox.py not found at {multiroblox_path}")
                return False

    
            python_exe = sys.executable
            if python_exe.endswith("python.exe"):
                pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
                if os.path.exists(pythonw_exe):
                    python_exe = pythonw_exe

            self.process = subprocess.Popen(
                [python_exe, multiroblox_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            self.enabled = True
            print("Multi-Roblox started successfully")
            return True

        except Exception as e:
            print(f"Failed to start Multi-Roblox: {e}")
            return False

    def stop(self):
        
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                print("Multi-Roblox stopped")
            except Exception as e:
                print(f"Error stopping Multi-Roblox: {e}")
                try:
                    self.process.kill()
                except:
                    pass

        self.process = None
        self.enabled = False

    def is_running(self):
     
        return self.process is not None and self.process.poll() is None

    def update_from_settings(self):
        
        if not os.path.exists(self.settings_file):
            return

        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)

            should_enable = settings.get("multi_roblox", False)

            if should_enable and not self.is_running():
                if PYWIN32_AVAILABLE:
                    return self.start()
                else:
                    print("Cannot enable Multi-Roblox: pywin32 not installed")
                    return False
            elif not should_enable and self.is_running():
                self.stop()
                return True
            elif should_enable and self.is_running():
                return True 
            elif not should_enable and not self.is_running():
                return True  

        except Exception as e:
            print(f"Error reading settings for Multi-Roblox: {e}")
            return False

        return False


class AddAccountDialog(QtWidgets.QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Account - Roblox Login")
        self.setMinimumWidth(450)
        self.setModal(True)
        self.cookie = None
        self.username = None
        self.password = None
        self.login_manager = None

        layout = QtWidgets.QVBoxLayout(self)

       
        instructions = QtWidgets.QLabel(
            "<b>Add Roblox Account</b><br><br>"
            "Enter your Roblox username and password below.<br>"
            "The login will be automated and your session cookie will be saved.<br><br>"
            "<b>Note:</b> 2FA (Two-Factor Authentication) is not supported.<br>"
            "If your account has 2FA enabled, please disable it temporarily or use cookie login."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        
        form_layout = QtWidgets.QFormLayout()
        form_layout.setLabelAlignment(QtCore.Qt.AlignRight)

        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Enter Roblox username")
        self.username_input.setMinimumHeight(32)
        form_layout.addRow("Username:", self.username_input)

        
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Enter Roblox password")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_input.setMinimumHeight(32)
        form_layout.addRow("Password:", self.password_input)

        
        self.alias_input = QtWidgets.QLineEdit()
        self.alias_input.setPlaceholderText("Optional nickname for this account")
        self.alias_input.setMinimumHeight(32)
        form_layout.addRow("Alias:", self.alias_input)

        layout.addLayout(form_layout)

       
        self.status_label = QtWidgets.QLabel("Ready to login")
        self.status_label.setStyleSheet("color: #3c8c40; font-weight: bold; padding: 5px;")
        layout.addWidget(self.status_label)

        
        self.progress = QtWidgets.QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        
        self.btn_login = QtWidgets.QPushButton("🔐 Login & Save Account")
        self.btn_login.setMinimumHeight(40)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #3c8c40;
                color: white;
                font-weight: bold;
                font-size: 11pt;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #4a9d4f;
            }
            QPushButton:disabled {
                background-color: #2b2d31;
                color: #666;
            }
        """)
        self.btn_login.clicked.connect(self._login_account)
        layout.addWidget(self.btn_login)

        
        self.btn_cookie_login = QtWidgets.QPushButton("Use Cookie Instead")
        self.btn_cookie_login.setMinimumHeight(30)
        self.btn_cookie_login.setStyleSheet("""
            QPushButton {
                background-color: #2b2d31;
                color: #888;
                border: 1px solid #3a3c41;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #333539;
                color: #ccc;
            }
        """)
        self.btn_cookie_login.clicked.connect(self._cookie_login)
        layout.addWidget(self.btn_cookie_login)

      
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)

       
        if not ROBLOX_MODULES_AVAILABLE:
            self._show_missing_modules_error()

    def _show_missing_modules_error(self):
    
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.btn_login.setEnabled(False)
        self.btn_cookie_login.setEnabled(False)

        self.status_label.setText("❌ Missing required modules")
        self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 5px;")

        error_msg = QtWidgets.QLabel(
            "<b>Selenium not installed!</b><br><br>"
            "Please install required packages:<br>"
            "<code>pip install selenium webdriver-manager</code><br><br>"
            "Then restart the application."
        )
        error_msg.setWordWrap(True)
        error_msg.setStyleSheet("color: #e74c3c; background-color: #2b2d31; padding: 10px; border-radius: 5px;")

        layout = self.layout()
        layout.insertWidget(1, error_msg)

    def _update_status(self, message, color="#3c8c40", progress=None):
       
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold; padding: 5px;")

        if progress is not None:
            self.progress.setVisible(True)
            self.progress.setValue(progress)

        QtWidgets.QApplication.processEvents()

    def _login_account(self):
        
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        alias = self.alias_input.text().strip()

        if not username:
            self._update_status("❌ Please enter a username", "#e74c3c")
            return

        if not password:
            self._update_status("❌ Please enter a password", "#e74c3c")
            return

        if not ROBLOX_MODULES_AVAILABLE:
            self._update_status("❌ Required modules not installed", "#e74c3c")
            return

    
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.btn_login.setEnabled(False)
        self.btn_cookie_login.setEnabled(False)

        self._update_status("⏳ Initializing browser...", "#f39c12", 10)

        try:
          
            self.login_manager = RobloxLogin()

            self._update_status("🖥️ Launching browser (visible)...", "#f39c12", 30)

          
            if not self.login_manager.setup_driver(username, headless=False):
                self._update_status("❌ Failed to initialize browser", "#e74c3c")
                self._reenable_inputs()
                return

            self._update_status("🔑 Logging in to Roblox...", "#f39c12", 50)


            if self.login_manager.login_with_credentials(username, password):
                self._update_status("✅ Login successful! Extracting cookie...", "#3c8c40", 80)

            
                cookie = self.login_manager.get_current_cookie()

                if cookie:
                    self.cookie = cookie
                    self.username = username

                  
                    if alias:
                        self.alias = alias

                    self._update_status("✅ Account ready to save!", "#3c8c40", 100)

                   
                    QtWidgets.QMessageBox.information(
                        self, "Success",
                        f"Account '{username}' logged in successfully!\n\n"
                        f"The session cookie has been captured and will be saved."
                    )

               
                    self.accept()
                else:
                    self._update_status("❌ Failed to extract cookie", "#e74c3c")
                    QtWidgets.QMessageBox.warning(
                        self, "Cookie Error",
                        "Logged in but failed to extract session cookie.\n"
                        "Please try again or use manual cookie method."
                    )
                    self._reenable_inputs()
            else:
                self._update_status("❌ Login failed", "#e74c3c")
                QtWidgets.QMessageBox.critical(
                    self, "Login Failed",
                    "Failed to login to Roblox.\n\n"
                    "Possible reasons:\n"
                    "1. Incorrect username/password\n"
                    "2. Account has 2FA enabled (not supported)\n"
                    "3. Roblox login page changed\n"
                    "4. Network issues\n\n"
                    "Please try again or use cookie login method."
                )
                self._reenable_inputs()

        except Exception as e:
            self._update_status(f"❌ Error: {str(e)[:50]}...", "#e74c3c")
            QtWidgets.QMessageBox.critical(
                self, "Login Error",
                f"An error occurred during login:\n\n{str(e)}\n\n"
                "Please try again or use cookie login method."
            )
            self._reenable_inputs()

        finally:
           
            if self.login_manager:
                self.login_manager.close()
                self.login_manager = None

    def _cookie_login(self):
       
        from PyQt5 import QtWidgets

        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Add Account with Cookie")
        dlg.setMinimumWidth(400)

        layout = QtWidgets.QVBoxLayout(dlg)

        instructions = QtWidgets.QLabel(
            "<b>Manual Cookie Login</b><br><br>"
            "1. Log in to Roblox in your browser<br>"
            "2. Open Developer Tools (F12)<br>"
            "3. Go to Application/Storage > Cookies<br>"
            "4. Copy the <code>.ROBLOSECURITY</code> cookie value<br><br>"
            "Paste the cookie below:"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        form_layout = QtWidgets.QFormLayout()

        username_input = QtWidgets.QLineEdit()
        username_input.setPlaceholderText("Enter username (optional, for display)")
        form_layout.addRow("Username:", username_input)

        cookie_input = QtWidgets.QTextEdit()
        cookie_input.setPlaceholderText("Paste .ROBLOSECURITY cookie here")
        cookie_input.setMaximumHeight(100)
        form_layout.addRow("Cookie:", cookie_input)

        layout.addLayout(form_layout)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            username = username_input.text().strip()
            cookie = cookie_input.toPlainText().strip()

            if not cookie:
                QtWidgets.QMessageBox.warning(self, "Missing Cookie", "Please enter a cookie value.")
                return

            if not username:
                username = "Unknown"

            self.username = username
            self.cookie = cookie

           
            alias = self.alias_input.text().strip()
            if alias:
                self.alias = alias

            QtWidgets.QMessageBox.information(
                self, "Success",
                f"Account '{username}' added with cookie!"
            )
            self.accept()

    def _reenable_inputs(self):
      
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)
        self.btn_login.setEnabled(True)
        self.btn_cookie_login.setEnabled(True)
        self.progress.setVisible(False)

    def get_account_data(self):
        return {
            "username": self.username if self.username else "Unknown",
            "cookie": self.cookie if self.cookie else "",
            "alias": getattr(self, 'alias', '')
        }


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, encryption_choice=None):
        super().__init__()
        self.encryption_choice = encryption_choice
       
        self.accounts_file = os.path.join(BASE_DIR, "Jsons", "accounts.json")
        self.settings_file = os.path.join(BASE_DIR, "Jsons", "settings.json")

       
        self.multi_roblox = MultiRobloxManager(base_dir=BASE_DIR, settings_file=os.path.join("Jsons", "settings.json"))

      
        self.login_manager = None
        self.launcher = None
        self.current_account = None

        if ROBLOX_MODULES_AVAILABLE:
            self.login_manager = RobloxLogin()
            self.launcher = RobloxLauncher()

        
        self._load_and_apply_settings()

        self.setWindowTitle("Roblox Account Manager")
       
        self.resize(760, 420)
        self.setMinimumSize(700, 360)

     
        self.setPalette(create_dark_palette())
        self.setStyleSheet("""
            QTableWidget { gridline-color: #2e2f34; }
            QHeaderView::section { background-color: #2b2d31; color: #e8eef6; padding: 3px; font-size: 9pt; }
            QPushButton { padding: 5px 8px; font-size: 9pt; }
            QLabel { color: #e8eef6; font-size: 9pt; }
            QLineEdit, QSpinBox, QTextEdit, QComboBox { background-color: #2b2d31; color: #e8eef6; border: 1px solid #3a3c41; padding: 3px; font-size: 9pt; }
        """)

        central = QtWidgets.QWidget()
        central_layout = QtWidgets.QVBoxLayout(central)
        central_layout.setContentsMargins(8, 8, 8, 8)
        central_layout.setSpacing(8)
        self.setCentralWidget(central)

        top_bar = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("<b>Roblox Account Manager</b>")
        title.setStyleSheet("font-size:11pt;")
        top_bar.addWidget(title)
        top_bar.addStretch()

  
        self.multi_roblox_indicator = QtWidgets.QLabel("Multi-Roblox: OFF")
        self.multi_roblox_indicator.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 9pt;")
        top_bar.addWidget(self.multi_roblox_indicator)
        self._update_multi_roblox_indicator()

        settings_btn = QtWidgets.QPushButton("Settings")
        settings_btn.setFixedHeight(26)
        settings_btn.clicked.connect(self.open_settings)
        top_bar.addWidget(settings_btn)

        central_layout.addLayout(top_bar)

      
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        central_layout.addWidget(splitter, 1)

        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        splitter.addWidget(left_widget)
        splitter.setStretchFactor(0, 2)

        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Username", "Alias", "Description"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        left_layout.addWidget(self.table)

        bottom_actions = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton("Add Account")
        self.btn_add.setFixedHeight(26)
        self.btn_remove = QtWidgets.QPushButton("Remove")
        self.btn_remove.setFixedHeight(26)
        self.chk_hide_usernames = QtWidgets.QCheckBox("Hide Usernames")
      
        bottom_actions.addWidget(self.btn_add)
        bottom_actions.addWidget(self.btn_remove)
        bottom_actions.addWidget(self.chk_hide_usernames)
        bottom_actions.addStretch()
        left_layout.addLayout(bottom_actions)

        theme_actions = QtWidgets.QHBoxLayout()
        self.btn_edit_theme = QtWidgets.QPushButton("Edit Theme")
        self.btn_edit_theme.setFixedHeight(22)
        self.btn_account_control = QtWidgets.QPushButton("Account Control")
        self.btn_account_control.setFixedHeight(22)
        theme_actions.addWidget(self.btn_edit_theme)
        theme_actions.addWidget(self.btn_account_control)
        theme_actions.addStretch()
        left_layout.addLayout(theme_actions)

        
        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 1)

   
        place_group = QtWidgets.QGroupBox("Current Place")
        pg_layout = QtWidgets.QFormLayout(place_group)
        pg_layout.setLabelAlignment(QtCore.Qt.AlignLeft)
        self.line_place_id = QtWidgets.QLineEdit()
        self.line_place_id.setPlaceholderText("Place ID")
        self.line_place_id.setFixedHeight(24)
        self.line_job_id = QtWidgets.QLineEdit()
        self.line_job_id.setPlaceholderText("Job ID")
        self.line_job_id.setFixedHeight(24)
        self.btn_join_server = QtWidgets.QPushButton("Join Server")
        self.btn_join_server.setFixedHeight(26)
        pg_layout.addRow("Place ID:", self.line_place_id)
        pg_layout.addRow("Job ID:", self.line_job_id)
        pg_layout.addRow("", self.btn_join_server)
        right_layout.addWidget(place_group)

      
        util_group = QtWidgets.QGroupBox("Utilities")
        u_layout = QtWidgets.QFormLayout(util_group)
        self.line_username = QtWidgets.QLineEdit()
        self.line_username.setFixedHeight(24)
        self.btn_follow = QtWidgets.QPushButton("Follow")
        self.btn_follow.setFixedHeight(24)
        h_user = QtWidgets.QHBoxLayout()
        h_user.addWidget(self.line_username)
        h_user.addWidget(self.btn_follow)
        u_layout.addRow("Username:", h_user)

        self.line_alias = QtWidgets.QLineEdit()
        self.line_alias.setFixedHeight(24)
        self.btn_set_alias = QtWidgets.QPushButton("Set Alias")
        self.btn_set_alias.setFixedHeight(24)
        h_alias = QtWidgets.QHBoxLayout()
        h_alias.addWidget(self.line_alias)
        h_alias.addWidget(self.btn_set_alias)
        u_layout.addRow("Set Alias:", h_alias)

        right_layout.addWidget(util_group)

       
        desc_group = QtWidgets.QGroupBox("Account Description")
        d_layout = QtWidgets.QVBoxLayout(desc_group)
        self.text_description = QtWidgets.QTextEdit()
        self.text_description.setFixedHeight(80)
        self.text_description.setPlaceholderText("Account Description\nCan be multiple lines")
        self.btn_set_description = QtWidgets.QPushButton("Set Description")
        self.btn_set_description.setFixedHeight(24)
        d_layout.addWidget(self.text_description)
        d_layout.addWidget(self.btn_set_description)
        right_layout.addWidget(desc_group)

        bottom_right = QtWidgets.QHBoxLayout()
        self.btn_account_utilities = QtWidgets.QPushButton("Account Utilities")
        self.btn_account_utilities.setFixedHeight(24)
        self.btn_set_description_short = QtWidgets.QPushButton("Set Description")
        self.btn_set_description_short.setFixedHeight(24)
        bottom_right.addWidget(self.btn_account_utilities)
        bottom_right.addWidget(self.btn_set_description_short)
        bottom_right.addStretch()
        right_layout.addLayout(bottom_right)

   
        self._load_accounts()

        
        self.btn_add.clicked.connect(self._add_account)
        self.btn_remove.clicked.connect(self._stub_remove)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.btn_join_server.clicked.connect(self._join_server)
        self.btn_set_alias.clicked.connect(self._stub_set_alias)
        self.btn_set_description.clicked.connect(self._stub_set_description)
        self.btn_set_description_short.clicked.connect(self._stub_set_description)
        self.btn_edit_theme.clicked.connect(self._stub_edit_theme)
        self.btn_account_control.clicked.connect(self._stub_account_control)
        self.btn_follow.clicked.connect(self._follow_user)

    def _load_and_apply_settings(self):
       
        if not os.path.exists(self.settings_file):
            return

        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)

          
            self.multi_roblox.update_from_settings()

        except Exception as e:
            print(f"Error loading settings: {e}")

    def _update_multi_roblox_indicator(self):
        
        if self.multi_roblox.is_running():
            self.multi_roblox_indicator.setText("Multi-Roblox: ON")
            self.multi_roblox_indicator.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 9pt;")
        else:
            self.multi_roblox_indicator.setText("Multi-Roblox: OFF")
            self.multi_roblox_indicator.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 9pt;")

    def _load_accounts(self):
       
        if not os.path.exists(self.accounts_file):
            print(f"Accounts file not found: {self.accounts_file}")
            return

        try:
            with open(self.accounts_file, 'r') as f:
                accounts = json.load(f)

            print(f"Loaded {len(accounts)} accounts")

           
            self.table.setRowCount(0)

           
            for account in accounts:
                r = self.table.rowCount()
                self.table.insertRow(r)

               
                username_item = QtWidgets.QTableWidgetItem(account.get("username", ""))
                username_item.setData(QtCore.Qt.UserRole, account.get("cookie", account.get("password", "")))
                self.table.setItem(r, 0, username_item)

                
                self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(account.get("alias", "")))

                
                desc = account.get("description", "")
                it = QtWidgets.QTableWidgetItem(desc)
                it.setToolTip(desc)
                self.table.setItem(r, 2, it)

            print("Accounts loaded successfully")

        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            QtWidgets.QMessageBox.warning(self, "Load Error",
                                          f"Accounts file is corrupted.\nError: {e}")
        except Exception as e:
            print(f"Error loading accounts: {e}")
            import traceback
            traceback.print_exc()

    def _save_accounts(self):
    
        accounts = []

        for row in range(self.table.rowCount()):
            username_item = self.table.item(row, 0)
            alias_item = self.table.item(row, 1)
            desc_item = self.table.item(row, 2)

            account = {
                "username": username_item.text() if username_item else "",
                "cookie": username_item.data(QtCore.Qt.UserRole) if username_item else "",
                "alias": alias_item.text() if alias_item else "",
                "description": desc_item.text() if desc_item else ""
            }
            accounts.append(account)

        try:
          
            accounts_dir = os.path.dirname(self.accounts_file)
            if not os.path.exists(accounts_dir):
                try:
                    os.makedirs(accounts_dir, exist_ok=True)
                except Exception:
                    pass

            with open(self.accounts_file, 'w') as f:
                json.dump(accounts, f, indent=4)
            print(f"Saved {len(accounts)} accounts")
        except Exception as e:
            print(f"Error saving accounts: {e}")
            QtWidgets.QMessageBox.critical(self, "Save Error", f"Failed to save accounts: {e}")

    def _add_account(self):
       
        if not ROBLOX_MODULES_AVAILABLE:
            QtWidgets.QMessageBox.critical(
                self, "Modules Missing",
                "Roblox login modules not available.\n\n"
                "Please install required packages:\n"
                "pip install selenium webdriver-manager\n\n"
                "Then restart the application."
            )
            return

        dlg = AddAccountDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            data = dlg.get_account_data()

            if not data["cookie"]:
                QtWidgets.QMessageBox.warning(self, "Error", "No cookie captured. Account not saved.")
                return

            r = self.table.rowCount()
            self.table.insertRow(r)

            
            username_item = QtWidgets.QTableWidgetItem(data["username"])
            username_item.setData(QtCore.Qt.UserRole, data["cookie"])
            self.table.setItem(r, 0, username_item)

            
            alias = data.get("alias", "")
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(alias))

        
            self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(""))

            self._save_accounts()

            QtWidgets.QMessageBox.information(
                self, "Success",
                f"Account '{data['username']}' added successfully!\n\n"
                f"The session cookie has been saved and can be used for future logins."
            )

    def _stub_remove(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        if not rows:
            return
        for r in rows:
            self.table.removeRow(r)
        self._save_accounts()

    def _on_selection_changed(self):
        rows = {i.row() for i in self.table.selectedIndexes()}
        if not rows:
            self.line_username.clear()
            self.text_description.clear()
            self.line_alias.clear()
            return
        r = sorted(rows)[0]
        uname = self.table.item(r, 0).text() if self.table.item(r, 0) else ""
        alias = self.table.item(r, 1).text() if self.table.item(r, 1) else ""
        desc = self.table.item(r, 2).text() if self.table.item(r, 2) else ""
        self.line_username.setText(uname)
        self.line_alias.setText(alias)
        self.text_description.setPlainText(desc)

    def _join_server(self):
        
        pid = self.line_place_id.text().strip()
        jid = self.line_job_id.text().strip()

        if not pid:
            QtWidgets.QMessageBox.warning(self, "Missing Place ID", "Please enter a Place ID.")
            return

        rows = {i.row() for i in self.table.selectedIndexes()}
        if not rows:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select an account first.")
            return

        row = sorted(rows)[0]
        username_item = self.table.item(row, 0)
        username = username_item.text() if username_item else ""
        cookie = username_item.data(QtCore.Qt.UserRole) if username_item else ""

        if not username or not cookie:
            QtWidgets.QMessageBox.warning(self, "Missing Credentials",
                                          "This account doesn't have stored cookie credentials.")
            return

        if not ROBLOX_MODULES_AVAILABLE:
            QtWidgets.QMessageBox.critical(
                self, "Modules Missing",
                "Roblox login modules not available.\n"
                "Please install: pip install selenium webdriver-manager"
            )
            return

        try:
        
            success, message = RobloxLauncher.launch_game(
                place_id=pid,
                job_id=jid if jid else None,
                username=username
            )

            if success:
                QtWidgets.QMessageBox.information(
                    self, "Success",
                    f"{message}\n\nChrome should open automatically with the game."
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Launch Failed",
                    f"Failed to launch game:\n\n{message}"
                )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error",
                f"An error occurred while joining server:\n{str(e)}"
            )

    def _follow_user(self):
     
        target_username = self.line_username.text().strip()

        if not target_username:
            QtWidgets.QMessageBox.warning(self, "Missing Username", "Please enter a username to follow.")
            return

        rows = {i.row() for i in self.table.selectedIndexes()}
        if not rows:
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select an account to use for following.")
            return

        row = sorted(rows)[0]
        username_item = self.table.item(row, 0)
        username = username_item.text() if username_item else ""
        cookie = username_item.data(QtCore.Qt.UserRole) if username_item else ""

        if not username or not cookie:
            QtWidgets.QMessageBox.warning(self, "Missing Credentials",
                                          "This account doesn't have stored cookie credentials.")
            return

        if not ROBLOX_MODULES_AVAILABLE:
            QtWidgets.QMessageBox.critical(
                self, "Modules Missing",
                "Roblox login modules not available.\n"
                "Please install: pip install selenium webdriver-manager"
            )
            return

   
        QtWidgets.QMessageBox.information(
            self, "Feature Not Implemented",
            f"The 'Follow User' feature is not yet implemented in RobloxLauncher.\n\n"
            f"You would need to add a follow_user method to roblox_launcher.py\n"
            f"that retrieves the user's current game and joins it."
        )

    def _stub_set_alias(self):
        alias = self.line_alias.text().strip()
        rows = {i.row() for i in self.table.selectedIndexes()}
        if not rows:
            QtWidgets.QMessageBox.warning(self, "Set Alias", "No account selected.")
            return
        for r in rows:
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(alias))
        self._save_accounts()

    def _stub_set_description(self):
        desc = self.text_description.toPlainText()
        rows = {i.row() for i in self.table.selectedIndexes()}
        if not rows:
            QtWidgets.QMessageBox.warning(self, "Set Description", "No account selected.")
            return
        for r in rows:
            self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(desc))
        self._save_accounts()

    def _stub_edit_theme(self):
        QtWidgets.QMessageBox.information(self, "Edit Theme", "Theme editor is not implemented in this UI-only demo.")

    def _stub_account_control(self):
        QtWidgets.QMessageBox.information(self, "Account Control", "Account control panel is not implemented in this UI-only demo.")

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
          
            self._load_and_apply_settings()
            
            self._update_multi_roblox_indicator()

    def closeEvent(self, event):
       
        self._save_accounts()

       
        if self.login_manager:
            self.login_manager.close()

       
        if self.multi_roblox.is_running():
            self.multi_roblox.stop()

        event.accept()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(create_dark_palette())

   
    sec = SecurityDialog()
    if sec.exec_() != QtWidgets.QDialog.Accepted:
        sys.exit(0)

    choice = getattr(sec, "choice", None)
    win = MainWindow(encryption_choice=choice)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()