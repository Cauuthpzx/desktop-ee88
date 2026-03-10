"""
MaxHub Manager v1.0.0
Quản lý Goserver, GoWeb, GoDesktop — console log realtime, kill port, system monitor.
"""
import os
import sys
import signal
import atexit
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from datetime import datetime
import time
import webbrowser
import psutil

# ── Cấu hình ──────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MSYS_BIN = "C:/msys64/mingw64/bin"

SERVICES = {
    "Goserver": {
        "cwd": os.path.join(PROJECT_ROOT, "Goserver"),
        "cmd": ["go", "run", "cmd/server/main.go"],
        "env": {"DB_PASSWORD": "hiepmun2021", "JWT_SECRET": "maxhub-dev-jwt-secret-2026"},
        "color": "#2ecc71",
        "port": 8080,
    },
    "GoWeb": {
        "cwd": os.path.join(PROJECT_ROOT, "GoWeb"),
        "cmd": ["pnpm.CMD", "dev:docs"],
        "env": {},
        "color": "#3498db",
        "port": 5173,
    },
    "GoDesktop": {
        "cwd": os.path.join(PROJECT_ROOT, "GoDesktop"),
        "cmd": None,
        "env": {"PATH": MSYS_BIN + os.pathsep + os.environ.get("PATH", "")},
        "color": "#e67e22",
        "port": None,
    },
}

MINGW32_MAKE = os.path.join(MSYS_BIN, "mingw32-make.exe")

DESKTOP_COMMANDS = {
    "Build": [
        "cmake", "-B", "build", "-G", "MinGW Makefiles",
        f"-DCMAKE_MAKE_PROGRAM={MINGW32_MAKE}",
        "-DCMAKE_PREFIX_PATH=C:/msys64/mingw64",
    ],
    "Compile": ["cmake", "--build", "build"],
    "Run": [os.path.join(PROJECT_ROOT, "GoDesktop", "build", "GoDesktop.exe")],
    "Clean": ["cmake", "--build", "build", "--target", "clean"],
}


def find_pid_on_port(port):
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr.port == port and conn.status == "LISTEN":
                return conn.pid
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        pass
    return None


def kill_port(port):
    pid = find_pid_on_port(port)
    if pid is None:
        return False, f"Port {port} không có process nào"
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.kill()
        proc.wait(timeout=3)
        return True, f"Đã kill {name} (PID {pid}) trên port {port}"
    except Exception as e:
        return False, f"Không thể kill PID {pid}: {e}"


def get_port_info(port):
    pid = find_pid_on_port(port)
    if pid is None:
        return None
    try:
        proc = psutil.Process(pid)
        return {"pid": pid, "name": proc.name(), "status": proc.status()}
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


class ConsolePanel(ttk.LabelFrame):
    """Panel console với log realtime."""

    def __init__(self, parent, name, color, port=None):
        label_text = f" {name} " + (f":{port} " if port else "")
        super().__init__(parent, text=label_text)
        self.name = name
        self.color = color
        self.port = port
        self.line_count = 0
        self.max_lines = 2000
        self.start_time = None

        # ── Header: status + uptime + line count ──
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=4, pady=(2, 0))

        self.status_dot = tk.Label(
            header, text="\u25cf", fg="#999", font=("Segoe UI", 11),
            bg=self._get_bg(),
        )
        self.status_dot.pack(side=tk.LEFT)

        self.status_label = ttk.Label(
            header, text="Dừng", foreground="#999", font=("Segoe UI", 8),
        )
        self.status_label.pack(side=tk.LEFT, padx=(2, 0))

        self.uptime_label = ttk.Label(
            header, text="", foreground="#888", font=("Segoe UI", 8),
        )
        self.uptime_label.pack(side=tk.LEFT, padx=(6, 0))

        self.lines_label = ttk.Label(
            header, text="0 dòng", foreground="#aaa", font=("Segoe UI", 8),
        )
        self.lines_label.pack(side=tk.RIGHT)

        ttk.Button(
            header, text="Xóa log", width=7, command=self.clear,
            style="Small.TButton",
        ).pack(side=tk.RIGHT, padx=(0, 4))

        # ── Console ──
        self.console = scrolledtext.ScrolledText(
            self, height=10, bg="#1e1e1e", fg="#dcdcdc",
            font=("Consolas", 9), insertbackground="#dcdcdc",
            state=tk.DISABLED, wrap=tk.WORD, relief=tk.SUNKEN,
            borderwidth=1, padx=6, pady=4,
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 4))
        self.console.tag_config("info", foreground="#d4d4d4")
        self.console.tag_config("error", foreground="#f44747")
        self.console.tag_config("warn", foreground="#cca700")
        self.console.tag_config("success", foreground="#4ec9b0")
        self.console.tag_config("system", foreground="#569cd6")
        self.console.tag_config("dim", foreground="#666666")

    def _get_bg(self):
        try:
            return self.master.winfo_toplevel().cget("bg")
        except Exception:
            return "#f0f0f0"

    def log(self, text, tag="info"):
        self.console.config(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{ts}] {text}\n", tag)
        self.line_count += 1
        if self.line_count > self.max_lines:
            self.console.delete("1.0", f"{self.line_count - self.max_lines}.0")
            self.line_count = self.max_lines
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)
        self.lines_label.config(text=f"{self.line_count} dòng")

    def clear(self):
        self.console.config(state=tk.NORMAL)
        self.console.delete("1.0", tk.END)
        self.console.config(state=tk.DISABLED)
        self.line_count = 0
        self.lines_label.config(text="0 dòng")

    def set_running(self, running):
        if running:
            self.status_dot.config(fg=self.color)
            self.status_label.config(text="Đang chạy", foreground=self.color)
            self.start_time = time.time()
        else:
            self.status_dot.config(fg="#999")
            self.status_label.config(text="Dừng", foreground="#999")
            self.start_time = None
            self.uptime_label.config(text="")

    def update_uptime(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            h, m, s = elapsed // 3600, (elapsed % 3600) // 60, elapsed % 60
            if h > 0:
                self.uptime_label.config(text=f"{h}h{m:02d}m{s:02d}s")
            elif m > 0:
                self.uptime_label.config(text=f"{m}m{s:02d}s")
            else:
                self.uptime_label.config(text=f"{s}s")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MaxHub Manager v1.0.0")
        self.geometry("1200x750")
        self.minsize(950, 550)
        self.configure(bg="#f0f0f0")

        style = ttk.Style()
        style.theme_use("vista")
        style.configure("TButton", padding=(8, 4), font=("Segoe UI", 9))
        style.configure("Small.TButton", padding=(4, 2), font=("Segoe UI", 8))
        style.configure("Start.TButton", padding=(8, 4), font=("Segoe UI", 9))
        style.configure("Stop.TButton", padding=(8, 4), font=("Segoe UI", 9))
        style.configure("TLabel", font=("Segoe UI", 9))
        style.configure("Title.TLabel", font=("Segoe UI", 13, "bold"))
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 9, "bold"))

        self.panels = {}
        self.processes = {}
        self._cmd_procs = {}
        self._shutting_down = False

        self._build_ui()
        self._update_uptime()
        self._update_status_bar()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Đăng ký cleanup cho MỌI cách thoát
        atexit.register(self._force_cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _build_ui(self):
        # ════════════════════════════════════════════════════════
        # HEADER
        # ════════════════════════════════════════════════════════
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=10, pady=(8, 0))

        ttk.Label(header, text="MaxHub Manager", style="Title.TLabel").pack(side=tk.LEFT)

        ttk.Label(
            header, text=PROJECT_ROOT, foreground="#888", font=("Segoe UI", 8),
        ).pack(side=tk.RIGHT)

        # ════════════════════════════════════════════════════════
        # THANH ĐIỀU KHIỂN CHÍNH
        # ════════════════════════════════════════════════════════
        ctrl_frame = ttk.LabelFrame(self, text=" Điều khiển chung ")
        ctrl_frame.pack(fill=tk.X, padx=10, pady=(6, 0))

        ctrl_inner = ttk.Frame(ctrl_frame)
        ctrl_inner.pack(padx=6, pady=6)

        # Nhóm 1: Quản lý service
        grp1 = ttk.Frame(ctrl_inner)
        grp1.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(grp1, text="\u25b6 Khởi động tất cả", command=self.start_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(grp1, text="\u25a0 Dừng tất cả", command=self.stop_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(grp1, text="\u21bb Restart tất cả", command=self.restart_all).pack(side=tk.LEFT, padx=2)

        ttk.Separator(ctrl_inner, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Nhóm 2: Port
        grp2 = ttk.Frame(ctrl_inner)
        grp2.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(grp2, text="Kill Port...", command=self.kill_port_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(grp2, text="Quét Port", command=self.scan_ports).pack(side=tk.LEFT, padx=2)

        ttk.Separator(ctrl_inner, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Nhóm 3: Tiện ích
        grp3 = ttk.Frame(ctrl_inner)
        grp3.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(grp3, text="Xóa tất cả log", command=self.clear_all_logs).pack(side=tk.LEFT, padx=2)
        ttk.Button(grp3, text="Mở thư mục dự án", command=lambda: os.startfile(PROJECT_ROOT)).pack(side=tk.LEFT, padx=2)

        # ════════════════════════════════════════════════════════
        # 3 CONSOLE PANELS
        # ════════════════════════════════════════════════════════
        console_frame = ttk.Frame(self)
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 0))
        console_frame.columnconfigure(0, weight=1)
        console_frame.columnconfigure(1, weight=1)
        console_frame.columnconfigure(2, weight=1)
        console_frame.rowconfigure(1, weight=1)

        # ── Tạo 3 cột: mỗi cột = nút điều khiển + console ──
        col = 0
        for name, cfg in SERVICES.items():
            # Nút điều khiển cho từng service
            btn_frame = ttk.LabelFrame(
                console_frame, text=f" {name} — Điều khiển ",
            )
            btn_frame.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 3, 0), pady=(0, 2))

            inner = ttk.Frame(btn_frame)
            inner.pack(padx=4, pady=4)

            if name == "Goserver":
                self._build_goserver_buttons(inner)
            elif name == "GoWeb":
                self._build_goweb_buttons(inner)
            elif name == "GoDesktop":
                self._build_godesktop_buttons(inner)

            # Console panel
            panel = ConsolePanel(console_frame, name, cfg["color"], cfg.get("port"))
            panel.grid(row=1, column=col, sticky="nsew", padx=(0 if col == 0 else 3, 0))
            self.panels[name] = panel

            col += 1

        # ════════════════════════════════════════════════════════
        # STATUS BAR
        # ════════════════════════════════════════════════════════
        status_bar = ttk.Frame(self)
        status_bar.pack(fill=tk.X, padx=10, pady=(4, 6))

        self.cpu_label = ttk.Label(status_bar, text="CPU: --", font=("Segoe UI", 8), foreground="#555")
        self.cpu_label.pack(side=tk.LEFT, padx=(0, 12))

        self.mem_label = ttk.Label(status_bar, text="RAM: --", font=("Segoe UI", 8), foreground="#555")
        self.mem_label.pack(side=tk.LEFT, padx=(0, 12))

        self.port_status = ttk.Label(status_bar, text="", font=("Segoe UI", 8), foreground="#555")
        self.port_status.pack(side=tk.RIGHT)

    # ── Nút cho Goserver ─────────────────────────────────────
    def _build_goserver_buttons(self, parent):
        row1 = ttk.Frame(parent)
        row1.pack(fill=tk.X)

        ttk.Button(row1, text="\u25b6 Start", width=8,
                   command=lambda: self.start_service("Goserver"),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(row1, text="\u25a0 Stop", width=8,
                   command=lambda: self.stop_service("Goserver"),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(row1, text="\u21bb Restart", width=8,
                   command=lambda: self.restart_service("Goserver"),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)

        ttk.Separator(row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        ttk.Button(row1, text="Kill :8080", width=8,
                   command=lambda: self.kill_port_action(8080, "Goserver"),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(row1, text="go mod tidy", width=10,
                   command=lambda: self.run_in_panel("Goserver", ["go", "mod", "tidy"], SERVICES["Goserver"]["cwd"]),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(row1, text="go test", width=8,
                   command=lambda: self.run_in_panel("Goserver", ["go", "test", "./..."], SERVICES["Goserver"]["cwd"]),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(row1, text="Mở :8080", width=8,
                   command=lambda: webbrowser.open("http://localhost:8080"),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)

    # ── Nút cho GoWeb ────────────────────────────────────────
    def _build_goweb_buttons(self, parent):
        row1 = ttk.Frame(parent)
        row1.pack(fill=tk.X)

        ttk.Button(row1, text="\u25b6 Start", width=8,
                   command=lambda: self.start_service("GoWeb"),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(row1, text="\u25a0 Stop", width=8,
                   command=lambda: self.stop_service("GoWeb"),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(row1, text="\u21bb Restart", width=8,
                   command=lambda: self.restart_service("GoWeb"),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)

        ttk.Separator(row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        ttk.Button(row1, text="Kill :5173", width=8,
                   command=lambda: self.kill_port_action(5173, "GoWeb"),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(row1, text="pnpm install", width=10,
                   command=self.web_install,
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(row1, text="pnpm build", width=10,
                   command=self.web_build,
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(row1, text="Mở :5173", width=8,
                   command=lambda: webbrowser.open("http://localhost:5173"),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)

    # ── Nút cho GoDesktop ────────────────────────────────────
    def _build_godesktop_buttons(self, parent):
        row1 = ttk.Frame(parent)
        row1.pack(fill=tk.X)

        ttk.Button(row1, text="Build+Compile", width=12,
                   command=self.desktop_build_and_compile,
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(row1, text="CMake Build", width=10,
                   command=lambda: self.desktop_cmd("Build"),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(row1, text="Compile", width=8,
                   command=lambda: self.desktop_cmd("Compile"),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(row1, text="\u25b6 Run", width=8,
                   command=lambda: self.desktop_cmd("Run"),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)
        ttk.Button(row1, text="Clean", width=8,
                   command=lambda: self.desktop_cmd("Clean"),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)

        ttk.Separator(row1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4)

        ttk.Button(row1, text="Mở thư mục", width=10,
                   command=lambda: os.startfile(SERVICES["GoDesktop"]["cwd"]),
                   style="Small.TButton").pack(side=tk.LEFT, padx=1)

    # ════════════════════════════════════════════════════════════
    # SERVICE MANAGEMENT
    # ════════════════════════════════════════════════════════════
    def start_service(self, name):
        if name in self.processes and self.processes[name] is not None:
            self.panels[name].log("Đã đang chạy!", "warn")
            return

        cfg = SERVICES[name]
        if cfg["cmd"] is None:
            self.panels[name].log("Dùng CMake Build → Compile → Run.", "system")
            return

        # Auto kill port nếu bị chiếm
        port = cfg.get("port")
        if port:
            pid = find_pid_on_port(port)
            if pid:
                self.panels[name].log(f"Port {port} đang bị chiếm (PID {pid}), đang kill...", "warn")
                ok, msg = kill_port(port)
                self.panels[name].log(msg, "success" if ok else "error")
                if not ok:
                    return
                time.sleep(0.3)

        env = os.environ.copy()
        env.update(cfg["env"])

        self.panels[name].log(f"Khởi động {name}...", "system")
        self.panels[name].log(f"$ {' '.join(cfg['cmd'])}", "dim")

        try:
            proc = subprocess.Popen(
                cfg["cmd"], cwd=cfg["cwd"], env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            self.processes[name] = proc
            self.panels[name].set_running(True)

            threading.Thread(
                target=self._read_output, args=(name, proc), daemon=True,
            ).start()

        except FileNotFoundError as e:
            self.panels[name].log(f"Lỗi: {e}", "error")
        except Exception as e:
            self.panels[name].log(f"Lỗi khởi động: {e}", "error")

    def _kill_proc_tree(self, pid):
        """Kill process và toàn bộ child processes của nó."""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            # Kill children trước
            for child in children:
                try:
                    child.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            # Kill parent
            try:
                parent.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            # Đợi tất cả chết
            gone, alive = psutil.wait_procs(children + [parent], timeout=3)
            # Force kill nếu vẫn còn sống
            for p in alive:
                try:
                    p.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except psutil.NoSuchProcess:
            pass
        except Exception:
            # Fallback: dùng taskkill
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True, timeout=5,
                )
            except Exception:
                pass

    def stop_service(self, name, silent=False):
        proc = self.processes.get(name)
        if proc is None:
            if not silent:
                self.panels[name].log(f"{name} chưa chạy.", "system")
            return

        if not silent:
            self.panels[name].log(f"Dừng {name}...", "system")

        self._kill_proc_tree(proc.pid)

        self.processes[name] = None
        if not silent:
            self.panels[name].set_running(False)
            self.panels[name].log(f"{name} đã dừng.", "success")

    def restart_service(self, name):
        self.stop_service(name)
        self.after(600, lambda: self.start_service(name))

    def start_all(self):
        for name in SERVICES:
            if SERVICES[name]["cmd"] is not None:
                self.start_service(name)

    def stop_all(self, silent=False):
        for name in SERVICES:
            if self.processes.get(name) is not None:
                self.stop_service(name, silent=silent)

    def restart_all(self):
        self.stop_all()
        self.after(800, self.start_all)

    # ════════════════════════════════════════════════════════════
    # KILL PORT
    # ════════════════════════════════════════════════════════════
    def kill_port_action(self, port, panel_name):
        panel = self.panels[panel_name]
        info = get_port_info(port)
        if info is None:
            panel.log(f"Port {port} trống, không có gì để kill.", "system")
            return
        panel.log(f"Port {port}: {info['name']} (PID {info['pid']})", "system")
        ok, msg = kill_port(port)
        panel.log(msg, "success" if ok else "error")

    def kill_port_dialog(self):
        port_str = simpledialog.askstring(
            "Kill Port", "Nhập port cần kill:", parent=self,
        )
        if not port_str:
            return
        try:
            port = int(port_str.strip())
        except ValueError:
            messagebox.showerror("Lỗi", "Port phải là số nguyên")
            return

        info = get_port_info(port)
        if info is None:
            messagebox.showinfo("Thông tin", f"Port {port} trống")
            return

        confirm = messagebox.askyesno(
            "Xác nhận",
            f"Kill {info['name']} (PID {info['pid']}) trên port {port}?",
        )
        if confirm:
            ok, msg = kill_port(port)
            # Tìm panel phù hợp để log
            target_panel = "Goserver"
            for name, cfg in SERVICES.items():
                if cfg.get("port") == port:
                    target_panel = name
                    break
            self.panels[target_panel].log(msg, "success" if ok else "error")

    def scan_ports(self):
        """Quét các port quan trọng, log vào từng panel tương ứng."""
        # Log tổng hợp vào Goserver panel
        panel = self.panels["Goserver"]
        panel.log("═══ Quét port ═══", "system")
        for port in [8080, 5173, 5432, 3000, 3001, 4173]:
            info = get_port_info(port)
            if info:
                panel.log(
                    f"  :{port}  \u2192  {info['name']} (PID {info['pid']}) [{info['status']}]",
                    "warn",
                )
            else:
                panel.log(f"  :{port}  \u2192  trống", "dim")

    # ════════════════════════════════════════════════════════════
    # GOWEB COMMANDS
    # ════════════════════════════════════════════════════════════
    def web_install(self):
        self.run_in_panel("GoWeb", ["pnpm.CMD", "install"], SERVICES["GoWeb"]["cwd"])

    def web_build(self):
        self.run_in_panel("GoWeb", ["pnpm.CMD", "build:docs"], SERVICES["GoWeb"]["cwd"])

    # ════════════════════════════════════════════════════════════
    # GODESKTOP COMMANDS
    # ════════════════════════════════════════════════════════════
    def _desktop_env(self):
        """Build env for GoDesktop with MSYS_BIN prepended to PATH."""
        env = os.environ.copy()
        # Ensure mingw64/bin is FIRST in PATH so cmake/MOC can find DLLs
        current_path = env.get("PATH", "")
        if MSYS_BIN.replace("/", "\\") not in current_path and MSYS_BIN not in current_path:
            env["PATH"] = MSYS_BIN + os.pathsep + current_path
        else:
            # Move it to front if already present but not first
            parts = current_path.split(os.pathsep)
            parts = [p for p in parts if p.replace("\\", "/") != MSYS_BIN.replace("\\", "/")
                     and p != MSYS_BIN]
            env["PATH"] = MSYS_BIN + os.pathsep + os.pathsep.join(parts)
        return env

    def _find_tool(self, name):
        """Find tool in MSYS_BIN or system PATH, return full path or None."""
        # Check MSYS_BIN first
        for ext in [".exe", ""]:
            full = os.path.join(MSYS_BIN, name + ext)
            if os.path.isfile(full):
                return full
        # Fallback: check system PATH
        import shutil
        found = shutil.which(name)
        return found

    def _desktop_check_tools(self, panel):
        """Check that cmake and mingw32-make are available."""
        for tool in ["cmake", "mingw32-make"]:
            path = self._find_tool(tool)
            if path is None:
                panel.log(f"⚠ Không tìm thấy {tool}.", "error")
                panel.log(f"  Kiểm tra MSYS2/MinGW64 đã cài chưa.", "error")
                panel.log(f"  PATH cần có: {MSYS_BIN}", "error")
                return False
            try:
                result = subprocess.run(
                    [path, "--version"],
                    env=self._desktop_env(),
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode != 0:
                    panel.log(f"⚠ {tool} không hoạt động (exit {result.returncode})", "error")
                    return False
            except Exception as e:
                panel.log(f"⚠ Lỗi kiểm tra {tool}: {e}", "error")
                return False
        return True

    def _desktop_clean_cache(self, cwd, panel):
        """Remove cmake cache files to force fresh configure."""
        import shutil
        removed = []
        for name in ["CMakeCache.txt", "CMakeFiles", "GoDesktop_autogen"]:
            path = os.path.join(cwd, "build", name)
            if os.path.isfile(path):
                os.remove(path)
                removed.append(name)
            elif os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
                removed.append(name)
        if removed:
            panel.log(f"Đã xóa cache: {', '.join(removed)}", "system")

    def _resolve_cmd(self, cmd):
        """Resolve the first element of cmd to full path if it's a known tool."""
        exe = cmd[0]
        # Skip if already absolute path
        if os.path.isabs(exe):
            return cmd
        resolved = self._find_tool(exe)
        if resolved:
            return [resolved] + cmd[1:]
        return cmd

    def desktop_cmd(self, cmd_key):
        cmd = DESKTOP_COMMANDS[cmd_key]
        cfg = SERVICES["GoDesktop"]
        cwd = cfg["cwd"]
        panel = self.panels["GoDesktop"]

        if not os.path.isdir(cwd):
            panel.log(f"Thư mục không tồn tại: {cwd}", "error")
            return

        env = self._desktop_env()

        # Pre-flight checks for build commands
        if cmd_key in ("Build", "Compile", "Clean"):
            if not self._desktop_check_tools(panel):
                return

        # For Build: auto-clean stale cmake cache to prevent MOC errors
        if cmd_key == "Build":
            cache_file = os.path.join(cwd, "build", "CMakeCache.txt")
            if os.path.isfile(cache_file):
                try:
                    with open(cache_file, "r") as f:
                        content = f.read()
                    if MSYS_BIN.replace("/", "\\") not in content and MSYS_BIN not in content:
                        panel.log("CMake cache cũ, xóa để configure lại...", "warn")
                        self._desktop_clean_cache(cwd, panel)
                except Exception:
                    pass

        # For Run: check exe exists
        if cmd_key == "Run":
            exe = cmd[0]
            if not os.path.isfile(exe):
                panel.log(f"Chưa build! Không tìm thấy: {os.path.basename(exe)}", "error")
                panel.log("Hãy chạy CMake Build → Compile trước.", "system")
                return

        self.run_in_panel("GoDesktop", self._resolve_cmd(cmd), cwd, env)

    def desktop_build_and_compile(self):
        """Run Build then Compile sequentially."""
        cfg = SERVICES["GoDesktop"]
        cwd = cfg["cwd"]
        panel = self.panels["GoDesktop"]
        env = self._desktop_env()

        if not os.path.isdir(cwd):
            panel.log(f"Thư mục không tồn tại: {cwd}", "error")
            return

        if not self._desktop_check_tools(panel):
            return

        # Auto-clean stale cache
        cache_file = os.path.join(cwd, "build", "CMakeCache.txt")
        if os.path.isfile(cache_file):
            try:
                with open(cache_file, "r") as f:
                    content = f.read()
                if MSYS_BIN.replace("/", "\\") not in content and MSYS_BIN not in content:
                    panel.log("CMake cache cũ, xóa để configure lại...", "warn")
                    self._desktop_clean_cache(cwd, panel)
            except Exception:
                pass

        existing = self._cmd_procs.get("GoDesktop")
        if existing and existing.poll() is None:
            panel.log("Đang có lệnh khác chạy, vui lòng đợi...", "warn")
            return

        def run():
            build_cmd = self._resolve_cmd(DESKTOP_COMMANDS["Build"])
            compile_cmd = self._resolve_cmd(DESKTOP_COMMANDS["Compile"])

            for step_name, cmd in [("CMake Configure", build_cmd), ("Compile", compile_cmd)]:
                self.after(0, panel.log, f"══ {step_name} ══", "system")
                self.after(0, panel.log, f"$ {' '.join(cmd)}", "dim")
                try:
                    proc = subprocess.Popen(
                        cmd, cwd=cwd, env=env,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, bufsize=1,
                    )
                    self._cmd_procs["GoDesktop"] = proc
                    for line in proc.stdout:
                        line = line.rstrip()
                        if line:
                            tag = "info"
                            lower = line.lower()
                            if "error" in lower or "fail" in lower:
                                tag = "error"
                            elif "warn" in lower:
                                tag = "warn"
                            elif "success" in lower or "done" in lower or "built" in lower:
                                tag = "success"
                            self.after(0, panel.log, line, tag)
                    proc.wait()
                    if proc.returncode != 0:
                        self.after(0, panel.log,
                                   f"✗ {step_name} thất bại (exit code {proc.returncode})", "error")
                        if step_name == "CMake Configure":
                            self.after(0, panel.log,
                                       "Thử xóa build/ và chạy lại.", "system")
                        return
                    self.after(0, panel.log,
                               f"✓ {step_name} hoàn tất", "success")
                except FileNotFoundError:
                    self.after(0, panel.log, f"Không tìm thấy: {cmd[0]}", "error")
                    return
                except Exception as e:
                    self.after(0, panel.log, f"Lỗi: {e}", "error")
                    return
                finally:
                    self._cmd_procs.pop("GoDesktop", None)

            self.after(0, panel.log, "══ Build hoàn tất! Nhấn Run để chạy. ══", "success")

        threading.Thread(target=run, daemon=True).start()

    # ════════════════════════════════════════════════════════════
    # GENERIC COMMAND RUNNER
    # ════════════════════════════════════════════════════════════
    def run_in_panel(self, panel_name, cmd, cwd, env=None):
        panel = self.panels[panel_name]

        # Kiểm tra nếu đang có lệnh chạy (không phải service)
        existing = self._cmd_procs.get(panel_name)
        if existing and existing.poll() is None:
            panel.log("Đang có lệnh khác chạy, vui lòng đợi...", "warn")
            return

        panel.log(f"$ {' '.join(cmd)}", "dim")

        def run():
            try:
                proc = subprocess.Popen(
                    cmd, cwd=cwd, env=env,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                )
                self._cmd_procs[panel_name] = proc
                for line in proc.stdout:
                    line = line.rstrip()
                    if line:
                        tag = "info"
                        lower = line.lower()
                        if "error" in lower or "fail" in lower:
                            tag = "error"
                        elif "warn" in lower:
                            tag = "warn"
                        elif "success" in lower or "done" in lower or "built" in lower:
                            tag = "success"
                        self.after(0, panel.log, line, tag)
                proc.wait()
                tag = "success" if proc.returncode == 0 else "error"
                self.after(0, panel.log,
                           f"Hoàn tất (exit code {proc.returncode})", tag)
            except FileNotFoundError:
                self.after(0, panel.log, f"Không tìm thấy: {cmd[0]}", "error")
            except Exception as e:
                self.after(0, panel.log, f"Lỗi: {e}", "error")
            finally:
                self._cmd_procs.pop(panel_name, None)

        threading.Thread(target=run, daemon=True).start()

    # ════════════════════════════════════════════════════════════
    # OUTPUT READER
    # ════════════════════════════════════════════════════════════
    def _read_output(self, name, proc):
        panel = self.panels[name]
        try:
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    tag = "info"
                    lower = line.lower()
                    if "error" in lower or "fail" in lower or "panic" in lower:
                        tag = "error"
                    elif "warn" in lower:
                        tag = "warn"
                    elif "starting" in lower or "ready" in lower or "success" in lower or "listening" in lower:
                        tag = "success"
                    self.after(0, panel.log, line, tag)
        except Exception:
            pass
        finally:
            self.processes[name] = None
            self.after(0, panel.set_running, False)
            self.after(0, panel.log, f"{name} kết thúc.", "system")

    # ════════════════════════════════════════════════════════════
    # PERIODIC UPDATES
    # ════════════════════════════════════════════════════════════
    def _update_uptime(self):
        for panel in self.panels.values():
            panel.update_uptime()
        self.after(1000, self._update_uptime)

    def _update_status_bar(self):
        try:
            cpu = psutil.cpu_percent(interval=0)
            mem = psutil.virtual_memory()
            self.cpu_label.config(text=f"CPU: {cpu:.0f}%")
            self.mem_label.config(
                text=f"RAM: {mem.used / (1024**3):.1f}/{mem.total / (1024**3):.1f} GB ({mem.percent}%)",
            )
            ports = []
            for name, cfg in SERVICES.items():
                p = cfg.get("port")
                if p:
                    info = get_port_info(p)
                    dot = "\u25cf" if info else "\u25cb"
                    ports.append(f":{p} {dot}")
            self.port_status.config(text="    ".join(ports))
        except Exception:
            pass
        self.after(3000, self._update_status_bar)

    def clear_all_logs(self):
        for panel in self.panels.values():
            panel.clear()

    # ════════════════════════════════════════════════════════════
    # CLEANUP — đảm bảo kill sạch bất kể cách thoát nào
    # ════════════════════════════════════════════════════════════
    def _force_cleanup(self):
        """Kill tất cả child processes — gọi bởi atexit, signal, on_close."""
        if self._shutting_down:
            return
        self._shutting_down = True

        # Kill service processes
        for name, proc in list(self.processes.items()):
            if proc is not None:
                self._kill_proc_tree(proc.pid)
                self.processes[name] = None

        # Kill command processes (go mod tidy, pnpm install, etc.)
        for name, proc in list(self._cmd_procs.items()):
            if proc is not None and proc.poll() is None:
                self._kill_proc_tree(proc.pid)
        self._cmd_procs.clear()

        # Double-check: kill theo port nếu vẫn còn sót
        for cfg in SERVICES.values():
            port = cfg.get("port")
            if port:
                pid = find_pid_on_port(port)
                if pid:
                    try:
                        p = psutil.Process(pid)
                        p.kill()
                    except Exception:
                        pass

    def _signal_handler(self, signum, frame):
        """Xử lý Ctrl+C, SIGTERM."""
        self._force_cleanup()
        try:
            self.destroy()
        except Exception:
            pass
        sys.exit(0)

    def on_close(self):
        """Nhấn X hoặc Alt+F4."""
        self._force_cleanup()
        try:
            self.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    app = App()
    app.mainloop()
