"""配置管理器"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..storage.base import StorageBackend
from ..storage.github_gist import GitHubGistBackend
from ..storage.cloud_file import CloudFileBackend
from ..storage.jsonbin import JSONBinBackend
from ..storage.github_simple import GitHubSimpleBackend
from ..auth.oauth import authenticate_github
from ..utils.crypto import CryptoManager, derive_user_key


class ConfigProfile:
    """配置档案"""
    
    def __init__(self, name: str, description: str = "", 
                 base_url: str = "", api_key: str = "", 
                 created_at: Optional[str] = None, 
                 last_used: Optional[str] = None):
        self.name = name
        self.description = description
        self.base_url = base_url
        self.api_key = api_key
        self.created_at = created_at or datetime.now().isoformat()
        self.last_used = last_used
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'description': self.description,
            'base_url': self.base_url,
            'api_key': self.api_key,
            'created_at': self.created_at,
            'last_used': self.last_used
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigProfile':
        """从字典创建"""
        return cls(**data)
    
    def update_last_used(self):
        """更新最后使用时间"""
        self.last_used = datetime.now().isoformat()


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, storage_backend: Optional[StorageBackend] = None):
        self.storage_backend = storage_backend
        self.profiles: Dict[str, ConfigProfile] = {}
        self.settings = {
            'default_profile': None,
            'auto_sync': True,
            'encryption_enabled': True,
            'storage_backend_type': None,  # 记住用户选择的存储类型
            'storage_initialized': False   # 标记是否已完成初始化
        }
        self.crypto_manager: Optional[CryptoManager] = None
        self.user_id: Optional[str] = None
        
        # 加载本地缓存配置
        self._load_local_cache()
    
    def _load_local_cache(self):
        """加载本地缓存配置"""
        cache_file = Path.home() / ".fastcc" / "cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    
                # 加载设置
                self.settings.update(data.get('settings', {}))
                
                # 加载用户ID
                self.user_id = data.get('user_id')
                
                # 加载配置档案（如果有缓存）
                profiles_data = data.get('profiles', {})
                for name, profile_data in profiles_data.items():
                    self.profiles[name] = ConfigProfile.from_dict(profile_data)
                    
            except (json.JSONDecodeError, IOError):
                pass
    
    def _save_local_cache(self):
        """保存本地缓存配置"""
        cache_dir = Path.home() / ".fastcc"
        cache_dir.mkdir(exist_ok=True)
        
        cache_file = cache_dir / "cache.json"
        
        data = {
            'user_id': self.user_id,
            'settings': self.settings,
            'profiles': {name: profile.to_dict() for name, profile in self.profiles.items()}
        }
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        cache_file.chmod(0o600)
    
    def initialize_storage_backend(self, force_choose: bool = False) -> bool:
        """智能初始化存储后端"""
        # 检查是否已经初始化过
        if not force_choose and self.settings.get('storage_initialized'):
            backend_type = self.settings.get('storage_backend_type')
            if backend_type:
                return self._init_backend_by_type(backend_type)
        
        # 首次使用或强制选择时，询问用户偏好
        print("🔧 选择同步方式：")
        print("1. GitHub跨平台同步（推荐）- Windows、Mac、Linux通用")
        print("2. 本地云盘同步 - 使用iCloud/OneDrive等")
        print("3. 仅本地存储 - 不同步")
        print("")
        print("💡 提示：选择后会记住您的偏好，可用 'nv config' 命令更改")
        
        try:
            choice = input("请选择 (1-3, 默认1): ").strip() or "1"
        except (KeyboardInterrupt, EOFError):
            choice = "1"
        
        return self._init_and_save_choice(choice)
    
    def _init_backend_by_type(self, backend_type: str) -> bool:
        """根据类型初始化存储后端"""
        try:
            if backend_type == "github":
                github_backend = GitHubSimpleBackend()
                self.storage_backend = github_backend
                self.user_id = f"github:{github_backend.user_id}"
                print(f"🔧 使用GitHub跨平台同步: {github_backend.user_id}")
                return True
            elif backend_type == "cloud":
                cloud_backend = CloudFileBackend()
                if cloud_backend.is_available():
                    self.storage_backend = cloud_backend
                    self.user_id = f"cloud:{os.getenv('USER', 'unknown')}"
                    print(f"🔧 使用云盘存储: {cloud_backend.backend_name}")
                    return True
                else:
                    print("⚠️  云盘不可用，回退到本地存储")
                    return self._init_and_save_choice("3")
            elif backend_type == "local":
                self.user_id = f"local:{os.getenv('USER', 'unknown')}"
                print("🔧 使用本地存储")
                return True
        except Exception as e:
            print(f"⚠️  存储后端初始化失败: {e}")
            print("回退到本地存储")
            return self._init_and_save_choice("3")
        
        return False
    
    def _init_and_save_choice(self, choice: str) -> bool:
        """初始化并保存用户选择"""
        success = False
        backend_type = None
        
        if choice == "1":
            # GitHub跨平台同步
            try:
                print("🔧 初始化GitHub跨平台同步...")
                github_backend = GitHubSimpleBackend()
                self.storage_backend = github_backend
                self.user_id = f"github:{github_backend.user_id}"
                backend_type = "github"
                success = True
            except Exception as e:
                print(f"⚠️  GitHub初始化失败: {e}")
                print("回退到云盘存储...")
                choice = "2"
        
        if choice == "2":
            # 云盘文件存储
            cloud_backend = CloudFileBackend()
            if cloud_backend.is_available():
                print(f"🔧 使用云盘存储: {cloud_backend.backend_name}")
                self.storage_backend = cloud_backend
                self.user_id = f"cloud:{os.getenv('USER', 'unknown')}"
                backend_type = "cloud"
                success = True
            else:
                print("⚠️  未检测到云盘，使用本地存储")
                choice = "3"
        
        if choice == "3" or not success:
            # 本地存储
            print("🔧 使用本地存储")
            print("💡 配置保存在本地 ~/.fastcc/")
            print("📁 如需跨设备同步，可将此文件夹放入云盘并创建软链接")
            print("   例如：ln -s ~/Dropbox/FastCC ~/.fastcc")
            self.user_id = f"local:{os.getenv('USER', 'unknown')}"
            backend_type = "local"
            success = True
        
        # 保存用户选择
        if success and backend_type:
            self.settings['storage_backend_type'] = backend_type
            self.settings['storage_initialized'] = True
            self._save_local_cache()
            print(f"✅ 已保存同步方式偏好: {backend_type}")
        
        return success
    
    def initialize_github_backend(self) -> bool:
        """初始化GitHub后端"""
        try:
            print("🔧 初始化GitHub存储后端...")
            
            # 获取GitHub访问令牌
            access_token = authenticate_github()
            if not access_token:
                print("❌ GitHub认证失败")
                return False
            
            # 创建GitHub Gist存储后端
            self.storage_backend = GitHubGistBackend(access_token)
            
            # 获取用户信息
            user_info = self.storage_backend.get_user_info()
            if user_info:
                self.user_id = f"github:{user_info['login']}"
                print(f"✅ 已连接到GitHub账户: {user_info['login']}")
            
            # 初始化加密管理器
            if self.settings['encryption_enabled']:
                master_key = derive_user_key(self.user_id, access_token)
                self.crypto_manager = CryptoManager(master_key)
            
            # 保存到本地缓存，确保user_id被持久化
            self._save_local_cache()
            
            return True
            
        except Exception as e:
            print(f"❌ 初始化GitHub后端失败: {e}")
            return False
    
    def sync_from_cloud(self) -> bool:
        """从云端同步配置"""
        if not self.storage_backend:
            return True  # 本地存储模式，直接返回成功
        
        try:
            print("☁️ 从云端同步配置...")
            
            config_data = self.storage_backend.load_config()
            if not config_data:
                print("📝 云端暂无配置数据")
                return True
            
            # 解密配置数据
            if self.crypto_manager and 'encrypted_profiles' in config_data:
                encrypted_profiles = config_data['encrypted_profiles']
                profiles_json = self.crypto_manager.decrypt(encrypted_profiles)
                profiles_data = json.loads(profiles_json)
            else:
                profiles_data = config_data.get('profiles', {})
            
            # 更新本地配置
            self.profiles.clear()
            for name, profile_data in profiles_data.items():
                self.profiles[name] = ConfigProfile.from_dict(profile_data)
            
            # 更新设置
            if 'settings' in config_data:
                self.settings.update(config_data['settings'])
            
            print(f"✅ 已同步 {len(self.profiles)} 个配置档案")
            
            # 保存到本地缓存
            self._save_local_cache()
            
            return True
            
        except Exception as e:
            print(f"❌ 从云端同步失败: {e}")
            return False
    
    def sync_to_cloud(self) -> bool:
        """同步配置到云端"""
        if not self.storage_backend:
            return True  # 本地存储模式，直接返回成功
        
        try:
            print("☁️ 同步配置到云端...")
            
            # 准备配置数据
            profiles_data = {name: profile.to_dict() for name, profile in self.profiles.items()}
            
            config_data = {
                'user_id': self.user_id,
                'settings': self.settings,
                'last_sync': datetime.now().isoformat()
            }
            
            # 加密配置数据
            if self.crypto_manager:
                profiles_json = json.dumps(profiles_data, ensure_ascii=False)
                config_data['encrypted_profiles'] = self.crypto_manager.encrypt(profiles_json)
            else:
                config_data['profiles'] = profiles_data
            
            # 上传到云端
            success = self.storage_backend.save_config(config_data)
            
            if success:
                print("✅ 配置已同步到云端")
                self._save_local_cache()
            else:
                print("❌ 同步到云端失败")
            
            return success
            
        except Exception as e:
            # 检查是否是权限问题
            if "403" in str(e) and "Forbidden" in str(e):
                print("⚠️  云同步失败：GitHub权限不足")
                print("📋 解决方案：")
                print("1. 重新运行 'nv init' 重新获取认证")
                print("2. 如果问题持续，请尝试禁用自动同步：")
                print("   编辑 ~/.fastcc/cache.json，设置 'auto_sync': false")
            else:
                print(f"❌ 同步到云端失败: {e}")
            return False
    
    def add_profile(self, name: str, description: str, base_url: str, api_key: str) -> bool:
        """添加配置档案"""
        if name in self.profiles:
            print(f"❌ 配置档案 '{name}' 已存在")
            return False
        
        profile = ConfigProfile(name, description, base_url, api_key)
        self.profiles[name] = profile
        
        # 如果是第一个配置，设为默认
        if not self.settings['default_profile']:
            self.settings['default_profile'] = name
        
        print(f"✅ 已添加配置档案: {name}")
        
        # 保存到本地缓存
        self._save_local_cache()
        
        # 自动同步到云端
        if self.settings['auto_sync']:
            self.sync_to_cloud()
        
        return True
    
    def remove_profile(self, name: str) -> bool:
        """删除配置档案"""
        if name not in self.profiles:
            print(f"❌ 配置档案 '{name}' 不存在")
            return False
        
        del self.profiles[name]
        
        # 如果删除的是默认配置，选择新的默认配置
        if self.settings['default_profile'] == name:
            if self.profiles:
                self.settings['default_profile'] = next(iter(self.profiles))
            else:
                self.settings['default_profile'] = None
        
        print(f"✅ 已删除配置档案: {name}")
        
        # 自动同步到云端
        if self.settings['auto_sync']:
            self.sync_to_cloud()
        
        return True
    
    def list_profiles(self) -> List[ConfigProfile]:
        """列出所有配置档案"""
        return list(self.profiles.values())
    
    def get_profile(self, name: str) -> Optional[ConfigProfile]:
        """获取指定配置档案"""
        return self.profiles.get(name)
    
    def get_default_profile(self) -> Optional[ConfigProfile]:
        """获取默认配置档案"""
        default_name = self.settings.get('default_profile')
        if default_name:
            return self.profiles.get(default_name)
        return None
    
    def set_default_profile(self, name: str) -> bool:
        """设置默认配置档案"""
        if name not in self.profiles:
            print(f"❌ 配置档案 '{name}' 不存在")
            return False
        
        self.settings['default_profile'] = name
        print(f"✅ 已设置默认配置: {name}")
        
        # 自动同步到云端
        if self.settings['auto_sync']:
            self.sync_to_cloud()
        
        return True
    
    def uninstall_local(self) -> bool:
        """卸载本地配置（保留云端数据）"""
        try:
            import shutil
            
            # 要删除的本地目录和文件
            local_paths = [
                Path.home() / ".fastcc",           # 主配置目录
                Path.home() / ".claude" / "settings.json"  # Claude配置文件（可选）
            ]
            
            deleted_items = []
            
            for path in local_paths:
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                        deleted_items.append(f"目录: {path}")
                    else:
                        path.unlink()
                        deleted_items.append(f"文件: {path}")
            
            if deleted_items:
                print("✅ 已删除本地配置:")
                for item in deleted_items:
                    print(f"   - {item}")
                print("")
                print("💡 说明:")
                print("   - 本地配置已清理完成")
                print("   - 云端数据已保留，其他设备仍可使用")
                print("   - 重新运行 'nv init' 可恢复配置")
            else:
                print("ℹ️ 未找到需要删除的本地配置")
            
            return True
            
        except Exception as e:
            print(f"❌ 卸载失败: {e}")
            return False
    
    def apply_profile(self, name: str) -> bool:
        """应用配置档案到Claude Code"""
        profile = self.get_profile(name)
        if not profile:
            print(f"❌ 配置档案 '{name}' 不存在")
            return False
        
        try:
            # 更新Claude Code配置文件
            claude_config_dir = Path.home() / ".claude"
            claude_config_dir.mkdir(exist_ok=True)
            
            claude_config_file = claude_config_dir / "settings.json"
            
            # 读取现有配置
            if claude_config_file.exists():
                with open(claude_config_file, 'r') as f:
                    claude_config = json.load(f)
            else:
                claude_config = {"env": {}, "permissions": {"allow": [], "deny": []}}
            
            # 更新API配置
            if "env" not in claude_config:
                claude_config["env"] = {}
            
            claude_config["env"]["ANTHROPIC_BASE_URL"] = profile.base_url
            claude_config["env"]["ANTHROPIC_API_KEY"] = profile.api_key
            claude_config["env"]["ANTHROPIC_AUTH_TOKEN"] = profile.api_key  # 同时填充 AUTH_TOKEN
            claude_config["apiKeyHelper"] = f"echo '{profile.api_key}'"
            
            # 写入配置文件
            with open(claude_config_file, 'w') as f:
                json.dump(claude_config, f, indent=2, ensure_ascii=False)
            
            # 设置文件权限
            claude_config_file.chmod(0o600)
            
            # 更新最后使用时间
            profile.update_last_used()
            
            print(f"✅ 已应用配置: {name}")
            print(f"   BASE_URL: {profile.base_url}")
            print(f"   API_KEY: {profile.api_key[:10]}...{profile.api_key[-4:]}")
            
            # 保存更新后的使用时间
            if self.settings['auto_sync']:
                self.sync_to_cloud()
            
            return True
            
        except Exception as e:
            print(f"❌ 应用配置失败: {e}")
            return False