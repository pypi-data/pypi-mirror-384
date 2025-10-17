# -- coding: utf-8 --
# Project: frappeclient
# Created Date: 2025 05 Sa
# Author: liming
# Email: lmlala@aliyun.com
# Copyright (c) 2025 FiuAI



import logging
from typing import List, Optional, Dict, Any
from .type import ClientConfig

logger = logging.getLogger(__name__)


class FiuaiConfig:
    """FiuaiSDK 配置单例类"""
    _instance: Optional['FiuaiConfig'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.client_config: Optional[ClientConfig] = None
            self._initialized = True
    
    def init(self, url: str, max_api_retry: int = 3, 
             timeout: int = 5, verify: bool = False):
        """
        初始化 FiuaiSDK 全局配置
        
        Args:
            url: API 服务器地址
            max_api_retry: 最大重试次数
            timeout: 请求超时时间
            verify: 是否验证 SSL 证书
        """
        
        # 初始化客户端配置
        self.client_config = ClientConfig(
            url=url, 
            max_api_retry=max_api_retry, 
            timeout=timeout,
            verify=verify,
        )
    

    
    def get_client_config(self) -> Optional[ClientConfig]:
        """获取 CLIENTCONFIG 实例"""
        return self.client_config
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self.client_config is not None


# 创建全局单例实例
_config = FiuaiConfig()



def get_client_config():
    return _config.get_client_config()

def is_initialized():
    return _config.is_initialized()


def init_fiuai(
    url: str,
    max_api_retry: int=3,
    timeout: int=5,
    verify: bool=False
):
    """
    初始化 FiuaiSDK 全局配置
    
    Args:
        url: API 服务器地址
        max_api_retry: 最大重试次数
        timeout: 请求超时时间
        verify: 是否验证 SSL 证书
    """
    _config.init(url, max_api_retry, timeout, verify)


###### tools

def get_int_value(key: str, data: Dict[str, Any]) -> int | None:
    """
    获取int类型的值
    """
    d = data.get(key, None)
    if not d:
        return None 

    return int(d)