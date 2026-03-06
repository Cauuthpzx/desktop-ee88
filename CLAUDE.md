# CLAUDE.md — PyQt6 Desktop App Template

---

## WINDOWS: TÊN FILE CẤM TUYỆT ĐỐI

Không bao giờ tạo file/folder với tên: `CON PRN AUX NUL COM1-9 LPT1-9`
Kể cả có extension: `nul.py`, `con.json`, `aux.log` — đều bị cấm.
Ký tự cấm trong tên file: `< > : " / \ | ? *`

Thay thế: `null_handler.py`, `console_utils.py`, `auxiliary.py`

---

## CẤU TRÚC DỰ ÁN

```
project/
├── main.py              # Entry point — SetCurrentProcessExplicitAppUserModelID + theme.apply(app)
├── icons/
│   ├── app/             # App icons: icon-taskbar.*, icon-titlebar.*, icon-tray.*
│   ├── layui/           # 184 icon SVG từ Layui (home.svg, edit.svg, delete.svg...)
│   └── material/        # 2100+ Google Material SVG (menu.svg, menu_open.svg...)
├── core/
│   ├── theme.py         # Tất cả constants: FONT_*, SPACING_*, MARGIN_*, sizing
│   ├── base_widgets.py  # BaseTab, BaseDialog, vbox(), hbox(), form_layout(), group(), divider()
│   └── app_window.py    # AppWindow(QMainWindow): menu + toolbar + tabs
├── tabs/                # Mỗi tab 1 file, kế thừa BaseTab
├── dialogs/             # Shared dialogs — dùng lại, không tự viết
├── widgets/             # Shared custom widgets — dùng lại, không tự viết
├── utils/               # db, settings, validators, formatters, table_helper, thread_worker
└── data/                # SQLite (tự tạo lần đầu chạy)
```

**Import flow một chiều:**
```
core/theme → core/base_widgets → utils → widgets / dialogs → tabs → core/app_window → main
```
Tab không import tab khác. Circular import = fix ngay.

---

## QUY TẮC BẮT BUỘC

### Windows taskbar icon
Phải gọi `SetCurrentProcessExplicitAppUserModelID` **TRƯỚC** khi tạo `QApplication` — đã có trong `main.py`:
```python
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myapp.id.1.0")
app = QApplication(sys.argv)  # sau đó mới tạo
```
Thiếu dòng này → icon taskbar KHÔNG hiện trên Windows.

### Styling — KHÔNG hardcode bất cứ thứ gì
```python
# SAI
layout.setSpacing(8)
widget.setStyleSheet("padding: 10px; font-size: 12pt;")

# ĐÚNG — dùng constants từ core/theme.py
from core import theme
layout.setSpacing(theme.SPACING_MD)      # 8
layout.setContentsMargins(*theme.MARGIN_DEFAULT)  # (10,10,10,10)
```

Constants có sẵn trong `core/theme.py`:
- `FONT_SIZE, FONT_SIZE_SM, FONT_SIZE_LG, FONT_SIZE_XL`
- `SPACING_XS=2, SPACING_SM=4, SPACING_MD=8, SPACING_LG=16, SPACING_XL=24`
- `MARGIN_DEFAULT=(10,10,10,10)`, `MARGIN_ZERO=(0,0,0,0)`, `MARGIN_DIALOG=(16,16,16,16)`
- `INPUT_HEIGHT=26, BUTTON_HEIGHT=28, TOOLBAR_HEIGHT=36, SIDEBAR_WIDTH=200`
- `WINDOW_MIN_W=960, WINDOW_MIN_H=640`

### Kích thước widget
- KHÔNG `setFixedHeight` / `setFixedWidth` cho `QPushButton`, `QLineEdit`, `QComboBox`, `QSpinBox`
- Fusion tự tính theo font — muốn to hơn thì tăng `FONT_SIZE` trong `core/theme.py`
- Chỉ set size khi thực sự cần: icon-only button, thumbnail, preview panel

### Layout — dùng factories từ `core/base_widgets.py`
```python
from core.base_widgets import vbox, hbox, form_layout, group, divider

# KHÔNG làm thế này:
lay = QVBoxLayout()
lay.setSpacing(8)
lay.setContentsMargins(10, 10, 10, 10)

# Làm thế này:
lay = vbox()          # spacing=SPACING_MD, margins=MARGIN_DEFAULT
lay = hbox(spacing=theme.SPACING_SM, margins=theme.MARGIN_ZERO)
lay = form_layout()   # QFormLayout, label AlignRight
grp, g = group("Tiêu đề", "vbox")  # trả về (QGroupBox, layout)
```

### Widget
- Tab mới → kế thừa `BaseTab` từ `core/base_widgets.py`, override `_build(layout)`
- Dialog mới → kế thừa `BaseDialog` từ `core/base_widgets.py`, override `_build_form()`, `_fill()`, `get_data()`
- Dùng `label()`, `section_label()`, `group()`, `divider()`, `scroll_tab()` từ `core/base_widgets.py`
- **Không tự viết lại** component đã có trong `widgets/`, `dialogs/`, `utils/`

---

## SHARED COMPONENTS — DÙNG NGAY

### dialogs/
| File | Dùng khi |
|------|----------|
| `confirm_dialog.py` | Xác nhận, alert, warn, error, success |
| `input_dialog.py` | Hỏi text / số / lựa chọn nhanh |
| `file_dialog.py` | Mở file, lưu file, chọn thư mục |
| `form_dialog.py` | Dialog form linh hoạt truyền fields vào |
| `about_dialog.py` | Dialog "Về ứng dụng" |

```python
from dialogs.confirm_dialog import confirm, alert, warn, error, success, confirm_delete
from dialogs.input_dialog   import get_text, get_int, get_float, get_choice
from dialogs.file_dialog    import open_file, save_file, open_files, open_folder
from dialogs.form_dialog    import FormDialog
from dialogs.about_dialog   import AboutDialog
```

### widgets/
| File | Widget | Dùng khi |
|------|--------|----------|
| `stat_card.py` | `StatCard` | Thẻ thống kê trên dashboard |
| `search_bar.py` | `SearchBar` | Thanh tìm kiếm có nút clear |
| `badge.py` | `Badge`, `StatusBadge` | Nhãn trạng thái nhỏ |
| `empty_state.py` | `EmptyState` | Hiển thị khi không có dữ liệu |
| `loading.py` | `LoadingBar`, `LoadingOverlay` | Hiệu ứng đang tải |
| `breadcrumb.py` | `Breadcrumb` | Đường dẫn điều hướng |
| `pagination.py` | `Pagination` | Phân trang (có `offset()` cho SQL) |
| `toolbar_widget.py` | `ContentToolbar` | Toolbar trong tab (Thêm/Sửa/Xoá + Search) |
| `form_widget.py` | `FormWidget` | Form nhúng trong tab (không phải dialog) |
| `table_crud.py` | `TableCrud` | Table đầy đủ: toolbar + search + table + pagination + empty state |
| `sidebar.py` | `CollapsibleSidebar` | Sidebar nav đóng/mở thay QTabWidget |

```python
from widgets.stat_card      import StatCard
from widgets.search_bar     import SearchBar
from widgets.badge          import Badge, StatusBadge
from widgets.empty_state    import EmptyState
from widgets.loading        import LoadingBar, LoadingOverlay
from widgets.breadcrumb     import Breadcrumb
from widgets.pagination     import Pagination
from widgets.toolbar_widget import ContentToolbar
from widgets.form_widget    import FormWidget
from widgets.table_crud     import TableCrud
from widgets.sidebar        import CollapsibleSidebar
```

### Thêm menu item vào sidebar

Sửa list `MENU` trong `core/app_window.py`:
```python
MENU = [
    {"icon": "icons/layui/home.svg",  "text": "Trang chu", "tab": HomeTab},
    None,  # separator
    {"icon": "icons/layui/user.svg",  "text": "Nhan vien", "tab": NhanVienTab},
    {"icon": "icons/layui/set.svg",   "text": "Cai dat",   "tab": CaiDatTab},
]
```
Moi entry la dict `{icon, text, tab}`. `None` = separator. Thu tu = thu tu hien thi.

### utils/
| File | Import | Dùng khi |
|------|--------|----------|
| `validators.py` | `required, email, phone, positive, validate_all` | Validate form trước khi lưu |
| `formatters.py` | `currency, number, date_str, phone_fmt, truncate, yesno` | Format để hiển thị |
| `table_helper.py` | `setup_table, load_table, get_selected_id, set_column_width` | Thao tác QTableWidget |
| `db.py` | `Database` | Kết nối và truy vấn SQLite |
| `settings.py` | `settings` | Lưu/đọc cấu hình app |
| `thread_worker.py` | `Worker, run_in_thread` | Chạy task nặng không đơ UI |

```python
from utils.validators    import required, email, phone, positive, validate_all
from utils.formatters    import currency, number, date_str, phone_fmt, truncate, yesno
from utils.table_helper  import setup_table, load_table, get_selected_id, set_column_width
from utils.db            import Database
from utils.settings      import settings
from utils.thread_worker import Worker, run_in_thread
```

---

## ICONS — 3 THƯ MỤC

### `icons/app/` — App icons
Chứa `icon-taskbar.*`, `icon-titlebar.*`, `icon-tray.*` (SVG + ICO + PNG các kích thước).
Dùng trong `main.py` — **không sửa path trong code khác**.

### `icons/layui/` — 184 SVG Layui
Dùng cho sidebar nav, toolbar, button — `fill="currentColor"` tự theo QPalette.

```python
from PyQt6.QtGui import QIcon

btn.setIcon(QIcon("icons/layui/home.svg"))
action = QAction(QIcon("icons/layui/edit.svg"), "Sửa", self)
```

Icon thường dùng:

| Icon file | Ý nghĩa |
|-----------|---------|
| `add-circle.svg` | Thêm mới |
| `edit.svg` | Sửa |
| `delete.svg` | Xoá |
| `search.svg` | Tìm kiếm |
| `refresh.svg` | Làm mới |
| `download-circle.svg` | Tải xuống / export |
| `upload.svg` | Tải lên / import |
| `home.svg` | Trang chủ |
| `user.svg` | Người dùng |
| `set.svg` | Cài đặt |
| `eye.svg` / `eye-invisible.svg` | Hiện / ẩn |
| `ok-circle.svg` | Thành công |
| `close-fill.svg` | Đóng / lỗi |
| `notice.svg` | Thông báo |
| `chart.svg` | Báo cáo / thống kê |
| `table.svg` | Danh sách / bảng |
| `export.svg` | Xuất file |
| `print.svg` | In |
| `log.svg` | Nhật ký |
| `key.svg` | Bảo mật / mật khẩu |

### `icons/material/` — 2100+ Google Material SVG
Bộ icon lớn hơn, dùng khi Layui không có icon phù hợp.
Sidebar toggle dùng `icons/material/menu.svg` và `icons/material/menu_open.svg`.

```python
QIcon("icons/material/menu.svg")
QIcon("icons/material/settings.svg")
```

### `icons/gallery/` — Gallery custom icons
Ported từ gallery project. Mỗi icon có 2 variant: `_black.svg` (light theme) và `_white.svg` (dark theme).
Thư mục `controls/` chứa 98 PNG thumbnail của các widget control.

**Dùng trực tiếp:**
```python
QIcon("icons/gallery/Grid_black.svg")
```

**Dùng qua Enum registry (`core/icon.py`):**
```python
from core.icon import GalleryIcon

btn.setIcon(GalleryIcon.GRID.icon())          # light theme (black)
btn.setIcon(GalleryIcon.GRID.icon(dark=True)) # dark theme (white)
```

Gallery icons có sẵn: `GRID`, `MENU`, `TEXT`, `PRICE`, `EMOJI_TAB_SYMBOLS`

---

## THREADING — QUY TẮC QUAN TRỌNG NHẤT

**Main thread = chỉ vẽ UI.** Bất kỳ blocking call nào ở đây = app đơ.

Mọi thao tác có thể > 50ms đều chạy trong background: file I/O, DB query, API call, tính toán nặng.

**Dùng `run_in_thread` từ `utils/thread_worker.py`:**

```python
from utils.thread_worker import run_in_thread
from widgets.loading     import LoadingOverlay

self._loading = LoadingOverlay(self)

run_in_thread(
    lambda: db.fetchall("SELECT * FROM bang_lon"),
    on_result=lambda data: self.crud.load(data, keys=["id", "ten"]),
    on_error=lambda e: error(self.window(), str(e)),
    on_finished=self._loading.stop,
)
self._loading.start("Đang tải...")
```

**Dùng `Worker` khi cần progress:**
```python
from utils.thread_worker import Worker

def xu_ly(progress_callback):
    for i in range(100):
        # ... làm việc ...
        progress_callback(i)

worker = Worker(xu_ly, use_progress=True)
worker.signals.progress.connect(self.progress_bar.setValue)
worker.signals.result.connect(self._on_done)
worker.signals.error.connect(lambda e: error(self, e))
worker.start()
```

**Không bao giờ:**
- Update UI trực tiếp từ worker — chỉ emit signal
- Dùng `time.sleep()` trong main thread
- Tạo `QThread` mới cho mỗi task

**Cleanup:** Disconnect signals trong `closeEvent()` để tránh memory leak.

---

## ERROR HANDLING

```python
# SAI — app âm thầm sai
try:
    result = load_data()
except Exception:
    pass

# ĐÚNG — log + thông báo user
try:
    result = load_data()
except (FileNotFoundError, PermissionError) as e:
    logger.error("load_data failed: %s", e, exc_info=True)
    error(self.window(), f"Không thể tải dữ liệu: {e}")
    return
```

- Catch tại tầng tab/controller — utils/service chỉ raise
- Log đầy đủ: exception type, message, stack trace
- Hiển thị message thân thiện, không technical detail
- Rollback state nếu operation thất bại giữa chừng

---

## SECURITY

```python
# SAI — SQL injection
db.execute(f"SELECT * FROM users WHERE name = '{name}'")

# ĐÚNG — parameterized query
db.execute("SELECT * FROM users WHERE name = ?", (name,))
```
- Validate mọi input trước khi dùng (dùng `validators.py`)
- Không log password, token, thông tin nhạy cảm

---

## CODE PATTERNS

### Thêm tab mới (nhanh nhất)

```python
# tabs/quan_ly_kho.py
from PyQt6.QtWidgets import QLineEdit, QSpinBox, QDialog
from core.base_widgets import BaseTab, BaseDialog, label, divider
from core import theme
from widgets.table_crud import TableCrud
from dialogs.confirm_dialog import confirm_delete, warn
from utils.validators import validate_all, required

class KhoDialog(BaseDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent, title="Thêm / Sửa hàng hóa",
                         min_width=380, data=data)

    def _build_form(self, form):
        self.ten_edit = QLineEdit()
        self.sl_spin  = QSpinBox(); self.sl_spin.setRange(0, 99999)
        form.addRow("Tên hàng:", self.ten_edit)
        form.addRow("Số lượng:", self.sl_spin)

    def _fill(self, data: dict):
        self.ten_edit.setText(data.get("ten", ""))
        self.sl_spin.setValue(data.get("so_luong", 0))

    def get_data(self) -> dict:
        return {"ten": self.ten_edit.text().strip(),
                "so_luong": self.sl_spin.value()}


class QuanLyKhoTab(BaseTab):
    def _build(self, layout):
        layout.addWidget(label("Quản lý kho", bold=True, size=theme.FONT_SIZE_LG))
        layout.addWidget(divider())

        self.crud = TableCrud(
            columns=["ID", "Tên hàng", "Số lượng"],
            on_add=self._on_add,
            on_edit=self._on_edit,
            on_delete=self._on_delete,
            on_search=self._on_search,
        )
        layout.addWidget(self.crud)
        self._reload()

    def _reload(self, q=""):
        data = []  # db.fetchall("SELECT id, ten, so_luong FROM hang_hoa WHERE ten LIKE ?", (f"%{q}%",))
        self.crud.load(data, keys=["id", "ten", "so_luong"])

    def _on_add(self):
        dlg = KhoDialog(self.window())
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        errors = validate_all([required("Tên hàng", data["ten"])])
        if errors:
            warn(self.window(), "\n".join(errors)); return
        # db.execute("INSERT INTO hang_hoa (ten, so_luong) VALUES (?, ?)", ...)
        self._reload()

    def _on_edit(self):
        id_ = self.crud.selected_id()
        if not id_: return
        rec = {}  # db.fetchone("SELECT * FROM hang_hoa WHERE id = ?", (id_,))
        dlg = KhoDialog(self.window(), data=rec)
        if dlg.exec() != QDialog.DialogCode.Accepted: return
        # db.execute("UPDATE hang_hoa SET ten=?, so_luong=? WHERE id=?", ...)
        self._reload()

    def _on_delete(self):
        id_ = self.crud.selected_id()
        if id_ and confirm_delete(self.window()):
            # db.execute("DELETE FROM hang_hoa WHERE id = ?", (id_,))
            self._reload()

    def _on_search(self, text: str):
        self._reload(q=text)
```

Sau đó trong `core/app_window.py`:
```python
from tabs.quan_ly_kho import QuanLyKhoTab
self.tabs.addTab(QuanLyKhoTab(), "Kho hàng")
```

### Background task với loading

```python
from utils.thread_worker import run_in_thread
from widgets.loading import LoadingOverlay
from dialogs.confirm_dialog import error

class MyTab(BaseTab):
    def _build(self, layout):
        self._loading = LoadingOverlay(self)
        # ...

    def _load_data(self):
        run_in_thread(
            lambda: db.fetchall("SELECT * FROM bang"),
            on_result=self._on_data,
            on_error=lambda e: error(self.window(), str(e)),
            on_finished=self._loading.stop,
        )
        self._loading.start("Đang tải...")

    def _on_data(self, data):
        self.crud.load(data, keys=["id", "ten"])
```

### Lưu/phục hồi cửa sổ — đã tích hợp trong AppWindow
```python
# core/app_window.py đã có sẵn:
def show(self):
    super().show()
    settings.restore_window(self)

def closeEvent(self, event):
    settings.save_window(self)
    super().closeEvent(event)
```

---

## PYTHON STANDARDS

**Naming:**
- Files/folders: `lowercase_with_underscores`
- Classes: `PascalCase` | Functions/methods: `snake_case` | Constants: `UPPER_SNAKE_CASE`
- Private: `_single_underscore` — không truy cập `_private` của class khác từ bên ngoài

**Code quality:**
- Type hints cho tất cả function signatures
- `@dataclass(frozen=True)` cho data models bất biến
- `pathlib.Path` thay `os.path`
- Early return thay vì if/else lồng sâu
- Specific exceptions — không dùng bare `except:`
- `__slots__` và `@dataclass` không dùng chung (incompatible — chọn một)

**Memory:**
- Disconnect signals trong `closeEvent()` / `cleanup()` — tránh memory leak
- `del` objects lớn ngay sau khi dùng xong
- `weakref` cho cache và observer pattern

---

## EXCEL EXPORT (xlsxwriter)

```python
# SAI — ghi mọi ô, file ~6MB
for row in range(32000):
    for col in range(60):
        worksheet.write(row, col, value, cell_format)

# ĐÚNG — set column format 1 lần, chỉ ghi ô có data → file ~2MB
worksheet.set_column(0, 59, width, cell_format)  # áp dụng cho ô trống trong column
for row_idx, row in enumerate(data_rows):
    for col, value in row.items():
        if value is not None:
            worksheet.write(row_idx, col, value)
# Ô trống inherit format từ column — có border mà không tốn dung lượng
# Kết quả: giảm 60-70% file size với data có nhiều ô trống
```

---

## COMMON MISTAKES

| Sai | Đúng |
|-----|------|
| I/O trong main thread | Dùng `run_in_thread()` |
| Update UI từ worker thread | Emit signal, để main thread xử lý |
| `except: pass` | Log + `error(self.window(), ...)` |
| Tự viết toolbar + table từ đầu | Dùng `TableCrud` |
| Tự viết `QMessageBox.question(...)` | Dùng `confirm_delete()` |
| Tự viết validate if/else | Dùng `validate_all([required(...)])` |
| `setFixedWidth` trên widget chuẩn | Bỏ — Fusion tự tính |
| Hardcode `8`, `(10,10,10,10)`, `"Segoe UI"` | Dùng `theme.SPACING_MD`, `theme.MARGIN_DEFAULT` |
| `from core.base_widgets import *` không dùng | Import đúng tên cần |
| Truy cập `obj._attr` từ class khác | Tạo public method trên class đó |
| `QFrame.StyledPanel` ra màu trắng | Bỏ + thêm `WA_TranslucentBackground` |
| Unicode icon không hiện | Dùng file `.svg` từ `icons/layui/` hoặc `icons/material/` |
| Thiếu `SetCurrentProcessExplicitAppUserModelID` | Đã có trong `main.py` — đừng xoá |
| Dialog About dùng `QMessageBox.about()` | Dùng `AboutDialog` từ `dialogs/about_dialog.py` |

---

## CHECKLIST KHI THÊM TAB MỚI

```
[ ] Tạo file trong tabs/, kế thừa BaseTab
[ ] Dialog kế thừa BaseDialog (nếu cần form)
[ ] Dùng TableCrud thay vì tự lắp toolbar + table
[ ] Validate qua validate_all() trước khi lưu
[ ] confirm_delete() trước khi xoá
[ ] I/O chạy trong run_in_thread(), dùng LoadingOverlay
[ ] Không import tab/feature khác
[ ] Đăng ký tab trong core/app_window.py
[ ] Test: UI không đơ khi load data lớn
[ ] Test: app đóng sạch, không có hanging thread
```

---

## REFERENCE

| Metric | Giá trị | Ghi chú |
|--------|---------|---------|
| UI block threshold | 50ms | Hơn → worker thread |
| `SPACING_XS/SM/MD/LG/XL` | 2/4/8/16/24px | Dùng từ `core/theme.py` |
| `MARGIN_DEFAULT` | (10,10,10,10) | Dùng `*theme.MARGIN_DEFAULT` |
| `FONT_SIZE` | 10pt | Base font Segoe UI |
| Debounce search | 300ms | SearchBar đã tự xử lý |
| API timeout | 15-30s | Tuỳ operation |
| Retry | 3 lần | Backoff: 1s → 2s → 4s |
| Thread pool | 4-8 threads | `QThread.idealThreadCount()` |
| Toast / alert duration | 3-5s | Auto-dismiss nếu có |
| Pagination default | 20 items/page | `TableCrud(page_size=20)` |
