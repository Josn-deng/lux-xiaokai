import platform
from typing import Literal, Callable
from PyQt5 import QtCore

try:
    import winreg  # Windows 深浅色检测
except ImportError:   # 非 Windows 环境降级
    winreg = None

ThemeType = Literal['light', 'dark']


class ThemeManager(QtCore.QObject):
    """全局主题管理。提供自动检测与切换信号。"""
    theme_changed = QtCore.pyqtSignal(str)  # 主题名称
    # 当 AI 返回完成（流结束）时发射，用于切换悬浮窗完成图标等
    ai_response_complete = QtCore.pyqtSignal()

    _instance = None

    LIGHT_STYLES = {
        'message_user': "QTextBrowser {background-color:#e3f2fd; border-radius:18px; padding:10px 10px; font-family: 'Segoe UI', 'Microsoft YaHei', 'SimHei', sans-serif; font-size:13px; color:#222;}",
        'message_ai': "QTextBrowser {background-color:#f0f8ff; border-radius:18px; padding:10px 10px; font-family: 'Segoe UI', 'Microsoft YaHei', 'SimHei', sans-serif; font-size:13px; color:#222;}",
        'window_bg': "QWidget {background:#ffffff;}"
    }

    DARK_STYLES = {
        'message_user': "QTextBrowser {background-color:#1e3a56; border-radius:18px; padding:10px 10px; font-family: 'Segoe UI', 'Microsoft YaHei', 'SimHei', sans-serif; font-size:13px; color:#ddd;}",
        'message_ai': "QTextBrowser {background-color:#1f2f3a; border-radius:18px; padding:10px 10px; font-family: 'Segoe UI', 'Microsoft YaHei', 'SimHei', sans-serif; font-size:13px; color:#ddd;}",
        'window_bg': "QWidget {background:#111b24;}"
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._theme: ThemeType = self._detect_system_theme()

    @property
    def theme(self) -> ThemeType:
        return self._theme

    def toggle_theme(self):
        self._theme = 'dark' if self._theme == 'light' else 'light'
        self.theme_changed.emit(self._theme)

    def set_theme(self, theme: ThemeType):
        if theme not in ('light', 'dark'):
            return
        if self._theme != theme:
            self._theme = theme
            self.theme_changed.emit(self._theme)

    def get_styles(self):
        return self.DARK_STYLES if self._theme == 'dark' else self.LIGHT_STYLES

    def style_for(self, key: str) -> str:
        return self.get_styles().get(key, '')

    def _detect_system_theme(self) -> ThemeType:
        if platform.system() != 'Windows' or winreg is None:
            return 'light'
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                # 1 = Light, 0 = Dark for AppsUseLightTheme
                value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
                return 'light' if value == 1 else 'dark'
        except Exception:
            return 'light'

theme_manager = ThemeManager()