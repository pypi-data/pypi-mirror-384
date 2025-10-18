"""厂商配置管理器"""

import json
import requests
from typing import Dict, List, Optional, Any


class Provider:
    """厂商信息"""
    
    def __init__(self, id: str, name: str, description: str, 
                 base_url: str, signup_url: str, 
                 docs_url: str = "", api_key_help: str = "",
                 **kwargs):
        self.id = id
        self.name = name
        self.description = description
        self.base_url = base_url
        self.signup_url = signup_url
        self.docs_url = docs_url
        self.api_key_help = api_key_help
        # 存储其他额外字段
        self.extra = kwargs
    
    def __str__(self):
        return f"{self.name} - {self.description}"


class ProvidersManager:
    """厂商配置管理器"""
    
    def __init__(self, config_url: str = None):
        self.config_url = config_url or "https://gist.githubusercontent.com/lghguge520/6bd1b97c4e2261c702edf5800afb5d31/raw/qcc_collection.json"
        self.providers: Dict[str, Provider] = {}
        self._last_error: Optional[str] = None
    
    def fetch_providers(self) -> bool:
        """从云端获取厂商配置"""
        try:
            print("🌐 获取厂商配置...")
            response = requests.get(self.config_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            providers_data = data.get('providers', {})
            
            self.providers.clear()
            for provider_id, provider_info in providers_data.items():
                self.providers[provider_id] = Provider(
                    id=provider_id,
                    **provider_info
                )
            
            print(f"[OK] 已获取 {len(self.providers)} 个厂商配置")
            return True
            
        except requests.RequestException as e:
            self._last_error = f"网络请求失败: {e}"
            print(f"[X] {self._last_error}")
            return False
        except json.JSONDecodeError as e:
            self._last_error = f"配置格式错误: {e}"
            print(f"[X] {self._last_error}")
            return False
        except Exception as e:
            self._last_error = f"获取配置失败: {e}"
            print(f"[X] {self._last_error}")
            return False
    
    def get_providers(self) -> List[Provider]:
        """获取所有厂商列表"""
        return list(self.providers.values())
    
    def get_provider(self, provider_id: str) -> Optional[Provider]:
        """根据ID获取厂商"""
        return self.providers.get(provider_id)
    
    def get_provider_by_index(self, index: int) -> Optional[Provider]:
        """根据索引获取厂商"""
        providers = list(self.providers.values())
        if 0 <= index < len(providers):
            return providers[index]
        return None
    
    def validate_api_key(self, provider: Provider, api_key: str) -> bool:
        """验证API Key格式（简单验证）"""
        if not api_key or not api_key.strip():
            return False
        
        # 根据厂商类型进行简单的格式验证
        if 'anthropic' in provider.id.lower():
            # Anthropic API Key 通常以 sk-ant- 开头
            return api_key.startswith('sk-ant-') and len(api_key) > 20
        elif 'openai' in provider.id.lower():
            # OpenAI API Key 通常以 sk- 开头
            return api_key.startswith('sk-') and len(api_key) > 20
        else:
            # 其他厂商，只检查长度
            return len(api_key.strip()) >= 10
    
    def validate_base_url(self, base_url: str) -> bool:
        """验证Base URL格式"""
        if not base_url:
            return False
        
        return (base_url.startswith('http://') or 
                base_url.startswith('https://'))
    
    def get_last_error(self) -> Optional[str]:
        """获取最后一次错误信息"""
        return self._last_error