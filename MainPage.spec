# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['MainPage.py'],
    pathex=[],
    binaries=[],
    datas=[('config.ini', '.'), ('background.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='MoYuFish',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['Icon.icns'],
)
app = BUNDLE(
    exe,
    name='MoYuFish.app',
    icon='logo.icns',
    bundle_identifier=None,
)
