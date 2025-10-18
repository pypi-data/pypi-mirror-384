#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试双重认证方式
验证同时发送 x-api-key 和 Authorization 是否能正常工作
"""

import httpx
import json
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "https://q.quuvv.cn"
API_KEY = "sk-2EQrynW6WnwhebbW95Ym8uyiezKAETsxtAkboJHJyzH64OfD"

def print_section(title: str):
    """打印分隔线标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_dual_auth():
    """测试同时使用两种认证方式"""
    print_section("测试：同时使用 x-api-key 和 Authorization")

    # 同时发送两种认证头
    headers = {
        "x-api-key": API_KEY,
        "Authorization": f"Bearer {API_KEY}",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 50,
        "messages": [
            {"role": "user", "content": "说 Hello"}
        ]
    }

    print("发送的请求头:")
    for key, value in headers.items():
        if key in ["x-api-key", "Authorization"]:
            # 隐藏部分 key
            display_value = value[:20] + "..." + value[-10:] if len(value) > 30 else value
            print(f"  {key}: {display_value}")
        else:
            print(f"  {key}: {value}")

    try:
        with httpx.Client(timeout=30.0) as client:
            print(f"\n发送请求到: {BASE_URL}/v1/messages")
            response = client.post(
                f"{BASE_URL}/v1/messages",
                headers=headers,
                json=payload
            )

            print(f"\n状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("\n✓ 成功！双重认证方式可用")
                print(f"\n模型: {data.get('model', 'N/A')}")

                if data.get('content'):
                    content = data['content'][0].get('text', '')
                    print(f"回复: {content}")

                usage = data.get('usage', {})
                print(f"Tokens: 输入={usage.get('input_tokens')}, 输出={usage.get('output_tokens')}")
            else:
                print(f"\n✗ 失败")
                print(f"响应: {response.text}")

    except Exception as e:
        print(f"\n✗ 异常: {e}")
        import traceback
        traceback.print_exc()

def test_only_x_api_key():
    """测试仅使用 x-api-key"""
    print_section("对比测试：仅使用 x-api-key")

    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 10,
        "messages": [
            {"role": "user", "content": "Hi"}
        ]
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{BASE_URL}/v1/messages",
                headers=headers,
                json=payload
            )

            print(f"状态码: {response.status_code}")
            print(f"结果: {'✓ 成功' if response.status_code == 200 else '✗ 失败'}")

    except Exception as e:
        print(f"✗ 异常: {e}")

def test_only_authorization():
    """测试仅使用 Authorization"""
    print_section("对比测试：仅使用 Authorization Bearer")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 10,
        "messages": [
            {"role": "user", "content": "Hi"}
        ]
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{BASE_URL}/v1/messages",
                headers=headers,
                json=payload
            )

            print(f"状态码: {response.status_code}")
            print(f"结果: {'✓ 成功' if response.status_code == 200 else '✗ 失败'}")

    except Exception as e:
        print(f"✗ 异常: {e}")

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("  双重认证方式测试")
    print("  验证同时发送两种认证头是否可行")
    print("="*60)

    test_dual_auth()
    test_only_x_api_key()
    test_only_authorization()

    print_section("总结")
    print("""
测试目的：验证 QCC 代理同时发送两种认证方式的策略

预期结果：
  - 双重认证应该成功（服务器会选择其中一种）
  - 仅 x-api-key 应该成功（Anthropic 原生格式）
  - 仅 Authorization 可能成功（取决于服务器兼容性）

优势：
  ✓ 最大化兼容性
  ✓ 支持 Anthropic 原生和 OpenAI 兼容服务
  ✓ 无需配置即可自动适配
    """)

if __name__ == "__main__":
    main()
