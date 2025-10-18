"""智能健康检测系统测试"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from fastcc.proxy.health_check_models import (
    ConversationalHealthCheck,
    HealthCheckResult
)
from fastcc.proxy.performance_metrics import PerformanceMetrics
from fastcc.proxy.weight_adjuster import (
    DynamicWeightAdjuster,
    WeightAdjustmentStrategy
)
from fastcc.proxy.conversational_checker import ConversationalHealthChecker
from fastcc.core.endpoint import Endpoint


class TestHealthCheckModels:
    """测试健康检查数据模型"""

    def test_conversational_health_check_creation(self):
        """测试创建健康检查记录"""
        check = ConversationalHealthCheck("test-endpoint")

        assert check.endpoint_id == "test-endpoint"
        assert check.check_id is not None
        assert check.timestamp is not None
        assert check.test_message is not None
        assert check.result is None
        assert check.response_time_ms is None

    def test_conversational_health_check_to_dict(self):
        """测试转换为字典"""
        check = ConversationalHealthCheck("test-endpoint")
        check.result = HealthCheckResult.SUCCESS
        check.response_time_ms = 250.5
        check.response_content = "1"
        check.response_valid = True
        check.response_score = 95.0

        data = check.to_dict()

        assert data['endpoint_id'] == "test-endpoint"
        assert data['result'] == "success"
        assert data['response_time_ms'] == 250.5
        assert data['response_content'] == "1"
        assert data['response_valid'] is True
        assert data['response_score'] == 95.0

    def test_conversational_health_check_from_dict(self):
        """测试从字典创建"""
        data = {
            'endpoint_id': 'test-endpoint',
            'check_id': 'abc123',
            'result': 'success',
            'response_time_ms': 300.0,
            'response_valid': True
        }

        check = ConversationalHealthCheck.from_dict(data)

        assert check.endpoint_id == 'test-endpoint'
        assert check.check_id == 'abc123'
        assert check.result == HealthCheckResult.SUCCESS
        assert check.response_time_ms == 300.0
        assert check.response_valid is True


class TestPerformanceMetrics:
    """测试性能指标"""

    def test_performance_metrics_creation(self):
        """测试创建性能指标"""
        metrics = PerformanceMetrics("test-endpoint")

        assert metrics.endpoint_id == "test-endpoint"
        assert metrics.total_checks == 0
        assert metrics.successful_checks == 0
        assert metrics.failed_checks == 0
        assert metrics.consecutive_successes == 0
        assert metrics.consecutive_failures == 0

    def test_add_success_check_result(self):
        """测试添加成功的检查结果"""
        metrics = PerformanceMetrics("test-endpoint")

        check = ConversationalHealthCheck("test-endpoint")
        check.result = HealthCheckResult.SUCCESS
        check.response_time_ms = 250.0

        metrics.add_check_result(check)

        assert metrics.total_checks == 1
        assert metrics.successful_checks == 1
        assert metrics.failed_checks == 0
        assert metrics.consecutive_successes == 1
        assert metrics.consecutive_failures == 0
        assert len(metrics.response_times) == 1
        assert metrics.response_times[0] == 250.0

    def test_add_failure_check_result(self):
        """测试添加失败的检查结果"""
        metrics = PerformanceMetrics("test-endpoint")

        check = ConversationalHealthCheck("test-endpoint")
        check.result = HealthCheckResult.FAILURE

        metrics.add_check_result(check)

        assert metrics.total_checks == 1
        assert metrics.successful_checks == 0
        assert metrics.failed_checks == 1
        assert metrics.consecutive_successes == 0
        assert metrics.consecutive_failures == 1

    def test_success_rate_calculation(self):
        """测试成功率计算"""
        metrics = PerformanceMetrics("test-endpoint")

        # 添加 7 次成功和 3 次失败
        for i in range(7):
            check = ConversationalHealthCheck("test-endpoint")
            check.result = HealthCheckResult.SUCCESS
            check.response_time_ms = 200.0
            metrics.add_check_result(check)

        for i in range(3):
            check = ConversationalHealthCheck("test-endpoint")
            check.result = HealthCheckResult.FAILURE
            metrics.add_check_result(check)

        assert metrics.total_checks == 10
        assert metrics.success_rate == 70.0

    def test_avg_response_time_calculation(self):
        """测试平均响应时间计算"""
        metrics = PerformanceMetrics("test-endpoint")

        times = [100, 200, 300, 400, 500]
        for time_ms in times:
            check = ConversationalHealthCheck("test-endpoint")
            check.result = HealthCheckResult.SUCCESS
            check.response_time_ms = float(time_ms)
            metrics.add_check_result(check)

        assert metrics.avg_response_time == 300.0

    def test_p95_response_time_calculation(self):
        """测试 P95 响应时间计算"""
        metrics = PerformanceMetrics("test-endpoint")

        # 添加 100 个响应时间，范围从 100-1000ms
        for i in range(100):
            check = ConversationalHealthCheck("test-endpoint")
            check.result = HealthCheckResult.SUCCESS
            check.response_time_ms = float(100 + i * 10)
            metrics.add_check_result(check)

        # P95 应该接近 1000 * 0.95 = 950
        p95 = metrics.p95_response_time
        assert p95 >= 900
        assert p95 <= 1100  # 放宽范围以允许边界情况

    def test_stability_score_all_success(self):
        """测试全部成功时的稳定性评分"""
        metrics = PerformanceMetrics("test-endpoint")

        # 添加 20 次成功，响应时间稳定
        for i in range(20):
            check = ConversationalHealthCheck("test-endpoint")
            check.result = HealthCheckResult.SUCCESS
            check.response_time_ms = 250.0 + i  # 轻微波动
            metrics.add_check_result(check)

        # 全部成功，稳定性应该很高
        assert metrics.stability_score > 80


class TestWeightAdjuster:
    """测试权重调整器"""

    def test_weight_adjustment_strategy_defaults(self):
        """测试权重调整策略默认值"""
        strategy = WeightAdjustmentStrategy()

        assert strategy.base_weight == 100
        assert strategy.min_weight == 10
        assert strategy.max_weight == 200
        assert strategy.smooth_factor == 0.7

    def test_calculate_response_score(self):
        """测试响应时间评分计算"""
        adjuster = DynamicWeightAdjuster()

        # 理想响应时间 (200ms) 应该得高分
        score = adjuster.calculate_response_score(200.0)
        assert score == 100.0

        # 快速响应 (100ms) 应该得满分
        score = adjuster.calculate_response_score(100.0)
        assert score == 100.0

        # 慢速响应 (2000ms) 应该得低分
        score = adjuster.calculate_response_score(2000.0)
        assert score < 30.0

    def test_calculate_failure_penalty(self):
        """测试连续失败惩罚计算"""
        adjuster = DynamicWeightAdjuster()

        # 无失败，无惩罚
        assert adjuster.calculate_failure_penalty(0) == 1.0

        # 1 次失败
        assert adjuster.calculate_failure_penalty(1) == 0.8

        # 2 次失败
        assert adjuster.calculate_failure_penalty(2) == 0.6

        # 3 次失败
        assert abs(adjuster.calculate_failure_penalty(3) - 0.4) < 0.01

        # 4+ 次失败，最大惩罚
        assert adjuster.calculate_failure_penalty(4) == 0.2
        assert adjuster.calculate_failure_penalty(10) == 0.2

    def test_calculate_new_weight_good_performance(self):
        """测试表现良好时的权重计算"""
        adjuster = DynamicWeightAdjuster()

        # 创建表现良好的指标
        metrics = PerformanceMetrics("test-endpoint")
        for i in range(10):
            check = ConversationalHealthCheck("test-endpoint")
            check.result = HealthCheckResult.SUCCESS
            check.response_time_ms = 200.0
            metrics.add_check_result(check)

        # 表现好的 endpoint 权重应该增加
        new_weight = adjuster.calculate_new_weight("test-endpoint", 100.0, metrics)
        assert new_weight > 100.0

    def test_calculate_new_weight_poor_performance(self):
        """测试表现不佳时的权重计算"""
        adjuster = DynamicWeightAdjuster()

        # 创建表现不佳的指标
        metrics = PerformanceMetrics("test-endpoint")

        # 添加一些失败
        for i in range(3):
            check = ConversationalHealthCheck("test-endpoint")
            check.result = HealthCheckResult.FAILURE
            metrics.add_check_result(check)

        # 添加一些慢速响应
        for i in range(7):
            check = ConversationalHealthCheck("test-endpoint")
            check.result = HealthCheckResult.SUCCESS
            check.response_time_ms = 3000.0  # 非常慢
            metrics.add_check_result(check)

        # 表现差的 endpoint 权重应该降低
        new_weight = adjuster.calculate_new_weight("test-endpoint", 100.0, metrics)
        assert new_weight < 100.0

    def test_adjust_endpoint_weight(self):
        """测试调整 endpoint 权重"""
        adjuster = DynamicWeightAdjuster()

        endpoint = Endpoint(
            base_url="https://test.com",
            api_key="test-key",
            weight=100
        )

        metrics = PerformanceMetrics(endpoint.id)
        for i in range(10):
            check = ConversationalHealthCheck(endpoint.id)
            check.result = HealthCheckResult.SUCCESS
            check.response_time_ms = 150.0  # 很快
            metrics.add_check_result(check)

        new_weight = adjuster.adjust_endpoint_weight(endpoint, metrics)

        # 快速稳定的 endpoint 应该获得更高权重
        assert new_weight > 100.0
        assert new_weight <= adjuster.strategy.max_weight


class TestConversationalHealthChecker:
    """测试对话式健康检查器"""

    def test_conversational_health_checker_creation(self):
        """测试创建健康检查器"""
        checker = ConversationalHealthChecker()

        assert checker.timeout == 30
        assert checker.max_tokens == 10
        assert len(checker.test_messages) > 0

    def test_validate_response(self):
        """测试响应验证"""
        checker = ConversationalHealthChecker()

        # 测试 "回复 1" 消息
        assert checker._validate_response("收到消息请回复 1", "1") is True
        assert checker._validate_response("收到消息请回复 1", "OK") is True
        assert checker._validate_response("收到消息请回复 1", "收到") is False

        # 测试 "1+1=?" 消息
        assert checker._validate_response("1+1=?", "2") is True
        assert checker._validate_response("1+1=?", "1") is False

        # 测试 ping/pong
        assert checker._validate_response("ping test", "pong") is True
        assert checker._validate_response("ping test", "hello") is False

    def test_calculate_response_score(self):
        """测试响应质量评分"""
        checker = ConversationalHealthChecker()

        # 快速有效的响应应该得高分
        score = checker._calculate_response_score(300, True, "1")
        assert score >= 80

        # 慢速响应应该得低分
        score = checker._calculate_response_score(3000, True, "1")
        assert score < 80

        # 无效响应应该得低分
        score = checker._calculate_response_score(300, False, "wrong answer")
        assert score < 60


def test_end_to_end_health_check_flow():
    """测试端到端的健康检查流程"""
    # 1. 创建 endpoint
    endpoint = Endpoint(
        base_url="https://api.test.com",
        api_key="test-key",
        weight=100
    )

    # 2. 创建性能指标
    metrics = PerformanceMetrics(endpoint.id)

    # 3. 模拟多次健康检查
    for i in range(10):
        check = ConversationalHealthCheck(endpoint.id)
        check.result = HealthCheckResult.SUCCESS if i < 8 else HealthCheckResult.FAILURE
        check.response_time_ms = 200.0 + i * 10
        check.response_valid = True
        check.response_score = 90.0

        metrics.add_check_result(check)

    # 4. 计算权重调整
    adjuster = DynamicWeightAdjuster()
    new_weight = adjuster.calculate_new_weight(endpoint.id, 100.0, metrics)

    # 5. 验证结果
    assert metrics.total_checks == 10
    assert metrics.success_rate == 80.0
    assert metrics.avg_response_time > 200.0
    assert new_weight != 100.0  # 权重应该有变化


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
