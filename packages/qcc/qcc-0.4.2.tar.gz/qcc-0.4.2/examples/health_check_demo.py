#!/usr/bin/env python3
"""智能健康检测系统演示

展示如何使用对话式健康检查、性能指标统计和动态权重调整功能。
"""

import asyncio
from fastcc.proxy import (
    ConversationalHealthChecker,
    PerformanceMetrics,
    DynamicWeightAdjuster,
    ConversationalHealthCheck,
    HealthCheckResult
)
from fastcc.core.endpoint import Endpoint


def print_separator(title=""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    else:
        print(f"{'='*60}\n")


def demo_health_check_models():
    """演示健康检查数据模型"""
    print_separator("1. 健康检查数据模型")

    # 创建健康检查记录
    check = ConversationalHealthCheck("demo-endpoint")
    check.result = HealthCheckResult.SUCCESS
    check.response_time_ms = 250.5
    check.response_content = "1"
    check.response_valid = True
    check.response_score = 95.0
    check.tokens_used = 5
    check.model_used = "claude-3-haiku-20240307"

    print("✅ 创建健康检查记录:")
    print(f"   Endpoint ID: {check.endpoint_id}")
    print(f"   测试消息: {check.test_message}")
    print(f"   结果: {check.result.value}")
    print(f"   响应时间: {check.response_time_ms:.1f}ms")
    print(f"   响应内容: {check.response_content}")
    print(f"   响应有效: {check.response_valid}")
    print(f"   质量评分: {check.response_score}/100")

    # 序列化
    data = check.to_dict()
    print(f"\n📦 序列化为字典: {len(data)} 个字段")

    # 反序列化
    restored = ConversationalHealthCheck.from_dict(data)
    print(f"✅ 反序列化成功: {restored.endpoint_id}")


def demo_performance_metrics():
    """演示性能指标统计"""
    print_separator("2. 性能指标统计")

    metrics = PerformanceMetrics("demo-endpoint")

    # 模拟10次检查
    print("📊 模拟 10 次健康检查...\n")

    for i in range(10):
        check = ConversationalHealthCheck("demo-endpoint")

        # 前8次成功，后2次失败
        if i < 8:
            check.result = HealthCheckResult.SUCCESS
            check.response_time_ms = 200.0 + i * 20  # 200-360ms
            check.response_valid = True
            check.response_score = 90.0
        else:
            check.result = HealthCheckResult.TIMEOUT
            check.error_message = "请求超时"

        metrics.add_check_result(check)

        # 显示进度
        status = "✅" if check.result == HealthCheckResult.SUCCESS else "❌"
        print(f"   {status} 检查 #{i+1}: {check.result.value} "
              f"({check.response_time_ms:.0f}ms)" if check.response_time_ms else "")

    # 显示统计结果
    print(f"\n📈 性能指标:")
    print(f"   总检查次数: {metrics.total_checks}")
    print(f"   成功次数: {metrics.successful_checks}")
    print(f"   失败次数: {metrics.failed_checks}")
    print(f"   成功率: {metrics.success_rate:.1f}%")
    print(f"   近期成功率: {metrics.recent_success_rate:.1f}%")
    print(f"   平均响应时间: {metrics.avg_response_time:.0f}ms")
    print(f"   P95 响应时间: {metrics.p95_response_time:.0f}ms")
    print(f"   稳定性评分: {metrics.stability_score:.1f}/100")
    print(f"   连续成功: {metrics.consecutive_successes} 次")
    print(f"   连续失败: {metrics.consecutive_failures} 次")


def demo_weight_adjustment():
    """演示动态权重调整"""
    print_separator("3. 动态权重调整")

    adjuster = DynamicWeightAdjuster()

    # 创建3个 endpoint，性能各异
    scenarios = [
        {
            "name": "endpoint-fast",
            "description": "快速稳定",
            "response_times": [150, 160, 155, 158, 152],
            "failures": 0
        },
        {
            "name": "endpoint-slow",
            "description": "响应慢",
            "response_times": [800, 850, 900, 820, 880],
            "failures": 0
        },
        {
            "name": "endpoint-unstable",
            "description": "不稳定",
            "response_times": [200, 300, 400, 500],
            "failures": 2
        }
    ]

    for scenario in scenarios:
        print(f"\n🔍 测试场景: {scenario['description']} ({scenario['name']})")

        # 创建 endpoint 和指标
        endpoint = Endpoint(
            base_url=f"https://{scenario['name']}.com",
            api_key="test-key",
            weight=100
        )

        metrics = PerformanceMetrics(endpoint.id)

        # 添加成功的检查
        for time_ms in scenario['response_times']:
            check = ConversationalHealthCheck(endpoint.id)
            check.result = HealthCheckResult.SUCCESS
            check.response_time_ms = float(time_ms)
            check.response_valid = True
            metrics.add_check_result(check)

        # 添加失败的检查
        for _ in range(scenario['failures']):
            check = ConversationalHealthCheck(endpoint.id)
            check.result = HealthCheckResult.FAILURE
            metrics.add_check_result(check)

        # 计算新权重
        new_weight = adjuster.calculate_new_weight(
            endpoint.id,
            endpoint.weight,
            metrics
        )

        change = new_weight - endpoint.weight
        change_pct = (change / endpoint.weight) * 100

        print(f"   当前权重: {endpoint.weight:.0f}")
        print(f"   新权重: {new_weight:.1f} ({change:+.1f}, {change_pct:+.1f}%)")
        print(f"   平均响应: {metrics.avg_response_time:.0f}ms")
        print(f"   成功率: {metrics.success_rate:.0f}%")
        print(f"   稳定性: {metrics.stability_score:.0f}/100")

        # 显示权重变化原因
        if new_weight > endpoint.weight:
            print(f"   ✅ 权重提升：性能优秀")
        elif new_weight < endpoint.weight:
            print(f"   ⚠️  权重降低：性能不佳")
        else:
            print(f"   ➖ 权重不变：性能一般")


async def demo_conversational_checker():
    """演示对话式健康检查器（需要真实 API）"""
    print_separator("4. 对话式健康检查器")

    print("ℹ️  此演示需要真实的 API endpoint")
    print("   由于演示环境限制，这里只展示功能说明\n")

    checker = ConversationalHealthChecker()

    print(f"✅ 检查器配置:")
    print(f"   超时时间: {checker.timeout}秒")
    print(f"   最大 Tokens: {checker.max_tokens}")
    print(f"   使用模型: {checker.model}")
    print(f"   测试消息数: {len(checker.test_messages)}")

    print(f"\n📝 测试消息列表:")
    for i, msg in enumerate(checker.test_messages, 1):
        print(f"   {i}. {msg}")

    print(f"\n💡 使用方法:")
    print(f"   endpoint = Endpoint(base_url='...', api_key='...')")
    print(f"   check = await checker.check_endpoint(endpoint)")
    print(f"   print(f'结果: {{check.result.value}}')")
    print(f"   print(f'响应时间: {{check.response_time_ms}}ms')")
    print(f"   print(f'质量评分: {{check.response_score}}/100')")


def demo_summary():
    """显示功能总结"""
    print_separator("5. 功能总结")

    features = [
        ("✅ 健康检查数据模型", "完整的检查记录、序列化支持"),
        ("✅ 性能指标统计", "多维度统计、历史追踪"),
        ("✅ 动态权重调整", "智能计算、平滑调整"),
        ("✅ 对话式健康检查", "真实 AI 测试、质量评估"),
        ("✅ 智能健康监控", "定时检查、自动调整"),
    ]

    print("🎯 智能健康检测系统核心功能:\n")
    for feature, desc in features:
        print(f"   {feature}")
        print(f"      {desc}\n")

    print("📊 相比传统 ping 测试的优势:\n")
    advantages = [
        "真实 API 调用测试，而非简单 ping",
        "验证 API Key 有效性",
        "检测限流和配额问题",
        "评估响应质量和内容",
        "多维度性能分析",
        "智能动态权重调整",
    ]
    for adv in advantages:
        print(f"   • {adv}")

    print("\n💡 下一步:")
    print("   1. 配置 endpoints (qcc endpoint add)")
    print("   2. 启动代理服务 (qcc proxy start)")
    print("   3. 查看健康状态 (qcc health metrics)")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  QCC 智能健康检测系统 - 功能演示")
    print("="*60)

    # 演示各个功能
    demo_health_check_models()
    demo_performance_metrics()
    demo_weight_adjustment()

    # 异步演示需要运行在 asyncio 中
    asyncio.run(demo_conversational_checker())

    demo_summary()

    print("\n" + "="*60)
    print("  演示完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
