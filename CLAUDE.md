# CLAUDE.md — MaxHub Desktop App (Online)

App desktop PyQt6 ket noi API server (FastAPI + PostgreSQL).
Desktop app KHONG truy cap DB truc tiep — moi thao tac qua HTTP API.

---

## WINDOWS: TEN FILE CAM

Khong tao file/folder ten: `CON PRN AUX NUL COM1-9 LPT1-9`
Ke ca co extension: `nul.py`, `con.json` — deu bi cam.
Ky tu cam: `< > : " / \ | ? *`
Thay the: `null_handler.py`, `console_utils.py`, `auxiliary.py`

---

## CAU TRUC DU AN

```
project/
├── main.py              # Entry point — login flow → AppWindow
├── .env                 # API_URL + DB config (gitignored)
├── .env.example         # Template .env
├── server/              # FastAPI backend (ban local cua code tren VPS)
│   ├── main.py          # FastAPI app: auth endpoints, JWT, PostgreSQL
│   └── .env.example     # Server env template
├── icons/
│   ├── app/             # icon-taskbar.*, icon-titlebar.*, icon-tray.*, login-bg.svg
│   ├── layui/           # 184 SVG Layui (fill="currentColor")
│   ├── material/        # 2100+ Google Material SVG
│   └── gallery/         # Custom icons: *_black.svg + *_white.svg, controls/ thumbnails
├── core/
│   ├── theme.py         # FONT_*, SPACING_*, MARGIN_*, sizing constants
│   ├── base_widgets.py  # BaseTab, BaseDialog, vbox(), hbox(), form_layout(), group(), divider()
│   ├── app_window.py    # AppWindow(QMainWindow): toolbar + sidebar + stacked tabs
│   └── icon.py          # GalleryIcon enum registry
├── tabs/                # Moi tab 1 file, ke thua BaseTab
├── dialogs/
│   ├── login_window.py  # LoginWindow: dang nhap / dang ky (hien truoc AppWindow)
│   └── ...              # Shared dialogs
├── widgets/             # Shared custom widgets
└── utils/
    ├── api.py           # HTTP client goi API server (ApiClient singleton)
    ├── db.py            # PostgreSQL wrapper (psycopg v3 — dung cho local dev/direct DB)
    ├── auth.py          # AuthService: init(), login(), register() — goi qua api.py
    ├── settings.py      # QSettings wrapper
    ├── validators.py    # required, email, phone, min_length, validate_all
    ├── formatters.py    # currency, number, date_str, phone_fmt, truncate
    ├── table_helper.py  # setup_table, load_table, get_selected_id
    ├── thread_worker.py # Worker, run_in_thread
    └── updater.py       # Auto update: check_update, download_update, apply_update
```

**Import flow mot chieu:**
```
core/theme → core/base_widgets → utils → widgets / dialogs → tabs → core/app_window → main
```
Tab khong import tab khac. Circular import = fix ngay.

---

## KIEN TRUC

```
Desktop App (PyQt6)  ──HTTP──>  API Server (FastAPI)  ──SQL──>  PostgreSQL
   utils/api.py                  server/main.py                  VPS database
   utils/auth.py                 JWT + bcrypt
```

- Desktop app chi goi HTTP endpoints qua `utils/api.py`
- Server xu ly auth (bcrypt hash, JWT token), business logic
- DB credentials chi nam tren server, KHONG trong desktop app
- `server/` la ban local cua code deploy tren VPS — sua o day roi upload len VPS

### VPS Info
- IP: `42.96.20.12` | User: `root` | OS: Ubuntu 22.04
- PostgreSQL 14 chay local tren VPS
- FastAPI chay qua systemd: `maxhub-api.service`
- API port: `8000` | DB port: `5432`
- Project dir tren VPS: `/opt/maxhub-api/`
- Deploy: upload `server/main.py` len VPS qua SFTP, restart service

---

## APP FLOW

```
main.py
  ├── SetCurrentProcessExplicitAppUserModelID (TRUOC QApplication)
  ├── QApplication + theme.apply(app) + install_tooltip(app)
  ├── auth.init()  → health check API server
  ├── LoginWindow.show()
  │     ├── Dang nhap thanh cong → login_success.emit(username)
  │     └── Dang ky → chuyen sang form register → thanh cong → quay lai login
  └── on_login_success:
        ├── LoginWindow.hide()
        ├── AppWindow.show()
        └── SystemTray.show()
```

**LoginWindow** (`dialogs/login_window.py`):
- QStackedWidget chua _LoginForm va _RegisterForm
- Auth chay trong worker thread (khong block UI)
- Remember me luu qua `utils/settings.py`
- Emit `login_success(username)` khi dang nhap thanh cong

---

## API CLIENT — utils/api.py

Desktop app goi server qua HTTP. `.env`:
```
API_URL=http://42.96.20.12:8000
```

### Su dung
```python
from utils.api import api

# Auth (KHONG can token)
ok, msg = api.register("admin", "123456")
ok, msg = api.login("admin", "123456")   # luu token tu dong
api.logout()

# Goi API (tu dong gui Bearer token)
ok, data = api.get("/api/users")
ok, data = api.post("/api/users", {"name": "Alice"})
ok, data = api.put("/api/users/1", {"name": "Bob"})
ok, data = api.delete("/api/users/1")

# Properties
api.is_logged_in   # bool
api.username        # str | None
api.role            # str | None
api.token           # str | None
```

### Auth service (wrapper)
```python
from utils.auth import auth

auth.init()                                    # health check server
ok, msg = auth.register("admin", "123456")     # POST /api/register
ok, msg = auth.login("admin", "123456")        # POST /api/login → luu JWT
auth.is_logged_in                              # bool
auth.username                                  # str | None
auth.role                                      # str | None
```

### Database (direct access — chi dung cho local dev)
```python
from utils.db import Database

with Database() as db:
    rows = db.fetchall("SELECT * FROM users WHERE role = %s", ("admin",))
```
Placeholder: `%s`. Ket qua: `dict`. Autocommit = True.

Bang `users`:
```sql
id BIGSERIAL PRIMARY KEY
username VARCHAR(100) UNIQUE NOT NULL
password_hash VARCHAR(255) NOT NULL
email VARCHAR(255)
role VARCHAR(50) DEFAULT 'user'
status VARCHAR(50) DEFAULT 'active'
token_version BIGINT DEFAULT 0
last_login_at TIMESTAMPTZ
last_login_ip VARCHAR(50)
created_at TIMESTAMPTZ DEFAULT NOW()
updated_at TIMESTAMPTZ DEFAULT NOW()
deleted_at TIMESTAMPTZ
```

---

## AUTO UPDATE — utils/updater.py

App tu dong kiem tra phien ban moi khi khoi dong (background thread).
Flow: `AppWindow.show()` → `check_update()` → hien dialog → `download_update()` → `apply_update()` → restart.

```python
from utils.updater import APP_VERSION, check_update, download_update, apply_update

# Kiem tra (trong worker thread)
info = check_update()  # GET /api/version, so sanh version
# info = {"version": "1.1.0", "update_url": "https://...", "force": False} hoac None

# Tai update (trong worker thread, co progress)
exe_path = download_update(info["update_url"], progress_callback=lambda pct: ...)

# Ap dung (main thread — se thoat app)
apply_update(exe_path)  # luu JWT session → tao .bat → restart
```

**Session persistence khi update:**
- `api.save_session()` luu JWT token vao QSettings truoc khi thoat
- `api.restore_session()` doc token tu QSettings khi khoi dong lai
- User KHONG bi logout sau khi update

**Server config** (VPS `/opt/maxhub-api/.env`):
```
APP_VERSION=1.0.0
UPDATE_URL=https://example.com/MaxHub_v1.1.0.exe
```

**Tang version khi release:**
1. Tang `APP_VERSION` trong `utils/updater.py` (client)
2. Tang `APP_VERSION` trong VPS `.env` (server) + dat `UPDATE_URL`
3. Restart service: `systemctl restart maxhub-api`

---

## QUY TAC BAT BUOC

### Windows taskbar icon
Phai goi `SetCurrentProcessExplicitAppUserModelID` **TRUOC** khi tao `QApplication` — da co trong `main.py`. Thieu = icon taskbar KHONG hien.

### Styling — KHONG hardcode
```python
# SAI
layout.setSpacing(8)
widget.setStyleSheet("padding: 10px; font-size: 12pt;")

# DUNG
from core import theme
layout.setSpacing(theme.SPACING_MD)
layout.setContentsMargins(*theme.MARGIN_DEFAULT)
```

Constants (`core/theme.py`):
- `FONT_SIZE=10, FONT_SIZE_SM=9, FONT_SIZE_LG=12, FONT_SIZE_XL=16`
- `SPACING_XS=2, SPACING_SM=4, SPACING_MD=8, SPACING_LG=16, SPACING_XL=24`
- `MARGIN_DEFAULT=(10,10,10,10)`, `MARGIN_ZERO=(0,0,0,0)`, `MARGIN_DIALOG=(16,16,16,16)`
- `INPUT_HEIGHT=26, BUTTON_HEIGHT=28, TOOLBAR_HEIGHT=36`
- `SIDEBAR_WIDTH=200, SIDEBAR_COLLAPSED_WIDTH=48, SIDEBAR_ANIM_MS=150`
- `WINDOW_MIN_W=960, WINDOW_MIN_H=640`

### Kich thuoc widget
- KHONG `setFixedHeight/Width` cho QPushButton, QLineEdit, QComboBox, QSpinBox
- Fusion tu tinh theo font
- Chi set size khi can: icon-only button, thumbnail, preview panel

### Layout — dung factories
```python
from core.base_widgets import vbox, hbox, form_layout, group, divider

lay = vbox()          # spacing=SPACING_MD, margins=MARGIN_DEFAULT
lay = hbox(spacing=theme.SPACING_SM, margins=theme.MARGIN_ZERO)
lay = form_layout()   # QFormLayout, label AlignRight
grp, g = group("Tieu de", "vbox")  # (QGroupBox, layout)
```

### Widget
- Tab moi → ke thua `BaseTab`, override `_build(layout)`
- Dialog moi → ke thua `BaseDialog`, override `_build_form()`, `_fill()`, `get_data()`
- Dung `label()`, `section_label()`, `group()`, `divider()`, `scroll_tab()`
- **Khong tu viet lai** component da co trong `widgets/`, `dialogs/`, `utils/`

---

## SHARED COMPONENTS

### dialogs/
| File | Dung khi |
|------|----------|
| `login_window.py` | Dang nhap / dang ky (hien truoc AppWindow) |
| `confirm_dialog.py` | Xac nhan, alert, warn, error, success |
| `input_dialog.py` | Hoi text / so / lua chon nhanh |
| `file_dialog.py` | Mo file, luu file, chon thu muc |
| `form_dialog.py` | Dialog form linh hoat truyen fields vao |
| `about_dialog.py` | Dialog "Ve ung dung" |

```python
from dialogs.login_window    import LoginWindow
from dialogs.confirm_dialog  import confirm, alert, warn, error, success, confirm_delete
from dialogs.input_dialog    import get_text, get_int, get_float, get_choice
from dialogs.file_dialog     import open_file, save_file, open_files, open_folder
from dialogs.form_dialog     import FormDialog
from dialogs.about_dialog    import AboutDialog
```

### widgets/
| File | Widget | Dung khi |
|------|--------|----------|
| `stat_card.py` | `StatCard` | The thong ke tren dashboard |
| `search_bar.py` | `SearchBar` | Thanh tim kiem co nut clear |
| `badge.py` | `Badge`, `StatusBadge` | Nhan trang thai nho |
| `empty_state.py` | `EmptyState` | Hien thi khi khong co du lieu |
| `loading.py` | `LoadingBar`, `LoadingOverlay` | Hieu ung dang tai |
| `breadcrumb.py` | `Breadcrumb` | Duong dan dieu huong |
| `pagination.py` | `Pagination` | Phan trang (co `offset()` cho SQL) |
| `toolbar_widget.py` | `ContentToolbar` | Toolbar trong tab (Them/Sua/Xoa + Search) |
| `form_widget.py` | `FormWidget` | Form nhung trong tab (khong phai dialog) |
| `table_crud.py` | `TableCrud` | Table day du: toolbar + search + table + pagination + empty state |
| `sidebar.py` | `CollapsibleSidebar` | Sidebar nav dong/mo (custom-painted, zero child widgets) |
| `tooltip.py` | `Tooltip`, `install` | Custom tooltip layui-vue style (arrow, shadow, fade) |

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
from widgets.tooltip        import Tooltip, install  # goi install(app) trong main.py
```

### Them menu item vao sidebar

Sua list `MENU` trong `core/app_window.py`:
```python
MENU = [
    {"icon": "icons/layui/home.svg",  "text": "Trang chu", "tab": HomeTab},
    None,  # separator
    {"icon": "icons/layui/user.svg",  "text": "Nhan vien", "tab": NhanVienTab},
    {"icon": "icons/layui/set.svg",   "text": "Cai dat",   "tab": CaiDatTab},
]
```
Moi entry: `{icon, text, tab}`. `None` = separator. Thu tu = thu tu hien thi.

### utils/
| File | Import | Dung khi |
|------|--------|----------|
| `api.py` | `api` | HTTP client goi API server (singleton) |
| `db.py` | `Database` | PostgreSQL direct (chi local dev) |
| `auth.py` | `auth` | Dang nhap, dang ky — goi qua api.py |
| `validators.py` | `required, email, phone, min_length, positive, validate_all` | Validate form truoc khi luu |
| `formatters.py` | `currency, number, date_str, phone_fmt, truncate, yesno` | Format de hien thi |
| `table_helper.py` | `setup_table, load_table, get_selected_id, set_column_width` | Thao tac QTableWidget |
| `settings.py` | `settings` | Luu/doc cau hinh app (QSettings) |
| `thread_worker.py` | `Worker, run_in_thread` | Chay task nang khong do UI |
| `updater.py` | `APP_VERSION, check_update, download_update, apply_update` | Auto update app |

---

## ICONS — 4 THU MUC

### `icons/app/` — App icons
`icon-taskbar.*`, `icon-titlebar.*`, `icon-tray.*`, `login-bg.svg`
Dung trong `main.py` — **khong sua path trong code khac**.

### `icons/layui/` — 184 SVG Layui
Sidebar nav, toolbar, button — `fill="currentColor"` tu theo QPalette.
```python
btn.setIcon(QIcon("icons/layui/home.svg"))
```

Icon thuong dung:
| Icon | Y nghia | | Icon | Y nghia |
|------|---------|---|------|---------|
| `add-circle.svg` | Them moi | | `home.svg` | Trang chu |
| `edit.svg` | Sua | | `user.svg` | Nguoi dung |
| `delete.svg` | Xoa | | `set.svg` | Cai dat |
| `search.svg` | Tim kiem | | `eye.svg` | Hien |
| `refresh.svg` | Lam moi | | `eye-invisible.svg` | An |
| `download-circle.svg` | Tai xuong | | `ok-circle.svg` | Thanh cong |
| `upload.svg` | Tai len | | `close-fill.svg` | Dong/loi |
| `chart.svg` | Thong ke | | `key.svg` | Bao mat |
| `table.svg` | Danh sach | | `notice.svg` | Thong bao |
| `export.svg` | Xuat file | | `log.svg` | Nhat ky |
| `print.svg` | In | | | |

### `icons/material/` — 2100+ Google Material SVG
Bo icon lon, dung khi Layui khong co.
Sidebar toggle: `icons/material/menu.svg` + `icons/material/menu_open.svg`

### `icons/gallery/` — Gallery custom icons
2 variant: `_black.svg` (light) va `_white.svg` (dark). Thu muc `controls/` chua 98 PNG thumbnail.
```python
# Truc tiep
QIcon("icons/gallery/Grid_black.svg")

# Qua Enum (core/icon.py)
from core.icon import GalleryIcon
btn.setIcon(GalleryIcon.GRID.icon())           # light
btn.setIcon(GalleryIcon.GRID.icon(dark=True))  # dark
```
Icons: `GRID`, `MENU`, `TEXT`, `PRICE`, `EMOJI_TAB_SYMBOLS`

---

## THREADING — QUY TAC QUAN TRONG NHAT

**Main thread = chi ve UI.** Bat ky blocking call nao = app do.

**TAT CA thao tac mang/DB deu PHAI chay trong worker thread** — day la app online, moi query di qua network.

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
self._loading.start("Dang tai...")
```

**Worker voi progress:**
```python
from utils.thread_worker import Worker

def xu_ly(progress_callback):
    for i in range(100):
        progress_callback(i)

worker = Worker(xu_ly, use_progress=True)
worker.signals.progress.connect(self.progress_bar.setValue)
worker.signals.result.connect(self._on_done)
worker.signals.error.connect(lambda e: error(self, e))
worker.start()
```

**Khong bao gio:**
- Update UI truc tiep tu worker — chi emit signal
- Dung `time.sleep()` trong main thread
- Tao `QThread` moi cho moi task
- Goi `Database()` truc tiep trong main thread (tru `auth.init()` luc khoi dong)

**Cleanup:** Disconnect signals trong `closeEvent()`.

---

## NETWORK & CONNECTION HANDLING

App goi API server qua HTTP — can xu ly mat ket noi:

```python
from utils.api import api
from utils.thread_worker import run_in_thread

def _load_data(self):
    run_in_thread(
        lambda: api.get("/api/data"),
        on_result=self._on_data,
        on_error=lambda e: error(self.window(), "Khong the ket noi may chu."),
        on_finished=self._loading.stop,
    )
    self._loading.start("Dang tai...")

def _on_data(self, result):
    ok, data = result
    if ok:
        self.crud.load(data, keys=["id", "ten"])
    else:
        error(self.window(), data.get("message", "Loi."))
```

**Xu ly loi mang:**
- Hien thi message than thien: "Khong the ket noi may chu" (khong hien technical detail)
- Retry 3 lan voi backoff: 1s → 2s → 3s
- Timeout: 15-30s tuy operation
- Mat ket noi giua chung → rollback + thong bao user

---

## ERROR HANDLING

```python
# SAI
try:
    result = load_data()
except Exception:
    pass

# DUNG
try:
    result = load_data()
except (psycopg.OperationalError, psycopg.InterfaceError) as e:
    logger.error("DB connection failed: %s", e, exc_info=True)
    error(self.window(), "Khong the ket noi may chu.")
    return
except Exception as e:
    logger.error("load_data failed: %s", e, exc_info=True)
    error(self.window(), f"Khong the tai du lieu: {e}")
    return
```

- Catch tai tang tab/controller — utils/service chi raise
- Phan biet loi mang vs loi logic
- Log day du: exception type, message, stack trace
- Hien thi message than thien, khong technical detail
- Rollback state neu operation that bai giua chung

---

## SECURITY

```python
# SAI — SQL injection
db.execute(f"SELECT * FROM users WHERE name = '{name}'")

# DUNG — parameterized query (PostgreSQL dung %s)
db.execute("SELECT * FROM users WHERE name = %s", (name,))
```

- Validate moi input truoc khi dung (`validators.py`)
- Password hash bang `bcrypt` — KHONG luu plaintext
- Khong log password, token, thong tin nhay cam
- `.env` nam trong `.gitignore` — KHONG commit password
- Soft delete (set `deleted_at`) thay vi DELETE khi can

---

## CODE PATTERNS

### Them tab moi (nhanh nhat)

```python
# tabs/quan_ly_kho.py
from PyQt6.QtWidgets import QLineEdit, QSpinBox, QDialog
from core.base_widgets import BaseTab, BaseDialog, label, divider
from core import theme
from widgets.table_crud import TableCrud
from widgets.loading import LoadingOverlay
from dialogs.confirm_dialog import confirm_delete, warn, error
from utils.validators import validate_all, required
from utils.db import Database
from utils.thread_worker import run_in_thread


class KhoDialog(BaseDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent, title="Them / Sua hang hoa",
                         min_width=380, data=data)

    def _build_form(self, form):
        self.ten_edit = QLineEdit()
        self.sl_spin  = QSpinBox(); self.sl_spin.setRange(0, 99999)
        form.addRow("Ten hang:", self.ten_edit)
        form.addRow("So luong:", self.sl_spin)

    def _fill(self, data: dict):
        self.ten_edit.setText(data.get("ten", ""))
        self.sl_spin.setValue(data.get("so_luong", 0))

    def get_data(self) -> dict:
        return {"ten": self.ten_edit.text().strip(),
                "so_luong": self.sl_spin.value()}


class QuanLyKhoTab(BaseTab):
    def _build(self, layout):
        layout.addWidget(label("Quan ly kho", bold=True, size=theme.FONT_SIZE_LG))
        layout.addWidget(divider())

        self._loading = LoadingOverlay(self)
        self.crud = TableCrud(
            columns=["ID", "Ten hang", "So luong"],
            on_add=self._on_add,
            on_edit=self._on_edit,
            on_delete=self._on_delete,
            on_search=self._on_search,
        )
        layout.addWidget(self.crud)
        self._reload()

    def _reload(self, q=""):
        run_in_thread(
            lambda: Database().fetchall(
                "SELECT id, ten, so_luong FROM hang_hoa WHERE ten ILIKE %s ORDER BY id",
                (f"%{q}%",),
            ),
            on_result=lambda data: self.crud.load(data, keys=["id", "ten", "so_luong"]),
            on_error=lambda e: error(self.window(), "Khong the tai du lieu."),
            on_finished=self._loading.stop,
        )
        self._loading.start("Dang tai...")

    def _on_add(self):
        dlg = KhoDialog(self.window())
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        errors = validate_all([required("Ten hang", data["ten"])])
        if errors:
            warn(self.window(), "\n".join(errors)); return
        run_in_thread(
            lambda: Database().execute(
                "INSERT INTO hang_hoa (ten, so_luong) VALUES (%s, %s)",
                (data["ten"], data["so_luong"]),
            ),
            on_result=lambda _: self._reload(),
            on_error=lambda e: error(self.window(), "Khong the them."),
        )

    def _on_edit(self):
        id_ = self.crud.selected_id()
        if not id_: return
        # Lay du lieu hien tai tu server
        run_in_thread(
            lambda: Database().fetchone("SELECT * FROM hang_hoa WHERE id = %s", (id_,)),
            on_result=lambda rec: self._show_edit_dialog(rec),
            on_error=lambda e: error(self.window(), "Khong the tai du lieu."),
        )

    def _show_edit_dialog(self, rec: dict | None):
        if not rec: return
        dlg = KhoDialog(self.window(), data=rec)
        if dlg.exec() != QDialog.DialogCode.Accepted: return
        data = dlg.get_data()
        run_in_thread(
            lambda: Database().execute(
                "UPDATE hang_hoa SET ten=%s, so_luong=%s WHERE id=%s",
                (data["ten"], data["so_luong"], rec["id"]),
            ),
            on_result=lambda _: self._reload(),
            on_error=lambda e: error(self.window(), "Khong the cap nhat."),
        )

    def _on_delete(self):
        id_ = self.crud.selected_id()
        if id_ and confirm_delete(self.window()):
            run_in_thread(
                lambda: Database().execute("DELETE FROM hang_hoa WHERE id = %s", (id_,)),
                on_result=lambda _: self._reload(),
                on_error=lambda e: error(self.window(), "Khong the xoa."),
            )

    def _on_search(self, text: str):
        self._reload(q=text)
```

Sau do trong `core/app_window.py` — them vao MENU list:
```python
{"icon": "icons/layui/table.svg", "text": "Kho hang", "tab": QuanLyKhoTab},
```

### Luu/phuc hoi cua so — da tich hop trong AppWindow
```python
# core/app_window.py da co san:
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
- Private: `_single_underscore`

**Code quality:**
- Type hints cho tat ca function signatures
- `@dataclass(frozen=True)` cho data models bat bien
- `pathlib.Path` thay `os.path`
- Early return thay vi if/else long sau
- Specific exceptions — khong dung bare `except:`
- `__slots__` va `@dataclass` khong dung chung

**Memory:**
- Disconnect signals trong `closeEvent()` / `cleanup()`
- `del` objects lon ngay sau khi dung xong
- `weakref` cho cache va observer pattern

---

## EXCEL EXPORT (xlsxwriter)

```python
# SAI — ghi moi o, file ~6MB
for row in range(32000):
    for col in range(60):
        worksheet.write(row, col, value, cell_format)

# DUNG — set column format 1 lan, chi ghi o co data → file ~2MB
worksheet.set_column(0, 59, width, cell_format)
for row_idx, row in enumerate(data_rows):
    for col, value in row.items():
        if value is not None:
            worksheet.write(row_idx, col, value)
```

---

## SERVER — FastAPI (server/main.py)

Ban local cua code chay tren VPS. Khi sua:
1. Sua `server/main.py` tai local
2. Upload len VPS qua SFTP hoac SSH
3. `systemctl restart maxhub-api` tren VPS

### API Endpoints hien co
| Method | Path | Auth | Mo ta |
|--------|------|------|-------|
| POST | `/api/register` | No | Dang ky (username, password) |
| POST | `/api/login` | No | Dang nhap → JWT token |
| GET | `/api/me` | Yes | Kiem tra token, tra ve user info |
| GET | `/api/health` | No | Health check |

### Them endpoint moi
```python
# Trong server/main.py

@app.get("/api/data")
def get_data(user=Depends(get_current_user), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT * FROM data WHERE deleted_at IS NULL")
    return {"ok": True, "items": cur.fetchall()}
```

Sau khi them: upload file + restart service tren VPS.

### Deploy commands (chay tren VPS qua SSH)
```bash
systemctl restart maxhub-api    # restart server
systemctl status maxhub-api     # check status
journalctl -u maxhub-api -n 50  # xem logs
```

---

## COMMON MISTAKES

| Sai | Dung |
|-----|------|
| API call trong main thread | `run_in_thread()` — **BAT BUOC voi app online** |
| Update UI tu worker thread | Emit signal, de main thread xu ly |
| `except: pass` | Log + `error(self.window(), ...)` |
| Tu viet toolbar + table tu dau | Dung `TableCrud` |
| Tu viet `QMessageBox.question(...)` | Dung `confirm_delete()` |
| Tu viet validate if/else | Dung `validate_all([required(...)])` |
| `setFixedWidth` tren widget chuan | Bo — Fusion tu tinh |
| Hardcode `8`, `(10,10,10,10)` | Dung `theme.SPACING_MD`, `theme.MARGIN_DEFAULT` |
| `from core.base_widgets import *` | Import dung ten can |
| Truy cap `obj._attr` tu class khac | Tao public method |
| `QFrame.StyledPanel` ra mau trang | Bo + them `WA_TranslucentBackground` |
| Unicode icon khong hien | Dung `.svg` tu `icons/layui/` hoac `icons/material/` |
| Thieu `SetCurrentProcessExplicitAppUserModelID` | Da co trong `main.py` — dung xoa |
| Dung `QToolTip` mac dinh | Goi `install(app)` trong `main.py` |
| Luu password plaintext | Dung `bcrypt` qua `utils/auth.py` |
| Commit `.env` vao git | `.env` da nam trong `.gitignore` |
| Dung `?` placeholder trong SQL | PostgreSQL dung `%s` |
| Giu Database connection lau | Tao moi + context manager cho moi operation |
| LIKE khong phan biet hoa thuong | PostgreSQL dung `ILIKE` thay `LIKE` |
| Desktop app goi DB truc tiep | Goi qua `utils/api.py` → server |
| Sua server code nhung khong upload | Upload `server/main.py` len VPS + restart |
| Hardcode API_URL trong code | Doc tu `.env` qua `utils/api.py` |

---

## CHECKLIST KHI THEM TAB MOI

```
[ ] Tao file trong tabs/, ke thua BaseTab
[ ] Dialog ke thua BaseDialog (neu can form)
[ ] Dung TableCrud thay vi tu lap toolbar + table
[ ] Validate qua validate_all() truoc khi luu
[ ] confirm_delete() truoc khi xoa
[ ] MOI I/O (DB query, file) chay trong run_in_thread() + LoadingOverlay
[ ] Xu ly loi mang: on_error hien message than thien
[ ] Khong import tab/feature khac
[ ] Dang ky tab trong MENU list o core/app_window.py
[ ] Test: UI khong do khi load data lon / mat mang
[ ] Test: app dong sach, khong co hanging thread/connection
```

---

## CHECKLIST KHI THEM BANG MOI

```
[ ] Tao bang: BIGSERIAL PRIMARY KEY, TIMESTAMPTZ cho thoi gian
[ ] created_at DEFAULT NOW(), updated_at DEFAULT NOW()
[ ] Soft delete: them deleted_at TIMESTAMPTZ (neu can)
[ ] Tao schema trong auth.init() hoac rieng service.init()
[ ] Tat ca query dung parameterized (%s)
[ ] Tim kiem dung ILIKE (khong phan biet hoa thuong)
[ ] Pagination: LIMIT %s OFFSET %s
```

---

## REFERENCE

| Metric | Gia tri | Ghi chu |
|--------|---------|---------|
| UI block threshold | 50ms | Hon → worker thread |
| `SPACING_XS/SM/MD/LG/XL` | 2/4/8/16/24px | `core/theme.py` |
| `MARGIN_DEFAULT` | (10,10,10,10) | `*theme.MARGIN_DEFAULT` |
| `FONT_SIZE` | 10pt | Segoe UI |
| Debounce search | 300ms | SearchBar da tu xu ly |
| DB/API timeout | 15-30s | Tuy operation |
| Retry | 3 lan | Backoff: 1s → 2s → 3s |
| Thread pool | 4-8 threads | `QThread.idealThreadCount()` |
| Pagination default | 20 items/page | `TableCrud(page_size=20)` |
| Password hash | bcrypt | `utils/auth.py` |
| SQL placeholder | `%s` | KHONG dung `?` |
| DB driver | psycopg v3 | `dict_row` factory |
