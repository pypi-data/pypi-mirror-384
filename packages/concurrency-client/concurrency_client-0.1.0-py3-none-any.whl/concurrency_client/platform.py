from .universal_api_client import UniversalApiClient
from .api_pool import ApiKeyPool
from .utils import load_api_keys

class Platform:
    # SiliconFlow平台配置
    SILICONFLOW_API_URL = "https://api.siliconflow.cn/v1"
    SILICONFLOW_API_KEY_FILE = './api_key_txt/siliconflow_api.txt'
    
    # ChatAPI平台配置
    CHATAPI_API_URL = "https://api.chataiapi.com/v1"
    CHATAPI_API_KEY_FILE = './api_key_txt/chatapi.txt'
    
    # 支持的平台列表
    SUPPORTED_PLATFORMS = ['siliconflow', 'chatapi']
    
    def __init__(self, key_pool, api_url, model) -> None:
        pass
    
    @classmethod
    def get_config(cls, platform: str):
        """获取指定平台的配置"""
        if platform not in cls.SUPPORTED_PLATFORMS:
            raise ValueError(f"Unsupported platform: {platform}")
            
        if platform == 'siliconflow':
            return {
                'api_url': cls.SILICONFLOW_API_URL,
                'api_key_pool': ApiKeyPool(load_api_keys(cls.SILICONFLOW_API_KEY_FILE))
                
            }
        elif platform == 'chatapi':
            return {
                'api_url': cls.CHATAPI_API_URL,
                'api_key_pool':  ApiKeyPool(load_api_keys(cls.CHATAPI_API_KEY_FILE))
            }

    @classmethod
    def create_client(cls, platform: str, model: str) -> UniversalApiClient:
        """根据平台名创建通用客户端，要求调用者提供模型名。"""
        cfg = cls.get_config(platform)
        return UniversalApiClient(
            key_pool=cfg['api_key_pool'],
            api_url=cfg['api_url'],
            model=model,
        )

    @classmethod
    def create_client_custom(
        cls,
        api_url: str,
        api_key_file: str,
        model: str,
        strategy: str = 'random',
    ) -> UniversalApiClient:
        """使用自定义 API_URL 与 API_KEY_FILE 创建通用客户端。

        :param api_url: 自定义平台的基础 URL，如 "https://api.example.com/v1"
        :param api_key_file: 本地密钥文件路径，每行一个 key
        :param model: 模型名称
        :param strategy: 密钥池策略，支持 'random' 与 'round_robin'
        """
        keys = load_api_keys(api_key_file)
        pool = ApiKeyPool(keys, strategy=strategy)
        return UniversalApiClient(
            key_pool=pool,
            api_url=api_url,
            model=model,
        )