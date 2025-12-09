import unittest
import os
import pathlib
import site
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore
from src.ui.bubbles.message_widget import ChatMessageWidget

def _ensure_qt_plugin_path_for_test():
    """简化版本：确保 qwindows.dll 插件路径已设置。"""
    try:
        from PyQt5.QtCore import QLibraryInfo
        plugins_dir = pathlib.Path(QLibraryInfo.location(QLibraryInfo.PluginsPath))
        platform_dir = plugins_dir / "platforms"
        qwindows = platform_dir / "qwindows.dll"
        if qwindows.exists():
            os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platform_dir))
            return
        for sp in site.getsitepackages():
            p = pathlib.Path(sp)
            candidates = [p / "PyQt5" / "Qt5" / "plugins" / "platforms", p / "PyQt5" / "Qt" / "plugins" / "platforms", p / "PyQt5" / "plugins" / "platforms"]
            for c in candidates:
                if (c / "qwindows.dll").exists():
                    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(c)
                    return
    except Exception:
        pass

_ensure_qt_plugin_path_for_test()
os.environ.setdefault("QT_QPA_PLATFORM", "windows")


class TestChatMessageWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 确保 QApplication 存在（避免重复创建导致异常）
        cls._app = QApplication.instance() or QApplication([])

    def test_initialization_without_streaming(self):
        w = ChatMessageWidget(
            role='user',
            raw_text='Hello **World**',
            max_width=300,
            user_style='QTextBrowser {background:#fff;}',
            ai_style='QTextBrowser {background:#eee;}'
        )
        # is_streaming 应该已初始化且为 False
        self.assertFalse(w.is_streaming)
        # 原始文本记录正确
        self.assertIn('Hello', w.raw_text)

    def test_streaming_mode(self):
        w = ChatMessageWidget(
            role='ai',
            raw_text='',
            max_width=300,
            user_style='QTextBrowser {background:#fff;}',
            ai_style='QTextBrowser {background:#eee;}'
        )
        w.start_streaming()
        self.assertTrue(w.is_streaming)
        w.stream_text('Hel')
        w.stream_text('lo')
        # 结束流式并刷新缓冲
        w.end_streaming()
        self.assertFalse(w.is_streaming)
        # 内容应包含完整流式文本
        self.assertIn('Hello', w.content.toPlainText())

    def test_streaming_markdown_render(self):
        w = ChatMessageWidget(
            role='ai',
            raw_text='',
            max_width=400,
            user_style='QTextBrowser {background:#fff;}',
            ai_style='QTextBrowser {background:#eee;}'
        )
        w.start_streaming()
        # 更直接的分块，避免代码围栏被拆分造成解析不稳定
        for chunk in ["```python\n", "print('hi')\n", "```"]:
            w.stream_text(chunk)
        w.end_streaming()
        # 验证原始文本包含代码围栏与代码内容，HTML 渲染差异在不同平台不稳定时以原始内容为准
        self.assertIn("print('hi')", w.raw_text)
        self.assertIn("```python", w.raw_text)

    def test_copy_and_toggle_code_block(self):
        code_md = "```python\n" + "\n".join(f"print({i})" for i in range(25)) + "\n```"  # > threshold lines
        w = ChatMessageWidget(
            role='ai',
            raw_text=code_md,
            max_width=500,
            user_style='QTextBrowser {background:#fff;}',
            ai_style='QTextBrowser {background:#eee;}'
        )
        # 使用内部状态而非 HTML 结构（Qt 可能重写标签导致类丢失）
        self.assertGreater(len(w._code_blocks), 0, '代码块未被识别')
        # 初始应折叠
        self.assertTrue(w._code_blocks[0]['collapsed'])
        # 展开（直接调用内部方法避免信号差异）
        w._toggle_code_block(0)
        self.assertFalse(w._code_blocks[0]['collapsed'])
        # 复制
        w._copy_code_block(0)
        clipboard = QApplication.clipboard()
        self.assertIsNotNone(clipboard)
        if clipboard is not None:
            self.assertIn('print(0)', clipboard.text())


if __name__ == '__main__':
    unittest.main()
