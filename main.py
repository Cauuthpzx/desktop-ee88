"""
main.py — Entry point
"""
import sys
import os
import ctypes

# PHẢI set trước khi tạo QApplication — icon taskbar Windows
myappid = "maxhub.app.1.0"
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from core import theme
from core.app_window import AppWindow
from dialogs.login_window import LoginWindow
from widgets.tooltip import install as install_tooltip
from utils.auth import auth

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def icon(name: str) -> QIcon:
    ico = os.path.join(BASE_DIR, "icons", "app", f"{name}.ico")
    svg = os.path.join(BASE_DIR, "icons", "app", f"{name}.svg")
    return QIcon(ico) if os.path.exists(ico) else QIcon(svg)


def main():
    app = QApplication(sys.argv)
    theme.apply(app)
    install_tooltip(app)

    # Tạo bảng users nếu chưa có
    auth.init()

    icon_taskbar  = icon("icon-taskbar")   # Hex + M
    icon_titlebar = icon("icon-titlebar")  # Shield
    icon_tray     = icon("icon-tray")      # Rounded square hub

    app.setWindowIcon(icon_taskbar)        # taskbar

    window = AppWindow()
    window.setWindowIcon(icon_titlebar)    # titlebar

    # System tray
    tray = QSystemTrayIcon(icon_tray, app)
    tray_menu = QMenu()
    tray_menu.addAction("Show", window.show)
    tray_menu.addAction("Hide", window.hide)
    tray_menu.addSeparator()
    tray_menu.addAction("Exit", app.quit)
    tray.setContextMenu(tray_menu)
    tray.setToolTip("MaxHub")

    # Login window — hien truoc AppWindow
    login = LoginWindow()
    login.setWindowIcon(icon_titlebar)

    def on_login_success(username: str) -> None:
        login.hide()
        window.show()
        tray.show()

    login.login_success.connect(on_login_success)
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
