# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Admin\\Desktop\\TEMPLE-PYQT6\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Admin\\Desktop\\TEMPLE-PYQT6\\icons', 'icons'), ('C:\\Users\\Admin\\Desktop\\TEMPLE-PYQT6\\i18n', 'i18n'), ('C:\\Users\\Admin\\Desktop\\TEMPLE-PYQT6\\.env', '.')],
    hiddenimports=['PyQt6.QtSvg', 'PyQt6.QtSvgWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'xmlrpc', 'pydoc', 'doctest', 'test', 'server', 'fastapi', 'uvicorn', 'psycopg2', 'pyjwt', 'python-dotenv', 'bcrypt'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MaxHub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\Admin\\Desktop\\TEMPLE-PYQT6\\icons\\app\\icon-taskbar.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MaxHub',
)
