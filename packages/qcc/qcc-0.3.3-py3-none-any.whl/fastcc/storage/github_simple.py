"""简化的GitHub存储后端 - 使用个人访问令牌"""

import json
import requests
import hashlib
import os
from typing import Dict, Optional, Any
from pathlib import Path
from .base import StorageBackend, StorageError, ConfigNotFoundError


class GitHubSimpleBackend(StorageBackend):
    """简化的GitHub存储后端"""
    
    API_BASE = "https://api.github.com"
    GIST_FILENAME = "fastcc_config.json"
    
    def __init__(self):
        self.access_token = None
        self.gist_id = None
        self.user_id = None
        self._load_or_setup_token()
    
    def _load_or_setup_token(self):
        """加载或设置访问令牌"""
        config_file = Path.home() / ".fastcc" / "github_simple.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.access_token = data.get('access_token')
                    self.gist_id = data.get('gist_id')
                    self.user_id = data.get('user_id')
                    return
            except:
                pass
        
        # 首次使用，请求用户提供GitHub个人访问令牌
        print("🔧 首次使用跨平台同步，需要GitHub个人访问令牌")
        print("📋 获取步骤：")
        print("1. 访问: https://github.com/settings/tokens")
        print("2. 点击 'Generate new token (classic)'")
        print("3. 选择权限: ✅ gist")
        print("4. 复制生成的令牌")
        print("")
        
        token = input("请粘贴GitHub个人访问令牌: ").strip()
        if token and token.startswith(('ghp_', 'github_pat_')):
            self.access_token = token
            self._test_and_save_token()
        else:
            print("❌ 无效的令牌格式")
            raise StorageError("GitHub令牌配置失败")
    
    def _test_and_save_token(self):
        """测试并保存令牌"""
        try:
            headers = {
                'Authorization': f'token {self.access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(f"{self.API_BASE}/user", headers=headers)
            response.raise_for_status()
            
            user_info = response.json()
            self.user_id = user_info['login']
            
            print(f"✅ GitHub令牌验证成功，用户: {self.user_id}")
            
            # 保存配置
            config_dir = Path.home() / ".fastcc"
            config_dir.mkdir(exist_ok=True)
            
            config_file = config_dir / "github_simple.json"
            data = {
                'access_token': self.access_token,
                'gist_id': self.gist_id,
                'user_id': self.user_id
            }
            
            with open(config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            config_file.chmod(0o600)
            
        except Exception as e:
            raise StorageError(f"GitHub令牌验证失败: {e}")
    
    def _get_headers(self) -> Dict[str, str]:
        """获取API请求头"""
        return {
            'Authorization': f'token {self.access_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
    
    def _find_config_gist(self) -> Optional[str]:
        """查找配置Gist"""
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
    
    def save_config(self, data: Dict[str, Any]) -> bool:
        """保存配置到GitHub Gist"""
        try:
            content = json.dumps(data, indent=2, ensure_ascii=False)
            
            if not self.gist_id:
                self.gist_id = self._find_config_gist()
            
            if self.gist_id:
                # 更新现有Gist
                gist_data = {
                    "files": {
                        self.GIST_FILENAME: {
                            "content": content
                        }
                    }
                }
                
                response = requests.patch(
                    f"{self.API_BASE}/gists/{self.gist_id}",
                    headers=self._get_headers(),
                    json=gist_data
                )
            else:
                # 创建新Gist
                gist_data = {
                    "description": "FastCC Configuration - 快速Claude配置同步",
                    "public": False,
                    "files": {
                        self.GIST_FILENAME: {
                            "content": content
                        }
                    }
                }
                
                response = requests.post(
                    f"{self.API_BASE}/gists",
                    headers=self._get_headers(),
                    json=gist_data
                )
                
                if response.status_code == 201:
                    result = response.json()
                    self.gist_id = result['id']
                    
                    # 更新本地配置
                    config_file = Path.home() / ".fastcc" / "github_simple.json"
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    config['gist_id'] = self.gist_id
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
            
            response.raise_for_status()
            print("✅ 配置已同步到GitHub (跨平台)")
            return True
            
        except Exception as e:
            raise StorageError(f"GitHub同步失败: {e}")
    
    def load_config(self) -> Optional[Dict[str, Any]]:
        """从GitHub Gist加载配置"""
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
            print("✅ 从GitHub加载配置 (跨平台)")
            return json.loads(content)
            
        except Exception as e:
            raise StorageError(f"GitHub加载失败: {e}")
    
    def delete_config(self) -> bool:
        """删除配置"""
        try:
            if self.gist_id:
                response = requests.delete(
                    f"{self.API_BASE}/gists/{self.gist_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
            
            print("✅ 已删除GitHub配置")
            return True
            
        except Exception as e:
            raise StorageError(f"删除失败: {e}")
    
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return bool(self.access_token and self.user_id)
    
    def authenticate(self) -> bool:
        """执行认证流程"""
        return self.is_authenticated()
    
    @property
    def backend_name(self) -> str:
        """后端名称"""
        return f"GitHub跨平台同步 ({self.user_id})"