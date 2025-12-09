import unittest
import os
import sys
os.environ.setdefault("QT_QPA_PLATFORM","windows")
from PyQt5.QtWidgets import QApplication

# 注入 src 到 sys.path 以支持 'ui.' 前缀导入
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(BASE_DIR, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src.ui.bubbles.chat_history_area import ChatHistoryArea


class TestHistoryAreaWidth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication([])

    import sys

    # 确保 src 路径在 sys.path 中
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    SRC_DIR = os.path.join(BASE_DIR, 'src')
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)

    def test_width_fraction_small(self):
        area = ChatHistoryArea()
        area.resize(500, 400)
        styles_user = 'QTextBrowser {background:#fff;}'
        styles_ai = 'QTextBrowser {background:#eee;}'
        msg = area.add_message('user', 'hello', styles_user, styles_ai)
        # fraction ~0.95 => expected ~500*0.95 - 40 = 435
        self.assertGreaterEqual(msg.max_width, 430)
        self.assertLessEqual(msg.max_width, 450)

    def test_width_fraction_medium(self):
        area = ChatHistoryArea()
        area.resize(800, 400)
        styles_user = 'QTextBrowser {background:#fff;}'
        styles_ai = 'QTextBrowser {background:#eee;}'
        msg = area.add_message('ai', 'hello', styles_user, styles_ai)
        # fraction ~0.92 => 800*0.92 - 40 = 696.4
        self.assertGreaterEqual(msg.max_width, 690)
        self.assertLessEqual(msg.max_width, 705)

    def test_width_fraction_large(self):
        area = ChatHistoryArea()
        area.resize(1300, 400)
        styles_user = 'QTextBrowser {background:#fff;}'
        styles_ai = 'QTextBrowser {background:#eee;}'
        msg = area.add_message('ai', 'hello', styles_user, styles_ai)
        # fraction ~0.88 => 1300*0.88 - 40 = 1104
        self.assertGreaterEqual(msg.max_width, 1095)
        self.assertLessEqual(msg.max_width, 1115)


if __name__ == '__main__':
    unittest.main()