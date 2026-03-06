"""
build.py — Build MaxHub desktop app voi PyInstaller (--onedir).

Chay:
    python build.py            # build binh thuong
    python build.py --clean    # xoa build/ dist/ truoc khi build
    python build.py --version 1.2.0   # dat version cu the

Ket qua:
    dist/MaxHub/              # folder chua app
    dist/MaxHub/MaxHub.exe    # executable chinh
    dist/MaxHub_1.0.0_sha256.txt  # hash SHA-256 de upload len server
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"
APP_NAME = "MaxHub"
ENTRY = ROOT / "main.py"
ICON = ROOT / "icons" / "app" / "icon-taskbar.ico"

# Cac folder/file can dong goi cung app
DATA_ITEMS: list[tuple[str, str]] = [
    # (source, dest_in_bundle)
    ("icons", "icons"),
    ("i18n", "i18n"),
    (".env", "."),
]

# Cac module an (PyInstaller khong tu detect)
HIDDEN_IMPORTS: list[str] = [
    "PyQt6.QtSvg",
    "PyQt6.QtSvgWidgets",
]

# Cac module KHONG can dong goi (giam kich thuoc)
EXCLUDES: list[str] = [
    "tkinter",
    "unittest",
    "xmlrpc",
    "pydoc",
    "doctest",
    "test",
    # Server — chi chay tren VPS, khong can trong desktop build
    "server",
    "fastapi",
    "uvicorn",
    "psycopg2",
    "pyjwt",
    "python-dotenv",
    "bcrypt",
]


def clean() -> None:
    """Xoa build artifacts."""
    for d in [BUILD, DIST]:
        if d.exists():
            print(f"  Xoa {d}")
            shutil.rmtree(d)
    spec = ROOT / f"{APP_NAME}.spec"
    if spec.exists():
        spec.unlink()


def sha256_file(path: Path) -> str:
    """Tinh SHA-256 cua file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_dir(folder: Path) -> str:
    """Tinh SHA-256 cua tat ca file trong folder (de verify update)."""
    h = hashlib.sha256()
    for root, _dirs, files in os.walk(folder):
        for name in sorted(files):
            fp = Path(root) / name
            with open(fp, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
    return h.hexdigest()


def build(version: str) -> Path:
    """Chay PyInstaller --onedir."""
    cmd: list[str] = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        f"--name={APP_NAME}",
        f"--icon={ICON}",
    ]

    # Add data
    sep = ";" if sys.platform == "win32" else ":"
    for src, dest in DATA_ITEMS:
        src_path = ROOT / src
        if src_path.exists():
            cmd.append(f"--add-data={src_path}{sep}{dest}")

    # Hidden imports
    for mod in HIDDEN_IMPORTS:
        cmd.append(f"--hidden-import={mod}")

    # Excludes
    for mod in EXCLUDES:
        cmd.append(f"--exclude-module={mod}")

    # Version info
    cmd.append(f"--distpath={DIST}")
    cmd.append(f"--workpath={BUILD}")

    cmd.append(str(ENTRY))

    print(f"\n  Building {APP_NAME} v{version}...")
    print(f"  Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print("\n  BUILD FAILED!")
        sys.exit(1)

    app_dir = DIST / APP_NAME
    if not app_dir.exists():
        print(f"\n  ERROR: {app_dir} khong ton tai sau khi build!")
        sys.exit(1)

    return app_dir


def write_version_file(app_dir: Path, version: str) -> None:
    """Ghi file version.txt vao app dir."""
    (app_dir / "version.txt").write_text(version, encoding="utf-8")


def compute_hash(app_dir: Path, version: str) -> None:
    """Tinh SHA-256 va ghi file hash."""
    print("\n  Tinh SHA-256...")
    exe = app_dir / f"{APP_NAME}.exe"
    if exe.exists():
        h = sha256_file(exe)
        hash_file = DIST / f"{APP_NAME}_{version}_sha256.txt"
        hash_file.write_text(
            f"SHA-256 ({APP_NAME}.exe) = {h}\n"
            f"Version: {version}\n",
            encoding="utf-8",
        )
        print(f"  SHA-256: {h}")
        print(f"  Ghi vao: {hash_file}")

        # In huong dan update server .env
        print(f"\n  === Cap nhat .env tren server ===")
        print(f"  APP_VERSION={version}")
        print(f"  UPDATE_SHA256={h}")
        size = exe.stat().st_size
        print(f"  UPDATE_FILE_SIZE={size}")
    else:
        print(f"  WARNING: {exe} khong tim thay, bo qua SHA-256.")


def main() -> None:
    parser = argparse.ArgumentParser(description=f"Build {APP_NAME} desktop app")
    parser.add_argument("--clean", action="store_true", help="Xoa build/dist truoc khi build")
    parser.add_argument("--version", default="1.0.0", help="Phien ban app (default: 1.0.0)")
    args = parser.parse_args()

    print(f"{'=' * 50}")
    print(f"  {APP_NAME} Build System")
    print(f"  Version: {args.version}")
    print(f"{'=' * 50}")

    if args.clean:
        print("\n  Cleaning...")
        clean()

    app_dir = build(args.version)
    write_version_file(app_dir, args.version)
    compute_hash(app_dir, args.version)

    print(f"\n{'=' * 50}")
    print(f"  BUILD THANH CONG!")
    print(f"  Output: {app_dir}")
    print(f"  Buoc tiep theo: chay Inno Setup voi installer.iss")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    main()
