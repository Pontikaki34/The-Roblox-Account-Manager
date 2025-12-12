import os
import sys

if getattr(sys, "frozen", False):
 .
    base = getattr(sys, "_MEIPASS", None)
    if base:
      
        candidates = [
            os.path.join(base, "platforms"),
            os.path.join(base, "PyQt5", "Qt", "plugins", "platforms"),
            os.path.join(base, "PySide2", "plugins", "platforms"),
        ]
        for c in candidates:
            if os.path.isdir(c):
                os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", c)
                break