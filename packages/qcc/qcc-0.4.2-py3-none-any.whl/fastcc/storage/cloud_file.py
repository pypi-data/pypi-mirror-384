"""基于云盘文件的存储后端"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path
from .base import StorageBackend, StorageError, ConfigNotFoundError


class CloudFileBackend(StorageBackend):
    """基于云盘文件的存储后端"""
    
    def __init__(self, cloud_path: Optional[str] = None):
        self.cloud_path = self._detect_cloud_path(cloud_path)
        self.config_file = self.cloud_path / "fastcc_config.json" if self.cloud_path else None
        
    def _detect_cloud_path(self, custom_path: Optional[str] = None) -> Optional[Path]:
        """自动检测云盘路径"""
        if custom_path:
            path = Path(custom_path)
            if path.exists():
                return path
        
        # 检测常见云盘路径（按优先级排序）
        cloud_paths = []
        
        # macOS
        if os.name == 'posix' and os.uname().sysname == 'Darwin':
            cloud_paths.extend([
                Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/FastCC",  # iCloud Drive
                Path.home() / "Dropbox/FastCC",
                Path.home() / "OneDrive/FastCC", 
                Path.home() / "Google Drive/FastCC",
            ])
        
        # Windows
        elif os.name == 'nt':
            cloud_paths.extend([
                Path.home() / "OneDrive/FastCC",           # OneDrive (默认)
                Path.home() / "Dropbox/FastCC",            # Dropbox
                Path.home() / "Google Drive/FastCC",       # Google Drive
                Path(os.environ.get('USERPROFILE', '')) / "iCloudDrive/FastCC",  # iCloud for Windows
            ])
        
        # Linux
        else:
            cloud_paths.extend([
                Path.home() / "Dropbox/FastCC",            # Dropbox
                Path.home() / "OneDrive/FastCC",           # OneDrive (rclone等)
                Path.home() / "GoogleDrive/FastCC",        # Google Drive (rclone等)
                Path.home() / "Nextcloud/FastCC",          # Nextcloud
                Path.home() / "ownCloud/FastCC",           # ownCloud
            ])
        
        # 不包含本地路径，只使用真正的云盘
        
        # 尝试每个路径
        for path in cloud_paths:
            try:
                if path.parent.exists():  # 父目录存在
                    path.mkdir(parents=True, exist_ok=True)  # 创建FastCC目录
                    return path
            except (OSError, PermissionError):
                continue  # 跳过无权限的路径
                
        return None
    
    @property
    def backend_name(self) -> str:
        """后端名称"""
        if self.cloud_path:
            return f"云盘文件 ({self.cloud_path.parent.name})"
        return "本地文件"
    
    def is_available(self) -> bool:
        """检查云盘是否可用"""
        return self.cloud_path is not None and self.cloud_path.parent.exists()
    
    def save_config(self, data: Dict[str, Any]) -> bool:
        """保存配置数据"""
        if not self.is_available():
            raise StorageError("云盘路径不可用")
        
        try:
            # 添加同步时间戳
            data['last_sync'] = datetime.now().isoformat()
            data['sync_source'] = 'fastcc'
            
            # 确保目录存在
            self.cloud_path.mkdir(parents=True, exist_ok=True)
            
            # 写入配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 设置文件权限
            self.config_file.chmod(0o600)
            
            print(f"[OK] 配置已同步到云盘: {self.config_file}")
            return True
            
        except Exception as e:
            raise StorageError(f"保存到云盘失败: {e}")
    
    def load_config(self) -> Optional[Dict[str, Any]]:
        """加载配置数据"""
        if not self.is_available():
            return None
            
        try:
            if not self.config_file.exists():
                raise ConfigNotFoundError("云盘中未找到配置文件")
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            print(f"[OK] 从云盘加载配置: {self.config_file}")
            return data
            
        except json.JSONDecodeError as e:
            raise StorageError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise StorageError(f"从云盘加载失败: {e}")
    
    def delete_config(self) -> bool:
        """删除配置数据"""
        if not self.is_available():
            return True
            
        try:
            if self.config_file.exists():
                self.config_file.unlink()
                print(f"[OK] 已删除云盘配置: {self.config_file}")
            return True
            
        except Exception as e:
            raise StorageError(f"删除云盘配置失败: {e}")
    
    def is_authenticated(self) -> bool:
        """检查是否已认证（云盘文件不需要认证）"""
        return self.is_available()
    
    def authenticate(self) -> bool:
        """执行认证流程（云盘文件不需要认证）"""
        return self.is_available()
    
    def get_sync_info(self) -> Dict[str, Any]:
        """获取同步信息"""
        if not self.is_available():
            return {"status": "不可用", "path": None}
            
        info = {
            "status": "可用",
            "path": str(self.cloud_path),
            "config_exists": self.config_file.exists() if self.config_file else False
        }
        
        if self.config_file and self.config_file.exists():
            stat = self.config_file.stat()
            info["last_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            info["file_size"] = stat.st_size
            
        return info