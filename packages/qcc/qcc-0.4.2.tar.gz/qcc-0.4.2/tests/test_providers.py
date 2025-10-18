#!/usr/bin/env python3
"""测试厂商配置功能"""

import sys
sys.path.insert(0, '/Users/yxhpy/Desktop/project/fastcc')

from fastcc.providers.manager import ProvidersManager

def test_providers():
    print("🧪 测试厂商配置管理器...")
    
    pm = ProvidersManager()
    print(f"📡 配置URL: {pm.config_url}")
    
    print("\n🌐 正在获取厂商配置...")
    success = pm.fetch_providers()
    print(f"获取结果: {'成功' if success else '失败'}")
    
    if not success:
        print(f"错误信息: {pm.get_last_error()}")
        return
    
    providers = pm.get_providers()
    print(f"\n📋 找到 {len(providers)} 个厂商:")
    
    for i, provider in enumerate(providers, 1):
        print(f"\n{i}. {provider.name}")
        print(f"   ID: {provider.id}")
        print(f"   描述: {provider.description}")
        print(f"   API地址: {provider.base_url}")
        print(f"   注册地址: {provider.signup_url}")
        if provider.docs_url:
            print(f"   文档: {provider.docs_url}")
        if provider.api_key_help:
            print(f"   API Key帮助: {provider.api_key_help}")
    
    # 测试API Key验证
    if providers:
        test_provider = providers[0]
        print(f"\n🔍 测试 {test_provider.name} 的 API Key 验证:")
        
        test_keys = [
            "sk-ant-1234567890abcdef",  # 正确格式
            "invalid-key",              # 错误格式
            "",                         # 空值
            "sk-1234567890abcdef1234567890abcdef"  # OpenAI格式
        ]
        
        for key in test_keys:
            valid = pm.validate_api_key(test_provider, key)
            print(f"   '{key[:20]}...' -> {'有效' if valid else '无效'}")

if __name__ == "__main__":
    test_providers()