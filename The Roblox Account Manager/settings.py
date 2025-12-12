import json
import os
import re
import subprocess
import sys
from pathlib import Path
from PyQt5 import QtWidgets, QtCore


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(460, 360)
        self.settings_file = "Jsons/settings.json"
        
        layout = QtWidgets.QVBoxLayout(self)

        tabs = QtWidgets.QTabWidget()
        layout.addWidget(tabs)

  
        general_tab = QtWidgets.QWidget()
        gen_layout = QtWidgets.QVBoxLayout(general_tab)

        self.chk_check_updates = QtWidgets.QCheckBox("Check for Updates")
        self.chk_async_launching = QtWidgets.QCheckBox("Async Launching")

        launch_h = QtWidgets.QHBoxLayout()
        self.spin_launch_delay = QtWidgets.QSpinBox()
        self.spin_launch_delay.setRange(0, 60)
        self.spin_launch_delay.setValue(8)
        launch_h.addWidget(QtWidgets.QLabel("Launch Delay"))
        launch_h.addStretch()
        launch_h.addWidget(self.spin_launch_delay)

        self.chk_disable_aging = QtWidgets.QCheckBox("Disable Aging Alert")
        self.chk_hide_multi = QtWidgets.QCheckBox("Multi Roblox")
        self.chk_run_on_startup = QtWidgets.QCheckBox("Run on Windows Startup")

        gen_layout.addWidget(self.chk_check_updates)
        gen_layout.addWidget(self.chk_async_launching)
        gen_layout.addLayout(launch_h)
        gen_layout.addWidget(self.chk_disable_aging)
        gen_layout.addWidget(self.chk_hide_multi)
        gen_layout.addWidget(self.chk_run_on_startup)
        gen_layout.addStretch()

        tabs.addTab(general_tab, "General")


        dev_tab = QtWidgets.QWidget()
        dev_layout = QtWidgets.QFormLayout(dev_tab)

        self.chk_debug_mode = QtWidgets.QCheckBox("Enable Debug Mode")
        self.line_webserver_port = QtWidgets.QLineEdit()
        self.line_webserver_port.setPlaceholderText("e.g. 8080")
        self.chk_disable_agings = QtWidgets.QCheckBox("Disable Aging Alert (developer)")
        dev_layout.addRow(self.chk_debug_mode)
        dev_layout.addRow("WebServer Port:", self.line_webserver_port)
        dev_layout.addRow(self.chk_disable_agings)

        tabs.addTab(dev_tab, "Developer")

        
        fps_group = QtWidgets.QGroupBox("FPS Unlocker")
        fps_layout = QtWidgets.QHBoxLayout(fps_group)
        left_col = QtWidgets.QVBoxLayout()
        right_col = QtWidgets.QVBoxLayout()

        self.chk_enable_fps = QtWidgets.QCheckBox("Enable FPS Unlocker")
        fps_target_layout = QtWidgets.QHBoxLayout()
        self.spin_target_fps = QtWidgets.QSpinBox()
        self.spin_target_fps.setRange(30, 1000)
        self.spin_target_fps.setValue(120)
        self.spin_target_fps.setEnabled(False)
        fps_target_layout.addWidget(QtWidgets.QLabel("Target FPS:"))
        fps_target_layout.addWidget(self.spin_target_fps)
        fps_target_layout.addStretch()

        self.btn_launch_fps = QtWidgets.QPushButton("Run FPS Unlocker")
        self.btn_launch_fps.setEnabled(False)

        left_col.addWidget(self.chk_enable_fps)
        left_col.addLayout(fps_target_layout)
        left_col.addWidget(self.btn_launch_fps)
        left_col.addStretch()

        fps_layout.addLayout(left_col)
        fps_layout.addLayout(right_col)

        layout.addWidget(fps_group)

        
        self.chk_enable_fps.toggled.connect(self._on_fps_toggled)
        self.btn_launch_fps.clicked.connect(self._on_launch_fps)

       
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        
        self._load_settings()

    def _on_fps_toggled(self, checked: bool):
        self.spin_target_fps.setEnabled(checked)
        self.btn_launch_fps.setEnabled(checked)

    def _get_roblox_settings_path(self):

        appdata = os.environ.get('LOCALAPPDATA')
        if not appdata:
            return None
        
        settings_path = Path(appdata) / 'Roblox' / 'GlobalBasicSettings_13.xml'
        
        if not settings_path.exists():
            return None
        
        return settings_path

    def _modify_fps_limit(self, target_fps):
    
        if target_fps <= 0:
            return False, f"Invalid target FPS value: {target_fps}"
        
        roblox_settings_path = self._get_roblox_settings_path()
        if not roblox_settings_path:
            return False, "Roblox settings file not found. Make sure Roblox is installed."
        
        try:
            
            with open(roblox_settings_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            
            pattern = r'(<int name="FramerateCap">)(-?\d+)(</int>)'
            
            if re.search(pattern, content):
                
                new_content = re.sub(
                    pattern,
                    f'\\g<1>{target_fps}\\g<3>',
                    content
                )
                
                
                if new_content != content:
                    with open(roblox_settings_path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    return True, f"Updated FPS cap to {target_fps}"
                else:
                    return True, f"FPS cap already set to {target_fps}"
            else:
                return False, "FramerateCap setting not found in Roblox settings file"
                
        except PermissionError:
            return False, "Permission denied. Try running the application as administrator."
        except Exception as e:
            return False, f"Error: {str(e)}"

    def _on_launch_fps(self):
  
        
        self._save_settings()
        
       
        if not self.chk_enable_fps.isChecked():
            QtWidgets.QMessageBox.warning(
                self,
                "FPS Unlocker Disabled",
                "Please enable FPS Unlocker first by checking the 'Enable FPS Unlocker' checkbox."
            )
            return
        
        target_fps = self.spin_target_fps.value()
        
       
        success, message = self._modify_fps_limit(target_fps)
        
        if success:
            QtWidgets.QMessageBox.information(
                self, 
                "FPS Unlocker", 
                f"FPS Unlocker executed successfully!\n\nTarget FPS: {target_fps}\n\n{message}"
            )
        else:
            QtWidgets.QMessageBox.warning(
                self, 
                "FPS Unlocker Error", 
                f"FPS Unlocker encountered an error:\n\n{message}"
            )

    def _load_settings(self):

        if not os.path.exists(self.settings_file):
            print(f"Settings file not found: {self.settings_file}")
            return
        
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            
            print(f"Loaded settings: {settings}")
            
            
            if "check_updates" in settings:
                self.chk_check_updates.setChecked(settings["check_updates"])
            if "async_launching" in settings:
                self.chk_async_launching.setChecked(settings["async_launching"])
            if "launch_delay" in settings:
                self.spin_launch_delay.setValue(settings["launch_delay"])
            if "disable_aging" in settings:
                self.chk_disable_aging.setChecked(settings["disable_aging"])
            if "multi_roblox" in settings:
                self.chk_hide_multi.setChecked(settings["multi_roblox"])
            if "run_on_startup" in settings:
                self.chk_run_on_startup.setChecked(settings["run_on_startup"])
            
            
            if "debug_mode" in settings:
                self.chk_debug_mode.setChecked(settings["debug_mode"])
            if "webserver_port" in settings:
                self.line_webserver_port.setText(str(settings["webserver_port"]))
            if "disable_aging_dev" in settings:
                self.chk_disable_agings.setChecked(settings["disable_aging_dev"])
            
            
            if "fps_unlocker_enabled" in settings:
                self.chk_enable_fps.setChecked(settings["fps_unlocker_enabled"])
            if "target_fps" in settings:
                self.spin_target_fps.setValue(settings["target_fps"])
            
            print("Settings loaded successfully")
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            QtWidgets.QMessageBox.warning(self, "Settings Error", 
                f"Settings file is corrupted. Using defaults.\nError: {e}")
        except Exception as e:
            print(f"Error loading settings: {e}")
            import traceback
            traceback.print_exc()

    def _save_settings(self):

        settings = {
         
            "check_updates": self.chk_check_updates.isChecked(),
            "async_launching": self.chk_async_launching.isChecked(),
            "launch_delay": self.spin_launch_delay.value(),
            "disable_aging": self.chk_disable_aging.isChecked(),
            "multi_roblox": self.chk_hide_multi.isChecked(),
            "run_on_startup": self.chk_run_on_startup.isChecked(),
            
            
            "debug_mode": self.chk_debug_mode.isChecked(),
            "webserver_port": self.line_webserver_port.text(),
            "disable_aging_dev": self.chk_disable_agings.isChecked(),
            
            
            "fps_unlocker_enabled": self.chk_enable_fps.isChecked(),
            "target_fps": self.spin_target_fps.value()
        }
        
        try:
           
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def _on_accept(self):
       
        self._save_settings()
        self.accept()