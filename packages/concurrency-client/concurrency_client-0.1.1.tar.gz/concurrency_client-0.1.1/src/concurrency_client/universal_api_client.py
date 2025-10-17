# universal_client.py
import asyncio
import logging
from collections import namedtuple
from typing import Dict, List, Optional, Tuple

from openai import APIError, AsyncOpenAI, AuthenticationError

from .api_pool import ApiKeyPool

CompletionUsage = namedtuple('CompletionUsage', ['prompt_tokens', 'completion_tokens', 'total_tokens'])

class UniversalApiClient:
    """
    一个通用的API客户端，支持可配置的API URL、模型和密钥池。
    通过为每个请求创建一次性客户端来与类OpenAI的API进行交互。
    """
    def __init__(self, key_pool: ApiKeyPool, api_url: str, model: str):
        """
        初始化通用API客户端。

        :param key_pool: ApiKeyPool的实例，用于管理API密钥。
        :param api_url: 目标API的基础URL (例如, "https://api.deepseek.com").
        :param model: 要使用的模型的名称。
        """
        self.api_url = api_url
        self.model = model
        self.key_pool = key_pool

    async def aclose(self):
        """
        清理资源。
        """
        if hasattr(self, 'key_pool'):
            self.key_pool.cleanup()

    async def _process_stream(self, stream) -> str:
        """处理流式输出，将其转换为完整文本"""
        result = ""
        async for chunk in stream:
            try:
                content = chunk.choices[0].delta.content
                if content:
                    result += content
            except Exception as e:
                logging.error(f"处理流式输出时出错: {e}")
                continue
        return result

    async def call(self, messages: List[Dict[str, str]], max_retries: int = 3, timeout: int = 1400, **kwargs) -> Optional[Tuple[str, Optional[CompletionUsage]]]:
        """
        使用从池中获取的密钥向API发送请求。
        对于每个请求，都会创建一个新的一次性客户端。

        :param messages: 一个消息列表，每个消息都是一个包含'role'和'content'的字典。
        :param max_retries: 最大重试次数。
        :param **kwargs: 额外的API参数，如 response_format, max_tokens 等。
        :return: 一个包含 (文本内容, usage对象或None) 的元组，如果失败则返回 (None, None)。
           return_example: ("I'm doing well, thank you for asking! How are you?", CompletionUsage(prompt_tokens=7, completion_tokens=15, total_tokens=127))
        """
        for attempt in range(max_retries):
            key = self.key_pool.get_key()
            if not key:
                logging.error("无法从池中获取API密钥。")
                await asyncio.sleep(1)
                continue

            try:
                # 使用 async with 确保每次请求后客户端都被正确关闭
                async with AsyncOpenAI(
                    api_key=key,
                    base_url=self.api_url,
                    timeout=timeout,
                    max_retries=0  # 我们在外部处理重试逻辑
                ) as client:

                    # 准备API调用参数
                    create_params = {
                        'model': self.model,
                        'messages': messages,
                        **kwargs  # 合并所有额外参数
                    }
                    
                    # 如果是流式输出
                    if 'stream' in kwargs and kwargs['stream']:
                        stream = await client.chat.completions.create(**create_params)
                        res = await self._process_stream(stream)
                        usage = None
                    else:
                        response = await client.chat.completions.create(**create_params)
                        res = response.choices[0].message.content
                        usage_obj = response.usage
                    
                        usage = CompletionUsage(
                            prompt_tokens=usage_obj.prompt_tokens,
                            completion_tokens=usage_obj.completion_tokens,
                            total_tokens=usage_obj.total_tokens
                        )
                    
                    return res, usage

            except AuthenticationError:
                logging.error(f"[尝试 {attempt+1}] 认证错误，API密钥无效或已过期: {key}。正在从池中删除。")
                self.key_pool.delete_key(key)
                continue
            
            except APIError as e:
                # logging.warning(f"[尝试 {attempt+1}] 发生API错误: {e.__class__.__name__} - {e}。将在1秒后重试。")
                logging.warning(f"[尝试 {attempt+1}] 发生API错误: {e.__class__.__name__} - {e}。将在1秒后重试。", exc_info=True)
                await asyncio.sleep(1)
                # raise Exception('APIError')

            except Exception as e:
                logging.error(f"[尝试 {attempt+1}] 发生意外错误: {e}", exc_info=True)
                await asyncio.sleep(1)
            
            finally:
                if key:
                    self.key_pool.release_key(key)

        logging.error("所有重试均失败。")
        return None, None
