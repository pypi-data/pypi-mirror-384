# concurrency-client

一个针对 OpenAI 兼容 Chat API 的轻量抽象与聚合门面，支持异步、密钥池与批量并发控制。

## 安装（本地打包后）
```bash
pip install .
# 或构建分发包：
python -m build
pip install dist/concurrency_client-0.1.0-py3-none-any.whl
```

## 快速开始
```python
import asyncio
from concurrency_client import ChatClient, Platform

async def main():
    # 使用内置平台（示例：chatapi）
    client = ChatClient(platform="chatapi", model="gpt-4")
    text, usage = await client.call_text("你好，简单自我介绍一下")
    print(text, usage)
    await client.aclose()

    # 使用自定义平台
    custom = Platform.create_client_custom(
        api_url="https://api.chataiapi.com/v1",
        api_key_file="./api_key_txt/chatapi.txt",
        model="gpt-4",
        strategy="round_robin",
    )
    text, usage = await custom.call(messages=[{"role": "user", "content": "说一句中文你好"}], stream=False)
    print(text, usage)
    await custom.aclose()

asyncio.run(main())
```

## 主要特性
- **统一门面**：`ChatClient.call_text/call_json/call_with_single_image/call_with_multi_images/call_batch`
- **批量并发**：`call_batch(max_concurrency, per_item_retries, backoff_*)`
- **密钥池**：`ApiKeyPool(strategy=random|round_robin)`
- **自定义平台**：`Platform.create_client_custom(api_url, api_key_file, model)`

## 目录结构
```
concurrency_client/
  concurrency_client/
    __init__.py
    api_pool.py
    universal_api_client.py
    platform.py
    chat_client.py
  api_key_txt/
    chatapi.txt  # 本地密钥，勿提交
  demo_test.py   # 本地演示脚本，勿打包
  pyproject.toml
  README.md
  LICENSE
```

## 注意
- 不要将 `api_key_txt/` 提交到版本库或打包到发布物。
- 示例依赖 OpenAI 兼容接口（如 ChatAPI）。不同平台的字段可能略有差异，建议优先使用 `ChatClient` 与 OpenAI 风格消息体。

## 许可证
MIT
