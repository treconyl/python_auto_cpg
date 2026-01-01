# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os

block_cipher = None

project_dir = Path(os.getcwd()).resolve()
repo_root = project_dir

app = project_dir / "app" / "main.py"
playwright_script = repo_root / "playwright" / "garena-runner.js"
proxy_script = repo_root / "playwright" / "001proxy-test.js"
logo_asset = project_dir / "assets" / "logo.png"

analysis = Analysis(
    [str(app)],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        (str(playwright_script), "playwright"),
        (str(proxy_script), "playwright"),
        (str(logo_asset), "assets"),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="python_auto_cpg",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
