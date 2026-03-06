"""
utils/settings.py
Lưu / đọc cấu hình ứng dụng bằng QSettings (registry trên Windows, file trên Mac/Linux).

Dùng:
    from utils.settings import settings

    # Lưu
    settings.set("window/width",  800)
    settings.set("window/height", 600)
    settings.set("app/last_dir",  "/home/user/docs")

    # Đọc
    w = settings.get("window/width",  default=960)
    h = settings.get("window/height", default=640)

    # Lưu/khôi phục kích thước cửa sổ tự động:
    settings.save_window(window)     # gọi trong closeEvent
    settings.restore_window(window)  # gọi sau show()
"""
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QMainWindow


# Tên app và tổ chức — đổi theo dự án
_ORG  = "MyCompany"
_APP  = "MyApp"


class AppSettings:
    def __init__(self):
        self._s = QSettings(_ORG, _APP)

    def set(self, key: str, value) -> None:
        self._s.setValue(key, value)

    def get(self, key: str, default=None):
        return self._s.value(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(self._s.value(key, default))
        except (TypeError, ValueError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = self._s.value(key, default)
        if isinstance(val, bool):
            return val
        return str(val).lower() in ("true", "1", "yes")

    def get_str(self, key: str, default: str = "") -> str:
        return str(self._s.value(key, default) or default)

    def remove(self, key: str) -> None:
        self._s.remove(key)

    def clear(self) -> None:
        self._s.clear()

    def all_keys(self) -> list[str]:
        return self._s.allKeys()

    # ── Window helpers ────────────────────────────────────
    def save_window(self, window: QMainWindow) -> None:
        """Lưu vị trí và kích thước cửa sổ. Gọi trong closeEvent."""
        self._s.setValue("window/geometry", window.saveGeometry())
        self._s.setValue("window/state",    window.saveState())

    def restore_window(self, window: QMainWindow) -> None:
        """Khôi phục vị trí và kích thước. Gọi sau show()."""
        geo   = self._s.value("window/geometry")
        state = self._s.value("window/state")
        if geo:
            window.restoreGeometry(geo)
        if state:
            window.restoreState(state)

    # ── Recent files ──────────────────────────────────────
    def add_recent_file(self, path: str, max_count: int = 10) -> None:
        recent = self.get_recent_files()
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self._s.setValue("recent_files", recent[:max_count])

    def get_recent_files(self) -> list[str]:
        val = self._s.value("recent_files", [])
        return val if isinstance(val, list) else [val] if val else []

    def clear_recent_files(self) -> None:
        self._s.remove("recent_files")


# Singleton — dùng trực tiếp trong toàn app
settings = AppSettings()
