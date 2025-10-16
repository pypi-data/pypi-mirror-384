"""加密解密工具模块"""

import os
import base64
import hashlib
from typing import Union, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CryptoManager:
    """加密管理器"""
    
    def __init__(self, password: Optional[str] = None):
        """
        初始化加密管理器
        
        Args:
            password: 用于派生密钥的密码，如果为None则生成随机密钥
        """
        self.password = password
        self.salt = None
        self.key = None
        self._fernet = None
    
    def _derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """从密码派生密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _generate_random_key(self) -> bytes:
        """生成随机密钥"""
        return Fernet.generate_key()
    
    def _get_or_create_key(self) -> bytes:
        """获取或创建密钥"""
        if self.key:
            return self.key
        
        if self.password:
            # 使用密码派生密钥
            if not self.salt:
                self.salt = os.urandom(16)
            self.key = self._derive_key_from_password(self.password, self.salt)
        else:
            # 生成随机密钥
            self.key = self._generate_random_key()
        
        return self.key
    
    def _get_fernet(self) -> Fernet:
        """获取Fernet实例"""
        if not self._fernet:
            key = self._get_or_create_key()
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """
        加密数据
        
        Args:
            data: 要加密的数据
            
        Returns:
            Base64编码的加密数据
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        fernet = self._get_fernet()
        encrypted_data = fernet.encrypt(data)
        
        # 如果使用密码派生密钥，需要包含salt
        if self.password and self.salt:
            # 格式: salt(16字节) + encrypted_data
            result = self.salt + encrypted_data
        else:
            result = encrypted_data
        
        return base64.b64encode(result).decode('ascii')
    
    def decrypt(self, encrypted_data: str, password: Optional[str] = None) -> str:
        """
        解密数据
        
        Args:
            encrypted_data: Base64编码的加密数据
            password: 解密密码（如果与初始化时不同）
            
        Returns:
            解密后的字符串
        """
        data = base64.b64decode(encrypted_data.encode('ascii'))
        
        # 如果提供了新密码，重新初始化
        if password and password != self.password:
            self.password = password
            self.key = None
            self._fernet = None
        
        # 如果使用密码派生密钥，需要提取salt
        if self.password:
            if len(data) < 16:
                raise ValueError("加密数据格式错误")
            self.salt = data[:16]
            encrypted_content = data[16:]
            
            # 重新生成密钥和Fernet实例
            self.key = None
            self._fernet = None
        else:
            encrypted_content = data
        
        fernet = self._get_fernet()
        decrypted_data = fernet.decrypt(encrypted_content)
        
        return decrypted_data.decode('utf-8')
    
    def get_key_info(self) -> dict:
        """获取密钥信息"""
        key = self._get_or_create_key()
        key_hash = hashlib.sha256(key).hexdigest()[:16]
        
        return {
            'key_type': 'password_derived' if self.password else 'random',
            'key_hash': key_hash,
            'has_salt': bool(self.salt)
        }
    
    def export_key(self) -> str:
        """导出密钥（Base64格式）"""
        key = self._get_or_create_key()
        
        if self.password and self.salt:
            # 导出salt + key
            export_data = self.salt + key
        else:
            export_data = key
        
        return base64.b64encode(export_data).decode('ascii')
    
    def import_key(self, exported_key: str, password: Optional[str] = None):
        """导入密钥"""
        data = base64.b64decode(exported_key.encode('ascii'))
        
        if password:
            # 密码派生模式，提取salt
            if len(data) < 48:  # 16字节salt + 32字节key
                raise ValueError("导入的密钥数据格式错误")
            self.salt = data[:16]
            self.key = data[16:]
            self.password = password
        else:
            # 随机密钥模式
            self.key = data
            self.password = None
            self.salt = None
        
        # 重置Fernet实例
        self._fernet = None


def encrypt_string(data: str, password: str) -> str:
    """快速加密字符串"""
    crypto = CryptoManager(password)
    return crypto.encrypt(data)


def decrypt_string(encrypted_data: str, password: str) -> str:
    """快速解密字符串"""
    crypto = CryptoManager()
    return crypto.decrypt(encrypted_data, password)


def generate_master_key() -> str:
    """生成主密钥"""
    return base64.urlsafe_b64encode(os.urandom(32)).decode('ascii')


def derive_user_key(user_id: str, master_key: str) -> str:
    """为用户派生唯一密钥"""
    combined = f"{user_id}:{master_key}".encode('utf-8')
    hash_obj = hashlib.sha256(combined)
    return base64.urlsafe_b64encode(hash_obj.digest()).decode('ascii')