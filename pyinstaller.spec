# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 项目根路径与入口
if '__file__' in globals():
    repo_root = Path(__file__).resolve().parent
else:
    # Fallback for cases where __file__ is not defined
    repo_root = Path(os.getcwd())
entry = repo_root / 'python-desktop-translator' / 'src' / 'main.py'

# 图标与资源（macOS 上 --icon 建议使用 .icns；此处交由 build 脚本传入）
datas = []

# 追加资源（示例：应用图标 PNG，会复制到 app 资源目录）
conduct_png = repo_root / 'python-desktop-translator' / 'src' / 'icons' / 'Conduct.png'
if conduct_png.exists():
    datas.append((str(conduct_png), 'icons'))

# QtWebEngine 资源与进程通常由 PyInstaller hooks 自动收集；若运行报缺失，再补充如下：
# from PyInstaller.utils.hooks import collect_data_files
# import PyQt5
# qt_datas = collect_data_files('PyQt5')
# datas += qt_datas

block_cipher = None

a = Analysis(
    [str(entry)],
    pathex=[str(repo_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # PyQt5 基础模块
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        # QtWebEngine 相关
        'PyQt5.QtWebEngine',
        'PyQt5.QtWebEngineCore',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtWebChannel',
        # 其他可能需要的模块
        'sip',
        'pkg_resources',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI桌面助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI 应用
    disable_windowed_traceback=False,
    argv_emulation=True,  # macOS 上处理拖拽文件到图标
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI桌面助手'
)

app = BUNDLE(
    coll,
    name='小铠同学.app',
    icon=None,
    bundle_identifier='com.xiaokai.translator',
)
