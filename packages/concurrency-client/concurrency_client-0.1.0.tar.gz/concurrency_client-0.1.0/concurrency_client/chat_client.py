# chat_client.py
from __future__ import annotations
import asyncio
from typing import List, Optional, Tuple, Dict, Any

from .platform import Platform
from .universal_api_client import CompletionUsage, UniversalApiClient


class ChatClient:
    """聚合门面，统一常用对话与多模态调用。

    约定：所有方法返回 (text, usage|None)。
    - text: 平台返回的文本内容（或 JSON 字符串）
    - usage: 令牌用量对象，流式/不支持用量时为 None
    """

    def __init__(self, platform: str, model: str):
        self.platform = platform
        self.model = model
        self._client: UniversalApiClient = Platform.create_client(platform=platform, model=model)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def call_text(self, user_prompt: str, system_prompt: str = "", **kwargs: Any) -> Tuple[Optional[str], Optional[CompletionUsage]]:
        messages: List[Dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return await self._client.call(messages=messages, **kwargs)

    async def call_json(self, user_prompt: str, system_prompt: str = "", **kwargs: Any) -> Tuple[Optional[str], Optional[CompletionUsage]]:
        # 统一通过 response_format 请求 JSON
        kwargs = {**kwargs, "response_format": {"type": "json_object"}}
        return await self.call_text(user_prompt=user_prompt, system_prompt=system_prompt, **kwargs)

    async def call_with_single_image(
        self,
        user_prompt: str,
        base64_image: str,
        system_prompt: str = "",
        mime_type: str = "image/png",
        **kwargs: Any,
    ) -> Tuple[Optional[str], Optional[CompletionUsage]]:
        # 构造 OpenAI Chat Completions 风格的多模态消息
        content: List[Dict[str, Any]] = [
            {"type": "text", "text": user_prompt}
        ]
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
        })
        messages: List[Dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})
        return await self._client.call(messages=messages, **kwargs)

    async def call_batch(
        self,
        user_prompts: List[str],
        system_prompt: str = "",
        *,
        max_concurrency: Optional[int] = None,
        per_item_retries: int = 0,
        backoff_base: float = 1.0,
        backoff_factor: float = 2.0,
        **kwargs: Any,
    ) -> List[Tuple[Optional[str], Optional[CompletionUsage]]]:
        """批量文本调用，返回与单次一致的 (text, usage) 列表。
        - max_concurrency: 最大并发数，None 表示不限制（按事件循环默认调度）
        - per_item_retries: 单条请求的最大重试次数
        - backoff_base/backoff_factor: 指数退避参数（首次等待 backoff_base，随后乘以 factor）
        """
        sem = asyncio.Semaphore(max_concurrency) if max_concurrency and max_concurrency > 0 else None

        async def _invoke_once(prompt: str):
            return await self.call_text(user_prompt=prompt, system_prompt=system_prompt, **kwargs)

        async def _with_retry(prompt: str):
            attempt = 0
            delay = backoff_base
            while True:
                try:
                    if sem is None:
                        return await _invoke_once(prompt)
                    async with sem:
                        return await _invoke_once(prompt)
                except Exception:
                    if attempt >= per_item_retries:
                        # 将失败以 (None, None) 形式返回，避免 raise 终止整体批量
                        return None, None
                    await asyncio.sleep(max(0.0, delay))
                    delay *= backoff_factor
                    attempt += 1

        tasks = [asyncio.create_task(_with_retry(p)) for p in user_prompts]
        return await asyncio.gather(*tasks)

    async def call_with_multi_images(
        self,
        user_prompt: str,
        base64_images: List[str],
        system_prompt: str = "",
        mime_type: str = "image/png",
        **kwargs: Any,
    ) -> Tuple[Optional[str], Optional[CompletionUsage]]:
        content: List[Dict[str, Any]] = [
            {"type": "text", "text": user_prompt}
        ]
        for img in base64_images:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{img}"}
            })
        messages: List[Dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})
        return await self._client.call(messages=messages, **kwargs)
