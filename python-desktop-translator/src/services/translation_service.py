"""翻译服务封装，适配新的 AIClient 与 AppConfig。

核心职责：
1. 将纯文本翻译请求委托给 AIClient.translate
2. 支持批量翻译
3. 预留语言检测与支持语言查询（当前 One-API 接口未提供，抛出 NotImplementedError）

source_language 在当前多轮 prompt 中不单独传递；如果后端未来需要，可在 AppConfig 中新增字段。
"""

from __future__ import annotations

from typing import List

from config.app_config import AppConfig
from services.ai_client import AIClient


class TranslationService:
    def __init__(self, ai_client: AIClient, config: AppConfig):
        self.ai_client = ai_client
        self.config = config

    def translate(self, text: str) -> str:
        if not text:
            return ""
        return self.ai_client.translate(self.config, text)

    def batch_translate(self, texts: List[str]) -> List[str]:
        return [self.translate(t) for t in texts]

    def detect_language(self, text: str) -> str:  # pragma: no cover - 未实现
        raise NotImplementedError("当前后端未提供语言检测接口")

    def get_supported_languages(self) -> List[str]:  # pragma: no cover - 未实现
        # 与 AppConfig target_language 约定的枚举保持一致
        return ["zh", "en", "vi"]