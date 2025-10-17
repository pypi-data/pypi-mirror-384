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
    """配置档案（扩展支持多 endpoint）"""

    def __init__(self, name: str, description: str = "",
                 base_url: str = "", api_key: str = "",
                 created_at: Optional[str] = None,
                 last_used: Optional[str] = None,
                 endpoints: Optional[List] = None,
                 priority: str = "primary",
                 enabled: bool = True):
        self.name = name
        self.description = description
        # 保持向后兼容：传统单 endpoint 字段
        self.base_url = base_url
        self.api_key = api_key
        # 新增：多 endpoint 支持
        self.endpoints = endpoints or []
        self.priority = priority  # primary, secondary, fallback
        self.enabled = enabled
        self.created_at = created_at or datetime.now().isoformat()
        self.last_used = last_used

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            'name': self.name,
            'description': self.description,
            'priority': self.priority,
            'enabled': self.enabled,
            'created_at': self.created_at,
            'last_used': self.last_used
        }

        # 如果有 endpoints，保存 endpoints 列表
        if self.endpoints:
            data['endpoints'] = [ep.to_dict() for ep in self.endpoints]
            # 为了向后兼容，同时保存第一个 endpoint 的数据
            if self.endpoints:
                data['base_url'] = self.endpoints[0].base_url
                data['api_key'] = self.endpoints[0].api_key
        else:
            # 如果没有 endpoints，使用传统字段
            data['base_url'] = self.base_url
            data['api_key'] = self.api_key

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigProfile':
        """从字典创建（兼容旧版本）"""
        # 构建参数字典，只包含旧版本支持的核心参数
        init_params = {
            'name': data['name'],
            'description': data.get('description', ''),
            'base_url': data.get('base_url', ''),
            'api_key': data.get('api_key', ''),
            'created_at': data.get('created_at'),
            'last_used': data.get('last_used')
        }

        # 如果当前版本支持新参数，则添加它们
        # 使用 try-except 来检测是否支持新参数
        import inspect
        sig = inspect.signature(cls.__init__)
        if 'endpoints' in sig.parameters:
            init_params['endpoints'] = None  # 稍后再设置
        if 'priority' in sig.parameters:
            init_params['priority'] = data.get('priority', 'primary')
        if 'enabled' in sig.parameters:
            init_params['enabled'] = data.get('enabled', True)

        # 创建 profile 实例
        profile = cls(**init_params)

        # 如果有 endpoints 数据，加载它们
        if 'endpoints' in data and data['endpoints']:
            try:
                from .endpoint import Endpoint
                profile.endpoints = [
                    Endpoint.from_dict(ep_data) for ep_data in data['endpoints']
                ]
            except (ImportError, AttributeError):
                # 旧版本没有 Endpoint 类，跳过
                pass

        return profile

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
        print("[+] 选择同步方式：")
        print("1. GitHub跨平台同步（推荐）- Windows、Mac、Linux通用")
        print("2. 本地云盘同步 - 使用iCloud/OneDrive等")
        print("3. 仅本地存储 - 不同步")
        print("")
        print("[?] 提示：选择后会记住您的偏好，可用 'nv config' 命令更改")
        
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
                print(f"[+] 使用GitHub跨平台同步: {github_backend.user_id}")
                return True
            elif backend_type == "cloud":
                cloud_backend = CloudFileBackend()
                if cloud_backend.is_available():
                    self.storage_backend = cloud_backend
                    self.user_id = f"cloud:{os.getenv('USER', 'unknown')}"
                    print(f"[+] 使用云盘存储: {cloud_backend.backend_name}")
                    return True
                else:
                    print("[!]  云盘不可用，回退到本地存储")
                    return self._init_and_save_choice("3")
            elif backend_type == "local":
                self.user_id = f"local:{os.getenv('USER', 'unknown')}"
                self.storage_backend = None  # 明确设置为 None 表示本地模式
                print("[+] 使用本地存储（无云端同步）")
                return True
        except Exception as e:
            print(f"[!]  存储后端初始化失败: {e}")
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
                print("[+] 初始化GitHub跨平台同步...")
                github_backend = GitHubSimpleBackend()
                self.storage_backend = github_backend
                self.user_id = f"github:{github_backend.user_id}"
                backend_type = "github"
                success = True
            except Exception as e:
                print(f"[!]  GitHub初始化失败: {e}")
                print("回退到云盘存储...")
                choice = "2"
        
        if choice == "2":
            # 云盘文件存储
            cloud_backend = CloudFileBackend()
            if cloud_backend.is_available():
                print(f"[+] 使用云盘存储: {cloud_backend.backend_name}")
                self.storage_backend = cloud_backend
                self.user_id = f"cloud:{os.getenv('USER', 'unknown')}"
                backend_type = "cloud"
                success = True
            else:
                print("[!]  未检测到云盘，使用本地存储")
                choice = "3"
        
        if choice == "3" or not success:
            # 本地存储
            print("[+] 使用本地存储")
            print("[?] 配置保存在本地 ~/.fastcc/")
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
            print(f"[OK] 已保存同步方式偏好: {backend_type}")
        
        return success
    
    def initialize_github_backend(self) -> bool:
        """初始化GitHub后端"""
        try:
            print("[+] 初始化GitHub存储后端...")
            
            # 获取GitHub访问令牌
            access_token = authenticate_github()
            if not access_token:
                print("[X] GitHub认证失败")
                return False
            
            # 创建GitHub Gist存储后端
            self.storage_backend = GitHubGistBackend(access_token)
            
            # 获取用户信息
            user_info = self.storage_backend.get_user_info()
            if user_info:
                self.user_id = f"github:{user_info['login']}"
                print(f"[OK] 已连接到GitHub账户: {user_info['login']}")
            
            # 初始化加密管理器
            if self.settings['encryption_enabled']:
                master_key = derive_user_key(self.user_id, access_token)
                self.crypto_manager = CryptoManager(master_key)
            
            # 保存到本地缓存，确保user_id被持久化
            self._save_local_cache()
            
            return True
            
        except Exception as e:
            print(f"[X] 初始化GitHub后端失败: {e}")
            return False
    
    def sync_from_cloud(self) -> bool:
        """从云端同步配置"""
        if not self.storage_backend:
            return True  # 本地存储模式，直接返回成功
        
        try:
            print("[~] 从云端同步配置...")
            
            config_data = self.storage_backend.load_config()
            if not config_data:
                print("[=] 云端暂无配置数据")
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
            
            print(f"[OK] 已同步 {len(self.profiles)} 个配置档案")
            
            # 保存到本地缓存
            self._save_local_cache()
            
            return True
            
        except Exception as e:
            print(f"[X] 从云端同步失败: {e}")
            return False
    
    def sync_to_cloud(self) -> bool:
        """同步配置到云端"""
        if not self.storage_backend:
            print("[i] 本地存储模式，无需云端同步")
            return True  # 本地存储模式，直接返回成功
        
        try:
            print("[~] 同步配置到云端...")
            
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
                print("[OK] 配置已同步到云端")
                self._save_local_cache()
            else:
                print("[X] 同步到云端失败")
            
            return success
            
        except Exception as e:
            # 检查是否是权限问题
            if "403" in str(e) and "Forbidden" in str(e):
                print("[!]  云同步失败：GitHub权限不足")
                print("[L] 解决方案：")
                print("1. 重新运行 'nv init' 重新获取认证")
                print("2. 如果问题持续，请尝试禁用自动同步：")
                print("   编辑 ~/.fastcc/cache.json，设置 'auto_sync': false")
            else:
                print(f"[X] 同步到云端失败: {e}")
            return False
    
    def add_profile(self, name: str, description: str, base_url: str, api_key: str) -> bool:
        """添加配置档案"""
        if name in self.profiles:
            print(f"[X] 配置档案 '{name}' 已存在")
            return False
        
        profile = ConfigProfile(name, description, base_url, api_key)
        self.profiles[name] = profile
        
        # 如果是第一个配置，设为默认
        if not self.settings['default_profile']:
            self.settings['default_profile'] = name
        
        print(f"[OK] 已添加配置档案: {name}")
        
        # 保存到本地缓存
        self._save_local_cache()
        
        # 自动同步到云端
        if self.settings['auto_sync']:
            self.sync_to_cloud()
        
        return True
    
    def remove_profile(self, name: str) -> bool:
        """删除配置档案"""
        if name not in self.profiles:
            print(f"[X] 配置档案 '{name}' 不存在")
            return False
        
        del self.profiles[name]
        
        # 如果删除的是默认配置，选择新的默认配置
        if self.settings['default_profile'] == name:
            if self.profiles:
                self.settings['default_profile'] = next(iter(self.profiles))
            else:
                self.settings['default_profile'] = None
        
        print(f"[OK] 已删除配置档案: {name}")
        
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
            print(f"[X] 配置档案 '{name}' 不存在")
            return False
        
        self.settings['default_profile'] = name
        print(f"[OK] 已设置默认配置: {name}")
        
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
                print("[OK] 已删除本地配置:")
                for item in deleted_items:
                    print(f"   - {item}")
                print("")
                print("[?] 说明:")
                print("   - 本地配置已清理完成")
                print("   - 云端数据已保留，其他设备仍可使用")
                print("   - 重新运行 'nv init' 可恢复配置")
            else:
                print("[i] 未找到需要删除的本地配置")
            
            return True
            
        except Exception as e:
            print(f"[X] 卸载失败: {e}")
            return False
    
    def apply_profile(self, name: str) -> bool:
        """应用配置档案到Claude Code"""
        profile = self.get_profile(name)
        if not profile:
            print(f"[X] 配置档案 '{name}' 不存在")
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

            # 优先使用第一个 endpoint，否则使用传统字段
            if profile.endpoints:
                first_endpoint = profile.endpoints[0]
                base_url = first_endpoint.base_url
                api_key = first_endpoint.api_key
            else:
                base_url = profile.base_url
                api_key = profile.api_key

            claude_config["env"]["ANTHROPIC_BASE_URL"] = base_url
            claude_config["env"]["ANTHROPIC_API_KEY"] = api_key
            claude_config["env"]["ANTHROPIC_AUTH_TOKEN"] = api_key  # 同时填充 AUTH_TOKEN
            claude_config["apiKeyHelper"] = f"echo '{api_key}'"

            # 写入配置文件
            with open(claude_config_file, 'w') as f:
                json.dump(claude_config, f, indent=2, ensure_ascii=False)

            # 设置文件权限
            claude_config_file.chmod(0o600)

            # 更新最后使用时间
            profile.update_last_used()

            print(f"[OK] 已应用配置: {name}")
            print(f"   BASE_URL: {base_url}")
            print(f"   API_KEY: {api_key[:10]}...{api_key[-4:]}")
            if profile.endpoints:
                print(f"   Endpoints: {len(profile.endpoints)} 个")

            # 保存更新后的使用时间
            self._save_local_cache()
            if self.settings['auto_sync']:
                self.sync_to_cloud()

            return True

        except Exception as e:
            print(f"[X] 应用配置失败: {e}")
            return False

    # ========== Endpoint 管理方法（新增） ==========

    def add_endpoint_to_profile(self, profile_name: str, endpoint) -> bool:
        """为配置添加 endpoint

        Args:
            profile_name: 配置名称
            endpoint: Endpoint 实例

        Returns:
            是否成功
        """
        profile = self.get_profile(profile_name)
        if not profile:
            print(f"[X] 配置 '{profile_name}' 不存在")
            return False

        # 初始化 endpoints 列表
        if not profile.endpoints:
            profile.endpoints = []

        profile.endpoints.append(endpoint)

        print(f"[OK] 已为配置 '{profile_name}' 添加 endpoint: {endpoint.id}")

        # 保存
        self._save_local_cache()
        if self.settings['auto_sync']:
            self.sync_to_cloud()

        return True

    def remove_endpoint_from_profile(self, profile_name: str, endpoint_id: str) -> bool:
        """从配置中删除 endpoint

        Args:
            profile_name: 配置名称
            endpoint_id: Endpoint ID

        Returns:
            是否成功
        """
        profile = self.get_profile(profile_name)
        if not profile:
            print(f"[X] 配置 '{profile_name}' 不存在")
            return False

        if not profile.endpoints:
            print(f"[X] 配置 '{profile_name}' 没有 endpoints")
            return False

        # 查找并删除
        for i, ep in enumerate(profile.endpoints):
            if ep.id == endpoint_id:
                del profile.endpoints[i]
                print(f"[OK] 已删除 endpoint: {endpoint_id}")

                # 保存
                self._save_local_cache()
                if self.settings['auto_sync']:
                    self.sync_to_cloud()

                return True

        print(f"[X] 未找到 endpoint: {endpoint_id}")
        return False

    def get_all_endpoints(self) -> List:
        """获取所有配置的所有 endpoint

        Returns:
            所有 endpoint 的列表
        """
        all_endpoints = []

        for profile in self.profiles.values():
            if profile.endpoints:
                all_endpoints.extend(profile.endpoints)

        return all_endpoints

    def save_profile(self, profile: ConfigProfile) -> bool:
        """保存配置档案（支持 endpoints）

        Args:
            profile: 配置档案实例

        Returns:
            是否成功
        """
        self.profiles[profile.name] = profile

        print(f"[OK] 已保存配置: {profile.name}")

        # 保存到本地和云端
        self._save_local_cache()
        if self.settings['auto_sync']:
            self.sync_to_cloud()

        return True

    def save_profiles(self) -> bool:
        """保存所有配置档案

        Returns:
            是否成功
        """
        try:
            # 保存到本地和云端
            print("[~] 保存配置...")
            self._save_local_cache()
            print(f"[i] auto_sync = {self.settings['auto_sync']}, storage_backend = {self.storage_backend}")
            if self.settings['auto_sync']:
                self.sync_to_cloud()

            return True
        except Exception as e:
            print(f"[X] 保存配置失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def has_profile(self, name: str) -> bool:
        """检查配置是否存在

        Args:
            name: 配置名称

        Returns:
            是否存在
        """
        return name in self.profiles