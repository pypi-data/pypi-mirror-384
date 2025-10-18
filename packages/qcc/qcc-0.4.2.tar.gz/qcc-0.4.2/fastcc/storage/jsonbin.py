"""JSONBin.io存储后端 - 免费JSON云存储"""

import json
import requests
from typing import Dict, Optional, Any
from pathlib import Path
from .base import StorageBackend, StorageError, ConfigNotFoundError


class JSONBinBackend(StorageBackend):
    """JSONBin.io存储后端"""
    
    API_BASE = "https://api.jsonbin.io/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_or_create_api_key()
        self.bin_id = None
        self._load_local_config()
    
    def _get_or_create_api_key(self) -> Optional[str]:
        """获取或创建API密钥"""
        config_file = Path.home() / ".fastcc" / "jsonbin.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    return data.get('api_key')
            except:
                pass
        
        # JSONBin.io提供免费服务，无需API密钥即可创建bin
        # 我们使用匿名方式
        return None
    
    def _load_local_config(self):
        """加载本地配置"""
        config_file = Path.home() / ".fastcc" / "jsonbin.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.bin_id = data.get('bin_id')
            except:
                pass
    
    def _save_local_config(self):
        """保存本地配置"""
        config_dir = Path.home() / ".fastcc"
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / "jsonbin.json"
        data = {
            'bin_id': self.bin_id,
            'api_key': self.api_key
        }
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        config_file.chmod(0o600)
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            'Content-Type': 'application/json',
            'X-Bin-Name': 'FastCC Configuration'
        }
        
        if self.api_key:
            headers['X-Master-Key'] = self.api_key
            
        return headers
    
    def save_config(self, data: Dict[str, Any]) -> bool:
        """保存配置数据"""
        try:
            headers = self._get_headers()
            
            if self.bin_id:
                # 更新现有bin
                url = f"{self.API_BASE}/b/{self.bin_id}"
                response = requests.put(url, json=data, headers=headers)
            else:
                # 创建新bin
                url = f"{self.API_BASE}/b"
                response = requests.post(url, json=data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    self.bin_id = result.get('metadata', {}).get('id')
                    self._save_local_config()
            
            if response.status_code == 200:
                print("[OK] 配置已同步到云端 (JSONBin)")
                return True
            else:
                raise StorageError(f"API请求失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            raise StorageError(f"保存到JSONBin失败: {e}")
    
    def load_config(self) -> Optional[Dict[str, Any]]:
        """加载配置数据"""
        if not self.bin_id:
            raise ConfigNotFoundError("未找到配置文件")
        
        try:
            headers = self._get_headers()
            url = f"{self.API_BASE}/b/{self.bin_id}/latest"
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print("[OK] 从云端加载配置 (JSONBin)")
                return result.get('record', {})
            elif response.status_code == 404:
                raise ConfigNotFoundError("配置文件不存在")
            else:
                raise StorageError(f"API请求失败: {response.status_code}")
                
        except Exception as e:
            raise StorageError(f"从JSONBin加载失败: {e}")
    
    def delete_config(self) -> bool:
        """删除配置数据"""
        if not self.bin_id:
            return True
        
        try:
            headers = self._get_headers()
            url = f"{self.API_BASE}/b/{self.bin_id}"
            
            response = requests.delete(url, headers=headers)
            
            if response.status_code == 200:
                self.bin_id = None
                self._save_local_config()
                print("[OK] 已删除云端配置 (JSONBin)")
                return True
            else:
                raise StorageError(f"删除失败: {response.status_code}")
                
        except Exception as e:
            raise StorageError(f"删除JSONBin配置失败: {e}")
    
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return True  # JSONBin支持匿名使用
    
    def authenticate(self) -> bool:
        """执行认证流程"""
        return True  # 无需认证
    
    @property
    def backend_name(self) -> str:
        """后端名称"""
        return "JSONBin.io"