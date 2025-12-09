"""应用入口：添加 Qt 平台插件路径自修复，避免 qwindows.dll 未找到错误。"""

import sys
import os
import pathlib
import traceback
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def global_exception_handler(exctype, value, tb):
    """全局异常处理器"""
    print(f"[FATAL ERROR] Unhandled exception: {exctype.__name__}: {value}")
    traceback.print_exception(exctype, value, tb)
    sys.exit(1)

# 安装全局异常处理器
sys.excepthook = global_exception_handler

def _ensure_qt_plugin_path(verbose: bool = True):
    """创建 QApplication 前：
    1. 读取 PyQt5 内置插件路径
    2. 根据平台设置正确的插件路径
    3. 输出诊断信息，方便定位问题
    """
    try:
        import platform
        system = platform.system().lower()

        if system == "windows":
            # Windows 平台逻辑
            from PyQt5.QtCore import QLibraryInfo
            plugins_dir = pathlib.Path(QLibraryInfo.location(QLibraryInfo.PluginsPath))
            platform_dir = plugins_dir / "platforms"
            qwindows = platform_dir / "qwindows.dll"
            if verbose:
                print(f"[QT DIAG] QLibraryInfo.PluginsPath = {plugins_dir}")
                print(f"[QT DIAG] Expected platform dir = {platform_dir}")
                print(f"[QT DIAG] qwindows.dll exists = {qwindows.exists()}")
                print(f"[QT DIAG] Existing env QT_QPA_PLATFORM_PLUGIN_PATH = {os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH')}")

            if qwindows.exists():
                os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platform_dir))
                if verbose:
                    print("[QT DIAG] Using platform dir from QLibraryInfo")
                return

            if verbose:
                print("[QT DIAG] qwindows.dll not found at expected location, scanning site-packages...")
            import site
            candidates = []
            for sp in site.getsitepackages():
                p = pathlib.Path(sp)
                for sub in [p / "PyQt5", p / "PyQt5" / "Qt5", p / "PyQt5" / "Qt" / "plugins", p / "PyQt5" / "Qt5" / "plugins"]:
                    plat = sub / "plugins" / "platforms" if (sub / "plugins" / "platforms").exists() else sub / "platforms"
                    q = plat / "qwindows.dll"
                    if q.exists():
                        candidates.append(q)
            if candidates:
                chosen = candidates[0].parent
                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(chosen)
                if verbose:
                    print(f"[QT DIAG] Found qwindows.dll at {chosen}, environment variable set.")
            else:
                print("[QT DIAG] WARNING: No qwindows.dll found during scan.")
        elif system == "darwin":  # macOS
            # macOS 通常不需要手动设置插件路径，PyQt5 会自动处理
            if verbose:
                print("[QT DIAG] macOS detected, using default Qt plugin paths")
        else:
            if verbose:
                print(f"[QT DIAG] Unsupported platform: {system}")

    except Exception as e:
        if verbose:
            print("[QT DIAG] Exception while ensuring plugin path:", e)
            traceback.print_exc()

_ensure_qt_plugin_path()

from PyQt5.QtCore import QCoreApplication, Qt  # noqa: E402 - 在创建 QApplication 之前设置属性
from PyQt5.QtWidgets import QApplication  # noqa: E402 - 需在设置环境变量后再导入
from PyQt5 import QtGui
from core.bootstrap import Bootstrap  # noqa: E402


def main():
    try:
        print("[APP] Starting 小铠同学 application...")
        # 启动前进行插件诊断
        _ensure_qt_plugin_path(verbose=True)

        # 在创建 QApplication 之前，启用共享 OpenGL 上下文以满足 QtWebEngine 要求
        try:
            aa_share = getattr(Qt, 'AA_ShareOpenGLContexts', None)
            if aa_share is not None:
                QCoreApplication.setAttribute(aa_share, True)
                print("[QT] AA_ShareOpenGLContexts enabled")
        except Exception as e:
            print(f"[QT] Failed to set AA_ShareOpenGLContexts: {e}")

        print("[QT] Creating QApplication...")
        # 诊断后再导入 QApplication 避免路径缺失
        app = QApplication(sys.argv)
        print("[QT] QApplication created successfully")

        # 防止关闭最后一个窗口后应用自动退出（托盘常驻）
        try:
            app.setQuitOnLastWindowClosed(False)
            print("[QT] setQuitOnLastWindowClosed set to False")
        except Exception as e:
            print(f"[QT] Failed to set quit on last window closed: {e}")

        # 设置全局应用图标（替换默认图标）
        try:
            repo_root = pathlib.Path(__file__).resolve().parents[1]
            icon_path = repo_root / 'src' / 'icons' / 'Conduct.png'
            if icon_path.exists():
                app.setWindowIcon(QtGui.QIcon(str(icon_path)))
                print(f"[ICON] Application icon set from {icon_path}")
            else:
                print(f"[ICON] Conduct.png not found at {icon_path}")
        except Exception as e:
            print(f'[ICON] Failed to set app icon: {e}')

        print("[APP] Initializing Bootstrap...")
        bootstrap = Bootstrap()
        print("[APP] Starting application...")
        bootstrap.run()

        print("[APP] Entering main event loop...")
        sys.exit(app.exec_())

    except Exception as e:
        print(f"[FATAL] Application crashed with error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()