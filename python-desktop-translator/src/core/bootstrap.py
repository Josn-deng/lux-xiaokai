"""应用启动引导：实例化配置、AI客户端与服务，并启动主悬浮窗。"""

from __future__ import annotations

from typing import Optional

from config.app_config import AppConfig
from services.ai_client import AIClient
from services.translation_service import TranslationService


class Bootstrap:
    def __init__(self):
        self.config: AppConfig = AppConfig()
        self.client: AIClient = AIClient(self.config.ai_server, self.config.api_key)
        self.translation_service: TranslationService = TranslationService(self.client, self.config)
        self._floating_window = None  # 延迟导入 UI

    def run(self):
        from ui.floating_window import FloatingWindow  # 局部导入避免循环引用
        self._floating_window = FloatingWindow(self.config, self.client, self.translation_service)
        self._floating_window.show()

    @property
    def window(self) -> Optional[object]:  # pragma: no cover - 仅用于运行期访问
        return self._floating_window
