"""GitHub Gist存储后端实现"""

import json
import requests
from typing import Dict, Optional, Any
from pathlib import Path
from .base import StorageBackend, StorageError, AuthenticationError, ConfigNotFoundError


class GitHubGistBackend(StorageBackend):
    """GitHub Gist存储后端"""
    
    GIST_FILENAME = "fastcc_config.json"
    API_BASE = "https://api.github.com"
    
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.gist_id = None
        self._load_local_config()
    
    def _load_local_config(self):
        """加载本地存储的配置信息"""
        config_file = Path.home() / ".fastcc" / "github.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.gist_id = data.get('gist_id')
                    if not self.access_token:
                        self.access_token = data.get('access_token')
            except (json.JSONDecodeError, IOError):
                pass
    
    def _save_local_config(self):
        """保存本地配置信息"""
        config_dir = Path.home() / ".fastcc"
        config_dir.mkdir(exist_ok=True)
        
        config_file = config_dir / "github.json"
        data = {
            'gist_id': self.gist_id,
            'access_token': self.access_token
        }
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # 设置文件权限为仅所有者可读写
        config_file.chmod(0o600)
    
    def _get_headers(self) -> Dict[str, str]:
        """获取API请求头"""
        if not self.access_token:
            raise AuthenticationError("未找到GitHub访问令牌")
        
        return {
            'Authorization': f'token {self.access_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
    
    def _find_config_gist(self) -> Optional[str]:
        """查找配置文件Gist"""
        try:
            response = requests.get(
                f"{self.API_BASE}/gists",
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            gists = response.json()
            for gist in gists:
                if self.GIST_FILENAME in gist.get('files', {}):
                    return gist['id']
            
            return None
        except requests.RequestException as e:
            raise StorageError(f"查找Gist失败: {e}")
    
    def _create_config_gist(self, data: Dict[str, Any]) -> str:
        """创建新的配置Gist"""
        gist_data = {
            "description": "FastCC Configuration - 快速Claude配置管理",
            "public": False,
            "files": {
                self.GIST_FILENAME: {
                    "content": json.dumps(data, indent=2, ensure_ascii=False)
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.API_BASE}/gists",
                headers=self._get_headers(),
                json=gist_data
            )
            response.raise_for_status()
            
            result = response.json()
            return result['id']
        except requests.RequestException as e:
            raise StorageError(f"创建Gist失败: {e}")
    
    def _update_config_gist(self, gist_id: str, data: Dict[str, Any]) -> bool:
        """更新配置Gist"""
        gist_data = {
            "files": {
                self.GIST_FILENAME: {
                    "content": json.dumps(data, indent=2, ensure_ascii=False)
                }
            }
        }
        
        try:
            response = requests.patch(
                f"{self.API_BASE}/gists/{gist_id}",
                headers=self._get_headers(),
                json=gist_data
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            raise StorageError(f"更新Gist失败: {e}")
    
    def save_config(self, data: Dict[str, Any]) -> bool:
        """保存配置数据"""
        try:
            if not self.gist_id:
                # 查找现有Gist
                self.gist_id = self._find_config_gist()
            
            if self.gist_id:
                # 更新现有Gist
                success = self._update_config_gist(self.gist_id, data)
            else:
                # 创建新Gist
                self.gist_id = self._create_config_gist(data)
                success = bool(self.gist_id)
            
            if success:
                self._save_local_config()
            
            return success
        except Exception as e:
            raise StorageError(f"保存配置失败: {e}")
    
    def load_config(self) -> Optional[Dict[str, Any]]:
        """加载配置数据"""
        try:
            if not self.gist_id:
                self.gist_id = self._find_config_gist()
            
            if not self.gist_id:
                raise ConfigNotFoundError("未找到配置文件")
            
            response = requests.get(
                f"{self.API_BASE}/gists/{self.gist_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            gist = response.json()
            if self.GIST_FILENAME not in gist.get('files', {}):
                raise ConfigNotFoundError("Gist中未找到配置文件")
            
            content = gist['files'][self.GIST_FILENAME]['content']
            return json.loads(content)
        
        except requests.RequestException as e:
            raise StorageError(f"加载配置失败: {e}")
        except json.JSONDecodeError as e:
            raise StorageError(f"配置文件格式错误: {e}")
    
    def delete_config(self) -> bool:
        """删除配置数据"""
        try:
            if not self.gist_id:
                return True  # 没有配置文件，认为删除成功
            
            response = requests.delete(
                f"{self.API_BASE}/gists/{self.gist_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            # 清理本地配置
            self.gist_id = None
            self._save_local_config()
            
            return True
        except requests.RequestException as e:
            raise StorageError(f"删除配置失败: {e}")
    
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        if not self.access_token:
            return False
        
        try:
            response = requests.get(
                f"{self.API_BASE}/user",
                headers=self._get_headers()
            )
            return response.status_code == 200
        except:
            return False
    
    def authenticate(self) -> bool:
        """执行认证流程"""
        # 这里需要实现OAuth流程，暂时返回False
        # 实际实现需要与auth模块配合
        return False
    
    @property
    def backend_name(self) -> str:
        """后端名称"""
        return "GitHub Gist"
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        try:
            response = requests.get(
                f"{self.API_BASE}/user",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except:
            return None