# -*- mode: python ; coding: utf-8 -*-
import os
import site

block_cipher = None
site_packages = site.getsitepackages()[0]

a = Analysis(
    ['../main.py'],  # Путь к вашему главному скрипту относительно папки packaging
    pathex=[],
    binaries=[],
    datas=[(os.path.join(site_packages, 'customtkinter'), 'customtkinter')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='video-flip-fixer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='universal2',
    codesign_identity=None,
    entitlements_file=None,
    icon='../icon.icns',  # Путь к иконке в корне репозитория
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='video-flip-fixer',
)
app = BUNDLE(
    coll,
    name='video-flip-fixer.app',
    icon='../icon.icns',  # Указываем иконку для macOS бандла
    bundle_identifier='com.video-flip-fixer.app',
)

