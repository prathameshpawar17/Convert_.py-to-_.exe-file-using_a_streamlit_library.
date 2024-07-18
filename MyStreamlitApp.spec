# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['streamlit', 'altair', 'pandas', 'importlib_resources']
hiddenimports += collect_submodules('importlib_resources')


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[("P:\\computer language\\project's\\python to EXE file transfer\\streamlit_exe_project\\venv\\Scripts\\streamlit.EXE", 'streamlit')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['setuptools', 'distutils'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MyStreamlitApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
