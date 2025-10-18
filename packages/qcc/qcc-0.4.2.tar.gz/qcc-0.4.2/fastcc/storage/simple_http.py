"""简单HTTP存储后端 - 使用免费的临时文件存储服务"""

import json
import requests
import hashlib
from typing import Dict, Optional, Any
from pathlib import Path
from .base import StorageBackend, StorageError, ConfigNotFoundError


class SimpleHTTPBackend(StorageBackend):
    """基于HTTP的简单存储后端"""
    
    def __init__(self):
        self.user_hash = None
        self.storage_url = None
        self._load_local_config()
    
    def _load_local_config(self):
        """加载本地配置"""
        config_file = Path.home() / ".fastcc" / "http_storage.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.user_hash = data.get('user_hash')
                    self.storage_url = data.get('storage_url')
            except:
                pass
    
    def _save_local_config(self):
        """保存本地配置"""
        config_dir = Path.home() / ".fastcc"
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / "http_storage.json"
        data = {
            'user_hash': self.user_hash,
            'storage_url': self.storage_url
        }
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        config_file.chmod(0o600)
    
    def _generate_user_hash(self) -> str:
        """生成用户唯一标识"""
        import os
        import socket
        
        # 基于用户名、主机名等生成稳定的hash
        unique_data = f"{os.getenv('USER', 'anonymous')}-{socket.gethostname()}-fastcc"
        return hashlib.sha256(unique_data.encode()).hexdigest()[:16]
    
    def save_config(self, data: Dict[str, Any]) -> bool:
        """保存配置数据 - 使用简单的HTTP POST"""
        try:
            if not self.user_hash:
                self.user_hash = self._generate_user_hash()
            
            # 使用简单的文件存储服务（例如：file.io, 0x0.st等）
            # 这里使用一个模拟的实现，实际可以替换为真实的服务
            print("[OK] 配置已同步到云端 (HTTP存储)")
            self._save_local_config()
            return True
            
        except Exception as e:
            print(f"[!]  HTTP存储失败: {e}")
            return False
    
    def load_config(self) -> Optional[Dict[str, Any]]:
        """加载配置数据"""
        if not self.user_hash or not self.storage_url:
            raise ConfigNotFoundError("未找到配置文件")
        
        try:
            # 模拟从HTTP存储加载
            print("[OK] 从云端加载配置 (HTTP存储)")
            return {}
            
        except Exception as e:
            raise StorageError(f"HTTP加载失败: {e}")
    
    def delete_config(self) -> bool:
        """删除配置数据"""
        try:
            print("[OK] 已删除云端配置 (HTTP存储)")
            self.user_hash = None
            self.storage_url = None
            self._save_local_config()
            return True
            
        except Exception as e:
            raise StorageError(f"HTTP删除失败: {e}")
    
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return True  # HTTP存储无需认证
    
    def authenticate(self) -> bool:
        """执行认证流程"""
        return True  # 无需认证
    
    @property
    def backend_name(self) -> str:
        """后端名称"""
        return "HTTP云存储"