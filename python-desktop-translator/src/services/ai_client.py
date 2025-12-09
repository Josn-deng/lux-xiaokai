"""AI 接口客户端，兼容 One-API/OpenAI 风格错误结构并分类异常。

当前后端使用的是 One-API 代理的 /v1/chat/completions 接口。这里统一封装：
1. 支持网络/超时重试（指数退避）
2. 针对常见错误分类：
   - 密钥失效/过期: AuthenticationError
   - 模型不存在: ModelNotFoundError
   - 速率限制: RateLimitError
   - 服务端错误: ServerError
   - 非法响应/解析失败: InvalidResponseError
3. 返回精简的文本结果（提取 choices[0].message.content）

后续其它功能（翻译/润色/问答）均可基于 chat() 构造不同的 system prompt。
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class AIClientError(Exception):
    """基础异常。"""


class AuthenticationError(AIClientError):
    """API 密钥无效/过期。"""


class ModelNotFoundError(AIClientError):
    """模型不存在。"""


class RateLimitError(AIClientError):
    """触发限流。"""


class ServerError(AIClientError):
    """服务器内部错误。"""


class InvalidResponseError(AIClientError):
    """返回格式不符合预期。"""


TRANSIENT_STATUS = {429, 500, 502, 503, 504}


class AIClient:
    def __init__(self, server_url: str, api_key: str, timeout: int = 30, max_retries: int = 3):
        # server_url 期望为完整的 chat completions 端点: http://host:port/v1/chat/completions
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key.replace("Bearer ", "") if api_key else ""
        self.timeout = timeout
        self.max_retries = max_retries

    # --------------------- 对外主方法 ---------------------
    def chat(self, payload: Dict[str, Any]) -> str:
        """发送 Chat Completions 请求，返回主消息文本。"""
        data = self._post_with_retry(payload)
        try:
            choices = data.get("choices")
            if not choices:
                raise InvalidResponseError("响应中缺少 choices 字段或为空")
            message = choices[0].get("message") or {}
            content = message.get("content")
            if not content:
                raise InvalidResponseError("响应中 message.content 为空")
            return content
        except (KeyError, TypeError) as e:  # noqa: BLE001
            raise InvalidResponseError(f"解析响应失败: {e}") from e

    def chat_stream(self, payload: Dict[str, Any]):
        """发送 Chat Completions 请求，流式返回主消息文本。
        
        Yields:
            str: AI响应的每个文本片段
        """
        # 添加stream参数以启用流式输出
        payload_with_stream = payload.copy()
        payload_with_stream["stream"] = True
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            response = requests.post(
                self.server_url,
                json=payload_with_stream,
                headers=headers,
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code >= 400:
                self._raise_for_status(response)
            
            # 处理流式响应
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        data_str = decoded_line[6:]  # 移除 'data: ' 前缀
                        if data_str == '[DONE]':
                            break
                        try:
                            import json
                            chunk_data = json.loads(data_str)
                            choices = chunk_data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except Exception:
                            # 忽略解析错误的行
                            continue
        except Exception as e:
            raise AIClientError(f"流式请求失败: {e}") from e

    # --------------------- 翻译等语义快捷方法 ---------------------
    def translate(self, config, original_text: str) -> str:
        """基于 AppConfig 构造翻译请求并返回译文。"""
        payload = config.build_translation_prompt(original_text)
        return self.chat(payload)

    def polish_text(self, config, original_text: str) -> str:
        """文本润色。"""
        payload = config.build_polish_prompt(original_text)
        return self.chat(payload)

    def ask_question(self, config, question: str) -> str:
        """问答。"""
        payload = config.build_qa_prompt(question)
        return self.chat(payload)

    def speech_translate(self, config, recognized_text: str) -> str:
        """语音翻译：传入已识别的文本。"""
        payload = config.build_speech_translation_prompt(recognized_text)
        return self.chat(payload)

    # --------------------- 核心请求与错误处理 ---------------------
    def _post_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        attempt = 0
        backoff = 1.0
        last_error: Optional[Exception] = None
        while attempt <= self.max_retries:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                resp = requests.post(
                    self.server_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                if resp.status_code >= 400:
                    self._raise_for_status(resp)
                # 尝试解析 JSON
                try:
                    return resp.json()
                except Exception as e:  # noqa: BLE001
                    raise InvalidResponseError(f"无法解析 JSON: {e}") from e
            except RateLimitError as e:  # 可重试
                last_error = e
                logger.warning("RateLimit: 第 %s 次尝试: %s", attempt + 1, e)
            except ServerError as e:  # 可重试
                last_error = e
                logger.warning("ServerError: 第 %s 次尝试: %s", attempt + 1, e)
            except (requests.Timeout, requests.ConnectionError) as e:  # noqa: PERF401 BLE001 - 网络错误重试
                last_error = e
                logger.warning("网络错误重试(%s/%s): %s", attempt + 1, self.max_retries, e)
            except AIClientError as e:  # 其它分类错误不再重试
                raise e
            attempt += 1
            if attempt > self.max_retries:
                break
            time.sleep(backoff)
            backoff *= 2  # 指数退避
        # 如果循环退出且没有成功
        if last_error:
            raise last_error
        raise AIClientError("请求失败但没有捕获到具体异常。")

    # --------------------- 状态码与错误结构解析 ---------------------
    def _raise_for_status(self, resp: requests.Response) -> None:
        status = resp.status_code
        text = resp.text or ""
        err_json: Dict[str, Any] = {}
        try:
            err_json = resp.json()
        except Exception:  # noqa: BLE001 - 不可解析时忽略，使用纯文本
            pass
        # OpenAI/One-API 错误结构通常为 {"error": {"message": "...", "code": "..."}}
        error_obj = err_json.get("error") if isinstance(err_json, dict) else None
        message = ""
        code = ""
        if isinstance(error_obj, dict):
            message = str(error_obj.get("message", ""))
            code = str(error_obj.get("code", ""))
        else:
            # 如果没有标准结构，用响应文本近似
            message = message or text

        lower_msg = message.lower()
        lower_code = code.lower()

        # 分类逻辑
        if status in {401, 403} or "invalid api key" in lower_msg or "key" in lower_msg and "expired" in lower_msg:
            raise AuthenticationError(f"认证失败/密钥失效: {message}")
        if status == 404 or "model" in lower_msg and "not" in lower_msg and "exist" in lower_msg or lower_code == "model_not_found":
            raise ModelNotFoundError(f"模型不存在: {message}")
        if status == 429 or lower_code == "rate_limit_exceeded" or "rate limit" in lower_msg:
            raise RateLimitError(f"触发限流: {message}")
        if status >= 500:
            raise ServerError(f"服务端错误({status}): {message}")
        # 其它 4xx 视为请求不合法或无法处理
        raise AIClientError(f"请求失败({status}): {message}")
