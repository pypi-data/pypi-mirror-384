import asyncio
import os
from pathlib import Path

# 使用已安装的库进行导入（非本地源码）
from concurrency_client import ChatClient, Platform

CUR_DIR = Path(__file__).resolve().parent
KEY_FILE = (CUR_DIR.parent / "api_key_txt" / "chatapi.txt").resolve()
MODEL = "gpt-4"


async def test_chatclient():
    has_env = bool(os.getenv("CC_API_KEYS") or os.getenv("CC_API_KEY_FILE") or os.getenv("CHATAPI_API_KEYS") or os.getenv("CHATAPI_API_KEY_FILE"))
    if not has_env and not KEY_FILE.exists():
        print(f"[skip] 未找到密钥文件: {KEY_FILE}，且未设置 CC/CHATAPI 环境变量")
        return

    client = ChatClient(platform="chatapi", model=MODEL)
    try:
        text, usage = await client.call_text("用一句话介绍一下你自己")
        print("[installed.ChatClient.single]", (text or "")[:120], usage)

        results = await client.call_batch([
            "一句话介绍地球",
            "一句话介绍月球",
        ], max_concurrency=2, per_item_retries=1)
        for i, (t, u) in enumerate(results):
            print(f"[installed.ChatClient.batch#{i}]", (t or "")[:120], u)
    finally:
        await client.aclose()


async def test_custom_platform():
    has_env = bool(os.getenv("CC_API_KEYS") or os.getenv("CC_API_KEY_FILE"))
    if has_env:
        client = ChatClient.from_custom(
            api_url="https://api.chataiapi.com/v1",
            model=MODEL,
            # 让库内部自动从 CC_API_KEYS/FILE 解析
        )
    elif KEY_FILE.exists():
        client = ChatClient.from_custom(
            api_url="https://api.chataiapi.com/v1",
            model=MODEL,
            api_key_file=str(KEY_FILE),
            strategy="round_robin",
        )
    else:
        print(f"[skip] 未找到密钥文件: {KEY_FILE}，且未设置 CC 环境变量")
        return
    try:
        text, usage = await client.call_text("说一句中文你好")
        print("[installed.Platform.custom]", (text or "")[:120], usage)
    finally:
        await client.aclose()


async def test_chatclient_stream():
    has_env = bool(os.getenv("CC_API_KEYS") or os.getenv("CC_API_KEY_FILE") or os.getenv("CHATAPI_API_KEYS") or os.getenv("CHATAPI_API_KEY_FILE"))
    if not has_env and not KEY_FILE.exists():
        print(f"[skip] 未找到密钥文件: {KEY_FILE}，且未设置 CC/CHATAPI 环境变量")
        return

    client = ChatClient(platform="chatapi", model=MODEL)
    try:
        text, usage = await client.call_text("这是一个流式测试，请逐步生成一段简短的问候。", stream=True)
        print("[installed.ChatClient.stream]", (text or "")[:120], usage)
    finally:
        await client.aclose()


async def test_custom_platform_stream():
    has_env = bool(os.getenv("CC_API_KEYS") or os.getenv("CC_API_KEY_FILE"))
    if has_env:
        client = ChatClient.from_custom(
            api_url="https://api.chataiapi.com/v1",
            model=MODEL,
        )
    elif KEY_FILE.exists():
        client = ChatClient.from_custom(
            api_url="https://api.chataiapi.com/v1",
            model=MODEL,
            api_key_file=str(KEY_FILE),
            strategy="round_robin",
        )
    else:
        print(f"[skip] 未找到密钥文件: {KEY_FILE}，且未设置 CC 环境变量")
        return
    try:
        text, usage = await client.call_text("这是一个流式测试（自定义平台），请逐步生成一段简短的问候。", stream=True)
        print("[installed.Platform.custom.stream]", (text or "")[:120], usage)
    finally:
        await client.aclose()


async def main():
    await test_chatclient()
    await test_custom_platform()
    # 流式测试（单条）
    await test_chatclient_stream()
    await test_custom_platform_stream()


if __name__ == "__main__":
    asyncio.run(main())
