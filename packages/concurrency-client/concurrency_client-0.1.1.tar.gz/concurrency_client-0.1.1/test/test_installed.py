import asyncio
from pathlib import Path

# 使用已安装的库进行导入（非本地源码）
from concurrency_client import ChatClient, Platform

CUR_DIR = Path(__file__).resolve().parent
KEY_FILE = (CUR_DIR.parent / "api_key_txt" / "chatapi.txt").resolve()
MODEL = "gpt-4"


async def test_chatclient():
    if not KEY_FILE.exists():
        print(f"[skip] 未找到密钥文件: {KEY_FILE}")
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
    if not KEY_FILE.exists():
        print(f"[skip] 未找到密钥文件: {KEY_FILE}")
        return

    client = Platform.create_client_custom(
        api_url="https://api.chataiapi.com/v1",
        api_key_file=str(KEY_FILE),
        model=MODEL,
        strategy="round_robin",
    )
    try:
        text, usage = await client.call(messages=[{"role": "user", "content": "说一句中文你好"}], stream=False)
        print("[installed.Platform.custom]", (text or "")[:120], usage)
    finally:
        await client.aclose()


async def main():
    await test_chatclient()
    await test_custom_platform()


if __name__ == "__main__":
    asyncio.run(main())
