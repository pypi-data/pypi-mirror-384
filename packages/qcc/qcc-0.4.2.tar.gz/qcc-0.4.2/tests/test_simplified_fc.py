#!/usr/bin/env python3
"""测试简化的 fc 命令流程"""

import sys
sys.path.insert(0, '/Users/yxhpy/Desktop/project/fastcc')

from fastcc.providers.manager import ProvidersManager
from fastcc.providers.browser import (
    print_step, print_provider_info
)

def test_simplified_fc():
    """测试简化的厂商快速配置流程"""
    print("🧪 测试简化的厂商快速配置流程...")
    
    # 获取厂商配置
    providers_manager = ProvidersManager()
    if not providers_manager.fetch_providers():
        print("❌ 无法获取厂商配置")
        return
    
    providers = providers_manager.get_providers()
    
    # 步骤1: 显示厂商列表
    print_step(1, 5, "选择 AI 厂商")
    print("📋 可用厂商:")
    for i, provider in enumerate(providers, 1):
        print(f"  {i}. {provider}")
    
    # 模拟选择
    selected_provider = providers[0]
    print(f"\n✅ 选择了: {selected_provider.name}")
    
    # 步骤2: 显示厂商信息并模拟打开浏览器
    print_step(2, 5, "注册或登录厂商账户")
    print_provider_info(selected_provider)
    
    print(f"\n🌐 正在打开 {selected_provider.name} 注册/登录页面...")
    print(f"📎 URL: {selected_provider.signup_url}")
    print("✅ 浏览器已打开 (模拟)")
    print(f"💡 请在浏览器中完成 {selected_provider.name} 的注册或登录")
    
    # 步骤3: API Key 输入
    print_step(3, 5, "获取 API Key")
    print(f"💡 {selected_provider.api_key_help}")
    print("等待用户输入 API Key... (模拟)")
    
    # 模拟 API Key 输入
    mock_api_key = "sk-ant-1234567890abcdefghijklmnopqrstuvwxyz"
    print(f"✅ 模拟输入 API Key: {mock_api_key[:15]}...")
    
    # 步骤4: Base URL 确认
    print_step(4, 5, "确认 API 地址")
    print(f"默认 API 地址: {selected_provider.base_url}")
    print("✅ 使用默认地址 (模拟)")
    
    # 步骤5: 配置创建
    print_step(5, 5, "创建配置档案")
    mock_config_name = "test_anthropic"
    mock_description = f"{selected_provider.name} 配置"
    
    print(f"✅ 模拟配置信息:")
    print(f"   名称: {mock_config_name}")
    print(f"   描述: {mock_description}")
    print(f"   厂商: {selected_provider.name}")
    print(f"   API地址: {selected_provider.base_url}")
    print(f"   API Key: {mock_api_key[:10]}...{mock_api_key[-4:]}")
    
    print("\n🎉 简化流程测试完成！")
    print("📋 新的流程:")
    print("   1. 选择厂商 → 2. 直接打开浏览器 → 3. 等待输入 API Key → 4. 完成配置")

if __name__ == "__main__":
    test_simplified_fc()