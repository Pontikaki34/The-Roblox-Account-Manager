from PyQt5 import QtCore, QtGui, QtWidgets


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


class SecurityDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.choice = None
        self.setWindowTitle("Roblox Account Manager")
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setModal(True)

        
        self.setMinimumSize(520, 160)
        self.setMaximumWidth(800)

        self.setStyleSheet("""
            QDialog { background-color: #1e2024; color: #e8eef6; }
            QLabel { color: #e8eef6; font-size: 12pt; }
            QPushButton {
                background-color: #2b2d31;
                color: #e8eef6;
                border: 1px solid #3a3c41;
                padding: 10px;
                font-size: 10pt;
                min-height: 36px;
            }
            QPushButton:hover { background-color: #333539; }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(12)

        label = QtWidgets.QLabel("Please select how you want your data to be secured")
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label)

        btn_default = QtWidgets.QPushButton("Default Encryption")
        btn_password = QtWidgets.QPushButton("Password Locked (Recommended)")

        
        buttons_layout = QtWidgets.QVBoxLayout()
        buttons_layout.setSpacing(8)
        buttons_layout.addWidget(btn_default)
        buttons_layout.addWidget(btn_password)
        layout.addLayout(buttons_layout)

        layout.addStretch()

        btn_default.clicked.connect(self._on_default)
        btn_password.clicked.connect(self._on_password)

        
        self.setPalette(create_dark_palette())

    def _on_default(self):
        self.choice = "default"
        self.accept()

    def _on_password(self):
        self.choice = "password"
        self.accept()