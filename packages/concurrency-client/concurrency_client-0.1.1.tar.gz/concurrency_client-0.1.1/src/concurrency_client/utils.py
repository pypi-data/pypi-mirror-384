# utils.py
import os
from pathlib import Path
from typing import List, Optional

def load_api_keys(file_path: str) -> List[str]:
    """从文件中加载API密钥，每行一个，忽略空行与首尾空白。
    若文件不存在则返回空列表。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def _split_keys(raw: str) -> List[str]:
    items = []
    for part in raw.replace("\r", "\n").split("\n"):
        for seg in part.split(','):
            seg = seg.strip()
            if seg:
                items.append(seg)
    # 去重保持顺序
    seen = set()
    result = []
    for k in items:
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result

def _default_key_file(platform: Optional[str]) -> Optional[Path]:
    home = Path.home()
    base = home / ".concurrency_client"
    if platform == 'chatapi':
        return base / "chatapi.keys"
    if platform == 'siliconflow':
        return base / "siliconflow.keys"
    return base / "keys.txt"

def load_api_keys_advanced(
    *,
    platform: Optional[str] = None,
    api_keys: Optional[List[str]] = None,
    api_key_file: Optional[str] = None,
    use_dotenv: bool = True,
) -> List[str]:
    """优先级：
    1) 显式传入 api_keys 或 api_key_file
    2) 通用环境变量 CC_API_KEYS / CC_API_KEY_FILE
    3) 平台环境变量（CHATAPI_API_KEYS / _FILE, SILICONFLOW_API_KEYS / _FILE）
    4) 默认路径（~/.concurrency_client/<platform>.keys）
    5) 若 use_dotenv 且安装了 python-dotenv，将尝试加载 .env 后再解析上述变量
    """
    # 可选加载 .env
    if use_dotenv:
        try:
            from dotenv import load_dotenv  # type: ignore
            load_dotenv()
        except Exception:
            pass

    # 1) 显式参数
    if api_keys and len(api_keys) > 0:
        return [k.strip() for k in api_keys if k and k.strip()]
    if api_key_file:
        return load_api_keys(api_key_file)

    # 2) 通用环境变量
    raw = os.getenv('CC_API_KEYS')
    if raw:
        keys = _split_keys(raw)
        if keys:
            return keys
    file_env = os.getenv('CC_API_KEY_FILE')
    if file_env:
        keys = load_api_keys(file_env)
        if keys:
            return keys

    # 3) 平台环境变量
    platform = (platform or '').lower() if platform else None
    if platform == 'chatapi':
        raw = os.getenv('CHATAPI_API_KEYS')
        if raw:
            keys = _split_keys(raw)
            if keys:
                return keys
        file_env = os.getenv('CHATAPI_API_KEY_FILE')
        if file_env:
            keys = load_api_keys(file_env)
            if keys:
                return keys
    elif platform == 'siliconflow':
        raw = os.getenv('SILICONFLOW_API_KEYS')
        if raw:
            keys = _split_keys(raw)
            if keys:
                return keys
        file_env = os.getenv('SILICONFLOW_API_KEY_FILE')
        if file_env:
            keys = load_api_keys(file_env)
            if keys:
                return keys

    # 4) 默认路径
    if platform:
        default_file = _default_key_file(platform)
        if default_file and default_file.exists():
            keys = load_api_keys(str(default_file))
            if keys:
                return keys

    return []
