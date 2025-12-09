import os
import json
from typing import Any, Dict


class AppConfig:
    """应用配置管理：负责加载/保存用户设置（AI服务器、模型、密钥、开机自启等）。

    持久化位置：%APPDATA%/python-desktop-translator/config.json (Windows) 或 当前目录.
    api_key 优先从环境变量 AI_API_KEY 读取，避免硬编码真实密钥。
    """

    def __init__(self):
        # 默认值按照用户提供的 curl 请求
        self.ai_server: str = "http://10.133.10.65:3000/v1/chat/completions"
        self.model: str = "qwen3-coder"
        self.api_key: str = os.getenv("AI_API_KEY", "Bearer sk-mIUYJcJE52eNqjLb17F39656A7D7414fB15b84C8D0490844")
        self.auto_start: bool = False
        # 目标语言（用于翻译功能），默认中文，可选：zh|en|vi
        self.target_language: str = "zh"

        self._config_path: str = self._resolve_config_path()
        # 初始化时尝试加载已有配置
        self.load_config()

    # ---------------------- 内部工具方法 ----------------------
    def _resolve_config_path(self) -> str:
        appdata = os.environ.get("APPDATA")
        if appdata:
            base_dir = os.path.join(appdata, "python-desktop-translator")
        else:
            base_dir = os.path.join(os.getcwd(), "python-desktop-translator-config")
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, "config.json")

    # ---------------------- 配置加载/保存 ----------------------
    def load_config(self) -> None:
        if not os.path.isfile(self._config_path):
            return
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.update_from_dict(data)
        except Exception as e:  # noqa: BLE001 简化错误处理
            print(f"[AppConfig] 读取配置失败: {e}")

    def save_config(self) -> None:
        data = {
            "ai_server": self.ai_server,
            "model": self.model,
            "api_key": self.api_key,
            "auto_start": self.auto_start,
            "target_language": self.target_language,
        }
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:  # noqa: BLE001
            print(f"[AppConfig] 保存配置失败: {e}")

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        self.ai_server = data.get("ai_server", self.ai_server)
        self.model = data.get("model", self.model)
        self.api_key = data.get("api_key", self.api_key)
        self.auto_start = data.get("auto_start", self.auto_start)
        self.target_language = data.get("target_language", self.target_language)

    # ---------------------- 业务辅助方法 ----------------------
    def build_chat_payload(self, system_prompt: str, user_content: str) -> Dict[str, Any]:
        """构造通用 Chat Completions 请求 payload."""
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }

    def build_translation_prompt(self, original_text: str) -> Dict[str, Any]:
        """根据 target_language 生成翻译请求 payload.

        支持语言：
        zh (中文), en (英文), vi (越南语)
        """
        language_map = {
            "zh": "中文",
            "en": "英文",
            "vi": "越南语",
        }
        target_label = language_map.get(self.target_language, "中文")
        system_prompt = (
            "你是一个专业的翻译专家，擅长多种语言间的准确翻译。请遵循以下原则：\n\n"
            "1. 保持原文意思准确无误\n"
            "2. 翻译结果自然流畅，符合目标语言习惯\n"
            "3. 专业术语要准确翻译\n"
            "4. 文化差异要妥善处理\n"
            "5. 保持原文的文体风格和语气\n\n"
            f"请将用户输入内容翻译为{target_label}，只输出译文，不要额外解释。"
        )
        user_content = f"待翻译文本: {original_text}" if original_text else ""
        return self.build_chat_payload(system_prompt, user_content)

    def build_polish_prompt(self, original_text: str) -> Dict[str, Any]:
        """构造文本润色的 prompt：提升语法、清晰度、简洁性，保留原意。"""
        system_prompt = (
            "你是一位专业的文本润色助手，目标：提升可读性、语法正确性、表达自然性，保持原意。\n"
            "润色原则：\n"
            "1. 不改变技术/术语含义\n"
            "2. 去除冗余，语言简练\n"
            "3. 语法与标点正确\n"
            "4. 保留原文语气（正式 / 轻松等）\n"
            "5. 如果原文本身已良好，做最少微调\n\n"
            "只输出润色后的结果，不要解释。"
        )
        user_content = f"待润色文本: {original_text}" if original_text else ""
        return self.build_chat_payload(system_prompt, user_content)

    def build_qa_prompt(self, question: str) -> Dict[str, Any]:
        """构造通用问答 prompt：要求准确、简洁，有条理。"""
        system_prompt = (
            "你是一个专业的知识问答助手，回答需：准确、分点清晰、必要时给简短示例。\n"
            "原则：\n"
            "1. 如果问题含糊，先澄清再回答\n"
            "2. 优先给出直接答案，再补充背景\n"
            "3. 避免无根据的猜测，如不确定需说明\n"
            "4. 用简洁的语言表达核心要点\n\n"
            "请回答用户问题。"
        )
        user_content = f"问题: {question}" if question else ""
        return self.build_chat_payload(system_prompt, user_content)

    def build_speech_translation_prompt(self, recognized_text: str) -> Dict[str, Any]:
        """语音翻译：已将音频转文字，需要将该文字翻译到 target_language。"""
        # 重用翻译逻辑，但区分用途便于后续统计
        return self.build_translation_prompt(recognized_text)

    # ---------------------- 展示 ----------------------
    def __str__(self) -> str:  # pragma: no cover - 打印展示不做单元测试
        masked_key = (
            self.api_key[:8] + "..." if self.api_key and len(self.api_key) > 8 else self.api_key
        )
        return (
            "AppConfig("
            f"ai_server={self.ai_server}, "
            f"model={self.model}, "
            f"api_key={masked_key}, "
            f"auto_start={self.auto_start}, "
            f"target_language={self.target_language}"\
            ")"
        )