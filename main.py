"""
main.py — Entry point
"""
import sys
import os
import ctypes

# PyInstaller --onedir: chuyen working dir ve thu muc chua exe
# de tat ca relative path (icons/, i18n/) hoat dong dung
if getattr(sys, "frozen", False):
    os.chdir(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))

# PHẢI set trước khi tạo QApplication — icon taskbar Windows
myappid = "maxhub.app.1.0"
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from core import theme
from core.i18n import init as init_i18n, t
from core.app_window import AppWindow
from dialogs.login_window import LoginWindow
from widgets.tooltip import install as install_tooltip
from utils.api import api
from utils.auth import auth
from utils.settings import settings
from utils.thread_worker import run_in_thread
from utils.updater import APP_VERSION
from utils.ws_client import ws_client
from monitoring import MonitoringManager

if getattr(sys, "frozen", False):
    BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def icon(name: str) -> QIcon:
    ico = os.path.join(BASE_DIR, "icons", "app", f"{name}.ico")
    svg = os.path.join(BASE_DIR, "icons", "app", f"{name}.svg")
    return QIcon(ico) if os.path.exists(ico) else QIcon(svg)


def main():
    app = QApplication(sys.argv)
    theme.apply(app)
    init_i18n()
    install_tooltip(app)

    from core.icon import _connect_theme_signal
    _connect_theme_signal()

    # Init API signals (phai sau QApplication)
    api.init_signals()

    # Monitoring — crash reporter + health checker + audit trail
    monitor = MonitoringManager(app_version=APP_VERSION)
    monitor.start()
    app.aboutToQuit.connect(monitor.shutdown)

    # Tạo bảng users nếu chưa có (background — không block UI)
    run_in_thread(auth.init)

    icon_taskbar  = icon("icon-taskbar")   # Hex + M
    icon_titlebar = icon("icon-titlebar")  # Shield
    icon_tray     = icon("icon-tray")      # Rounded square hub

    app.setWindowIcon(icon_taskbar)        # taskbar

    window = AppWindow()
    window.setWindowIcon(icon_titlebar)    # titlebar

    # System tray
    tray = QSystemTrayIcon(icon_tray, app)
    tray_menu = QMenu()
    tray_menu.addAction(t("menu.show"), window.show)
    tray_menu.addAction(t("menu.hide"), window.hide)
    tray_menu.addSeparator()
    tray_menu.addAction(t("menu.exit"), app.quit)
    tray.setContextMenu(tray_menu)
    tray.setToolTip(t("app.tray_tooltip"))

    # Login window — hien truoc AppWindow
    login = LoginWindow()
    login.setWindowIcon(icon_titlebar)

    def on_login_success(username: str) -> None:
        login.hide()
        window.show()
        tray.show()
        monitor.log_action("auth", "login", f"user={username}")
        # Sync agents + cookies tu DB xuong local (background, khong block)
        from utils.upstream import upstream
        from utils.thread_worker import run_in_thread
        run_in_thread(lambda: upstream.sync_from_db(username))
        # Connect WebSocket
        ws_client.connect()

    login.login_success.connect(on_login_success)

    def on_logout() -> None:
        monitor.log_action("auth", "logout")
        ws_client.disconnect()
        window.hide()
        tray.hide()
        login.show()

    auth.logged_out.connect(on_logout)

    # Session expired: token het han + refresh fail → force logout ngay
    api.session_expired.connect(auth.logout)

    # Auto-login: neu co session luu tu truoc, verify token trong background
    if settings.get_bool("login/remember") and settings.get_str("session/token"):
        # Show window ngay (khong block), verify token trong background
        window.show()
        tray.show()

        def _try_restore():
            ok = api.restore_session()
            if ok and api.username:
                # Sync agents trong cung worker thread (da o background)
                from utils.upstream import upstream
                upstream.sync_from_db(api.username)
            return ok

        def _on_restore_result(ok):
            if ok:
                ws_client.connect()
            else:
                # Token het han — quay ve login
                window.hide()
                tray.hide()
                login.show()

        run_in_thread(
            _try_restore,
            on_result=_on_restore_result,
            on_error=lambda e: (window.hide(), tray.hide(), login.show()),
        )
    else:
        login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
