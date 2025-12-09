import sys
import os
import pathlib
import traceback

# --- 确保 Qt 平台插件路径（参考 main.py 的自修复逻辑） ---
def _ensure_qt_plugin_path():
    try:
        from PyQt5.QtCore import QLibraryInfo
        plugins_dir = pathlib.Path(QLibraryInfo.location(QLibraryInfo.PluginsPath))
        platform_dir = plugins_dir / "platforms"
        qwindows = platform_dir / "qwindows.dll"
        if qwindows.exists():
            os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platform_dir))
            return
        import site
        for sp in site.getsitepackages():
            p = pathlib.Path(sp)
            for sub in [p / "PyQt5", p / "PyQt5" / "Qt5", p / "PyQt5" / "Qt" / "plugins", p / "PyQt5" / "Qt5" / "plugins"]:
                plat = sub / "plugins" / "platforms" if (sub / "plugins" / "platforms").exists() else sub / "platforms"
                q = plat / "qwindows.dll"
                if q.exists():
                    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(q.parent)
                    return
    except Exception:
        traceback.print_exc()

_ensure_qt_plugin_path()

from PyQt5 import QtWidgets, QtCore

# 确保能导入 src
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from ui.bubbles.message_widget import ChatMessageWidget

TEST_MD = """
1. **超大规模参数**

这是段普通文本，包含 *斜体* 和 **粗体**，以及行内代码 `print('hello')`。

代码块示例：
```python
for i in range(3):
    print(i)
```
"""

out_dir = os.path.join(ROOT, 'out_test')
os.makedirs(out_dir, exist_ok=True)
out_png = os.path.join(out_dir, 'message_widget_render.png')

app = QtWidgets.QApplication([])
# 创建 widget
w = ChatMessageWidget('ai', '', 420, "QTextBrowser {background:#fff3e0;}", "QTextBrowser {background:#f0f8ff;}")
w.set_markdown(TEST_MD)
# 显示并截图后退出
w.show()

# 允许布局/样式应用
QtCore.QTimer.singleShot(400, lambda: None)

def save_and_quit():
    try:
        pix = w.grab()
        pix.save(out_png)
        print('SAVED_PNG', out_png)
    except Exception as e:
        import traceback; traceback.print_exc(); print('SAVE_FAIL', e)
    finally:
        app.quit()

QtCore.QTimer.singleShot(700, save_and_quit)
app.exec_()
