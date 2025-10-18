#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 QCC 代理服务器的 Anthropic 协议支持
验证代理服务器是否正确转发 Anthropic /v1/messages 请求
"""

import httpx
import json
import sys
import io
import asyncio

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 测试配置
PROXY_URL = "http://127.0.0.1:7860"  # QCC 代理地址
TEST_API_KEY = "sk-2EQrynW6WnwhebbW95Ym8uyiezKAETsxtAkboJHJyzH64OfD"  # 用于测试的 API Key

def print_section(title: str):
    """打印分隔线标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

async def test_messages_endpoint():
    """测试 /v1/messages 端点通过代理"""
    print_section("测试 1: /v1/messages 通过代理")

    headers = {
        "x-api-key": TEST_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "用一个词回答：天空是什么颜色？"}
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"发送请求到代理: {PROXY_URL}/v1/messages")
            print(f"使用模型: {payload['model']}")

            response = await client.post(
                f"{PROXY_URL}/v1/messages",
                headers=headers,
                json=payload
            )

            print(f"\n状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print("\n✓ 成功！")
                print(f"模型: {data.get('model', 'N/A')}")

                if data.get('content'):
                    content = data['content'][0].get('text', '')
                    print(f"回复: {content}")

                usage = data.get('usage', {})
                print(f"Tokens: 输入={usage.get('input_tokens')}, 输出={usage.get('output_tokens')}")

                return True
            else:
                print(f"\n✗ 失败")
                print(f"响应: {response.text}")
                return False

    except Exception as e:
        print(f"\n✗ 异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_streaming_messages():
    """测试流式响应通过代理"""
    print_section("测试 2: 流式 /v1/messages 通过代理")

    headers = {
        "x-api-key": TEST_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 50,
        "messages": [
            {"role": "user", "content": "数到5"}
        ],
        "stream": True
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"发送流式请求到代理: {PROXY_URL}/v1/messages")

            async with client.stream(
                "POST",
                f"{PROXY_URL}/v1/messages",
                headers=headers,
                json=payload
            ) as response:
                print(f"状态码: {response.status_code}")

                if response.status_code == 200:
                    print("\n✓ 流式数据接收中...")
                    chunk_count = 0

                    async for line in response.aiter_lines():
                        if line.strip():
                            chunk_count += 1
                            if chunk_count <= 5:  # 只显示前5个 chunk
                                print(f"  Chunk {chunk_count}: {line[:100]}")

                    print(f"\n✓ 共接收 {chunk_count} 个数据块")
                    return True
                else:
                    body = await response.aread()
                    print(f"\n✗ 失败: {body.decode()}")
                    return False

    except Exception as e:
        print(f"\n✗ 异常: {e}")
        return False

async def test_all_available_models():
    """测试所有可用的 Claude 模型"""
    print_section("测试 3: 测试可用的 Claude 模型")

    models_to_test = [
        "claude-3-5-haiku-20241022",
        "claude-haiku-4-5-20251001",
        # 其他模型可能因负载限制而不可用
    ]

    headers = {
        "x-api-key": TEST_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    results = {}

    for model in models_to_test:
        print(f"\n测试模型: {model}")

        payload = {
            "model": model,
            "max_tokens": 10,
            "messages": [
                {"role": "user", "content": "Hi"}
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{PROXY_URL}/v1/messages",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    print(f"  ✓ 可用")
                    results[model] = "可用"
                else:
                    error_text = response.text[:100]
                    print(f"  ✗ 状态码: {response.status_code}")
                    print(f"  ✗ 错误: {error_text}")
                    results[model] = f"不可用 ({response.status_code})"

        except Exception as e:
            print(f"  ✗ 异常: {e}")
            results[model] = f"异常 ({str(e)[:50]})"

    print("\n结果汇总:")
    for model, status in results.items():
        print(f"  {model}: {status}")

    return results

async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("  QCC 代理服务器 Anthropic 协议测试")
    print(f"  代理地址: {PROXY_URL}")
    print("="*60)

    # 检查代理服务器是否运行
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{PROXY_URL}/")
            print(f"\n✓ 代理服务器运行中")
    except Exception:
        print(f"\n✗ 代理服务器未运行，请先启动: uvx qcc proxy start")
        return

    # 运行测试
    test1_result = await test_messages_endpoint()
    test2_result = await test_streaming_messages()
    test3_results = await test_all_available_models()

    # 总结
    print_section("测试总结")

    if test1_result:
        print("✓ 基础 /v1/messages 请求: 通过")
    else:
        print("✗ 基础 /v1/messages 请求: 失败")

    if test2_result:
        print("✓ 流式 /v1/messages 请求: 通过")
    else:
        print("✗ 流式 /v1/messages 请求: 失败")

    available_models = [m for m, s in test3_results.items() if s == "可用"]
    print(f"\n可用模型: {len(available_models)}/{len(test3_results)}")
    for model in available_models:
        print(f"  - {model}")

    if test1_result and test2_result and len(available_models) > 0:
        print("\n🎉 所有关键测试通过！QCC 代理服务器 Anthropic 协议支持正常！")
    else:
        print("\n⚠️ 部分测试失败，请检查配置和日志")

if __name__ == "__main__":
    asyncio.run(main())
