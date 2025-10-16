"""存储后端抽象基类"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class StorageBackend(ABC):
    """存储后端抽象基类"""
    
    @abstractmethod
    def save_config(self, data: Dict[str, Any]) -> bool:
        """保存配置数据"""
        pass
    
    @abstractmethod
    def load_config(self) -> Optional[Dict[str, Any]]:
        """加载配置数据"""
        pass
    
    @abstractmethod
    def delete_config(self) -> bool:
        """删除配置数据"""
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        pass
    
    @abstractmethod
    def authenticate(self) -> bool:
        """执行认证流程"""
        pass
    
    @property
    @abstractmethod
    def backend_name(self) -> str:
        """后端名称"""
        pass


class StorageError(Exception):
    """存储相关错误"""
    pass


class AuthenticationError(StorageError):
    """认证相关错误"""
    pass


class ConfigNotFoundError(StorageError):
    """配置未找到错误"""
    pass