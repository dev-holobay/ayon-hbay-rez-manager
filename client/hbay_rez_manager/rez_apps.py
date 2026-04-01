"""
Configuration for Rez applications that can be launched from the tray menu.
"""
import os

ADDON_ROOT = os.path.dirname(os.path.abspath(__file__))

REZ_APPS = {
    "USD View": {
        "rez-request": ["usd_nvidia"],
        "rez-executable": {"windows":"usdview_gui.bat", "linux":"usdview_gui", "darwin":"usdview_gui"},
        "icon": os.path.join(ADDON_ROOT, "icons", "usd.png")
    },
    "Open Rv": {
        "rez-request": ["openrv"],
        "rez-executable": {"windows":"rv.exe", "linux":"rv", "darwin":"rv"},
        "icon": os.path.join(ADDON_ROOT, "icons", "rv.png")
    },
    "QuiltiX": {
        "rez-request": ["QuiltiX"],
        "rez-executable": {"windows": "QuiltiX.bat", "linux": "", "darwin": ""},
        "icon": os.path.join(ADDON_ROOT, "icons", "quiltix.png")
    },
}
