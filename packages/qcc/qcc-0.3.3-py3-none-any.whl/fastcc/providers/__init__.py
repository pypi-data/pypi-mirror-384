"""厂商配置管理模块"""

from .manager import ProvidersManager
from .browser import open_browser_and_wait

__all__ = ['ProvidersManager', 'open_browser_and_wait']