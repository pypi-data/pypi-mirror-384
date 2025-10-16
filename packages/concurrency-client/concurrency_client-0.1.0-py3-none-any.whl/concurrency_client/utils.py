# utils.py
from typing import List

def load_api_keys(file_path: str) -> List[str]:
    """从文件中加载API密钥，每行一个，忽略空行与首尾空白。
    若文件不存在则返回空列表。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []
