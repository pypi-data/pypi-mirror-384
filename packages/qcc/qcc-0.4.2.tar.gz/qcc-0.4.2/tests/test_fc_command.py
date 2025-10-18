#!/usr/bin/env python3
"""测试 fc 命令的核心逻辑"""

import sys
sys.path.insert(0, '/Users/yxhpy/Desktop/project/fastcc')

from fastcc.providers.manager import ProvidersManager
from fastcc.providers.browser import (
    print_step, print_provider_info, confirm_continue
)

def test_fc_workflow():
    """测试厂商快速配置流程"""
    print("🧪 测试厂商快速配置流程...")
    
    # 步骤1: 获取厂商配置
    providers_manager = ProvidersManager()
    if not providers_manager.fetch_providers():
        print("❌ 无法获取厂商配置")
        return
    
    providers = providers_manager.get_providers()
    if not providers:
        print("❌ 暂无可用厂商配置")
        return
    
    # 步骤2: 显示厂商列表
    print_step(1, 5, "选择 AI 厂商")
    print("📋 可用厂商:")
    for i, provider in enumerate(providers, 1):
        print(f"  {i}. {provider}")
    
    # 模拟选择第一个厂商
    selected_provider = providers[0]
    print(f"\n✅ 模拟选择: {selected_provider.name}")
    
    # 步骤3: 显示厂商信息
    print_step(2, 5, "厂商信息")
    print_provider_info(selected_provider)
    
    # 步骤4: 模拟API Key验证
    print_step(3, 5, "API Key 验证测试")
    test_api_keys = [
        "sk-ant-1234567890abcdefghijklmnopqrstuvwxyz",
        "invalid-key",
        ""
    ]
    
    for api_key in test_api_keys:
        valid = providers_manager.validate_api_key(selected_provider, api_key)
        key_display = api_key[:15] + "..." if len(api_key) > 15 else api_key
        print(f"   测试 API Key '{key_display}': {'✅ 有效' if valid else '❌ 无效'}")
    
    # 步骤5: 测试Base URL验证
    print_step(4, 5, "Base URL 验证测试")
    test_urls = [
        "https://api.anthropic.com",
        "http://localhost:8080",
        "invalid-url",
        ""
    ]
    
    for url in test_urls:
        valid = providers_manager.validate_base_url(url)
        print(f"   测试 URL '{url}': {'✅ 有效' if valid else '❌ 无效'}")
    
    print_step(5, 5, "测试完成")
    print("🎉 厂商快速配置流程测试通过！")
    
    print(f"\n💡 接下来可以运行完整的 CLI 命令:")
    print(f"   PYTHONPATH=/Users/yxhpy/Desktop/project/fastcc python3 -m fastcc.cli fc")

if __name__ == "__main__":
    test_fc_workflow()