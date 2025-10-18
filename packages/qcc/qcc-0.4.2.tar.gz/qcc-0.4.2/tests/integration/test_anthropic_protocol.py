#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Anthropic 原生 API 协议
Claude Code 使用的是 /v1/messages 端点，而不是 OpenAI 的 /v1/chat/completions
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

def test_anthropic_messages_endpoint():
    """测试 Anthropic 原生 /v1/messages 端点"""
    print_section("测试 Anthropic 原生协议: /v1/messages")

    # Anthropic API 标准头
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    # Anthropic 原生请求格式
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "用一句话介绍你自己"}
        ]
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            print("发送请求到: /v1/messages")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            print(f"Payload: {json.dumps(payload, indent=2)}")

            response = client.post(
                f"{BASE_URL}/v1/messages",
                headers=headers,
                json=payload
            )

            print(f"\n状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")

            if response.status_code == 200:
                data = response.json()
                print("\n✓ 成功！使用 Anthropic 原生协议")
                print(f"\n完整响应:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(f"\n✗ 失败")
                print(f"响应内容: {response.text}")

    except Exception as e:
        print(f"\n✗ 异常: {e}")
        import traceback
        traceback.print_exc()

def test_anthropic_with_bearer_token():
    """测试使用 Bearer token 的 Anthropic 格式"""
    print_section("测试 Anthropic 格式 + Bearer Authorization")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Say hello"}
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

            if response.status_code == 200:
                data = response.json()
                print("✓ 成功！")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(f"✗ 失败: {response.text}")

    except Exception as e:
        print(f"✗ 异常: {e}")

def test_all_claude_models_with_anthropic_format():
    """测试所有 Claude 模型使用 Anthropic 格式"""
    print_section("测试所有 Claude 模型 (Anthropic 格式)")

    claude_models = [
        "claude-3-5-haiku-20241022",
        "claude-3-5-sonnet-20241022",
        "claude-3-7-sonnet-20250219",
        "claude-haiku-4-5-20251001",
        "claude-opus-4-1-20250805",
        "claude-opus-4-20250514",
        "claude-sonnet-4-20250514",
        "claude-sonnet-4-5",
        "claude-sonnet-4-5-20250929"
    ]

    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    for model in claude_models:
        print(f"\n测试模型: {model}")

        payload = {
            "model": model,
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

                if response.status_code == 200:
                    print(f"  ✓ 可用")
                else:
                    print(f"  ✗ 状态码: {response.status_code}")
                    error_text = response.text[:200]
                    print(f"  ✗ 错误: {error_text}")

        except Exception as e:
            print(f"  ✗ 异常: {e}")

def test_streaming_with_anthropic_format():
    """测试 Anthropic 格式的流式响应"""
    print_section("测试 Anthropic 格式流式响应")

    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 50,
        "messages": [
            {"role": "user", "content": "数到3"}
        ],
        "stream": True
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            with client.stream(
                "POST",
                f"{BASE_URL}/v1/messages",
                headers=headers,
                json=payload
            ) as response:
                print(f"状态码: {response.status_code}")

                if response.status_code == 200:
                    print("\n✓ 流式数据:")
                    for i, line in enumerate(response.iter_lines()):
                        if i >= 10:  # 只显示前10行
                            break
                        if line.strip():
                            print(f"  {line}")
                else:
                    print(f"✗ 失败: {response.read().decode()}")

    except Exception as e:
        print(f"✗ 异常: {e}")

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("  Anthropic 原生协议测试")
    print("  Claude Code 使用 /v1/messages 而不是 /v1/chat/completions")
    print("="*60)

    tests = [
        test_anthropic_messages_endpoint,
        test_anthropic_with_bearer_token,
        test_all_claude_models_with_anthropic_format,
        test_streaming_with_anthropic_format
    ]

    for test_func in tests:
        try:
            test_func()
        except KeyboardInterrupt:
            print("\n\n用户中断测试")
            sys.exit(0)
        except Exception as e:
            print(f"\n✗ 测试异常: {e}")

    print_section("总结")
    print("""
    关键区别：

    OpenAI 格式:
      - 端点: /v1/chat/completions
      - 认证: Authorization: Bearer {key}
      - 格式: {"model": "...", "messages": [...]}

    Anthropic 原生格式:
      - 端点: /v1/messages
      - 认证: x-api-key: {key}
      - 版本头: anthropic-version: 2023-06-01
      - 格式: {"model": "...", "max_tokens": ..., "messages": [...]}

    Claude Code 使用的是 Anthropic 原生格式！
    """)

if __name__ == "__main__":
    main()
