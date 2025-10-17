# api_pool.py
import random
from itertools import cycle
import sys
import logging
import threading

class MissingApiKeyError(Exception):
    pass

class EmptyKeyPoolError(Exception):
    pass

class ApiKeyPool:
    def __init__(self, api_keys: list, strategy: str = "random"):
        self.api_keys = api_keys
        self.strategy = strategy
        self.iterator = cycle(api_keys) if strategy == "round_robin" else None
        self._lock = threading.Lock()

    def get_key(self):
        with self._lock:
            if self.api_keys is None or len(self.api_keys) == 0:
                logging.error("未设置或空的API密钥池")
                raise EmptyKeyPoolError("API密钥池为空或未设置")
            if self.strategy == "random":
                return random.choice(self.api_keys)
            elif self.strategy == "round_robin":
                return next(self.iterator)
            else:
                raise ValueError(f"Unsupported strategy: {self.strategy}")
            
    def release_key(self, key):
        """
        释放API密钥，当前实现为空，因为简单的轮询或随机策略不需要释放逻辑
        保留此方法以保持接口一致性，便于未来扩展
        """
        pass
    
    def cleanup(self):
        """
        清理API密钥池，当前实现为空，因为简单的轮询或随机策略不需要清理逻辑
        保留此方法以保持接口一致性，便于未来扩展
        """
        pass
    
    def delete_key(self, key):
        """
        删除API密钥
        """
        with self._lock:
            try:
                self.api_keys.remove(key)
            except ValueError:
                # key 不存在时忽略
                return
            # 若为轮询策略，重建迭代器以避免引用已删除的key
            if self.strategy == "round_robin":
                self.iterator = cycle(self.api_keys) if self.api_keys else cycle(())