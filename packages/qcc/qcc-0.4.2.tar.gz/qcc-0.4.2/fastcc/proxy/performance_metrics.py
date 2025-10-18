"""性能指标统计模块"""

import statistics
from collections import deque
from datetime import datetime
from typing import List, Dict, Any
from .health_check_models import ConversationalHealthCheck, HealthCheckResult


class PerformanceMetrics:
    """性能指标统计

    跟踪和分析 endpoint 的性能表现，包括响应时间、成功率、
    稳定性等多个维度的指标。
    """

    def __init__(self, endpoint_id: str, history_size: int = 100):
        """初始化性能指标

        Args:
            endpoint_id: Endpoint ID
            history_size: 保存的历史记录数量
        """
        self.endpoint_id = endpoint_id
        self.history_size = history_size

        # 历史记录（最近 N 次检查）
        self.check_history: deque = deque(maxlen=history_size)

        # 实时统计
        self.total_checks = 0
        self.successful_checks = 0
        self.failed_checks = 0
        self.timeout_checks = 0
        self.rate_limited_checks = 0

        # 连续状态
        self.consecutive_successes = 0
        self.consecutive_failures = 0

        # 响应时间统计
        self.response_times: deque = deque(maxlen=history_size)

        # 最后更新时间
        self.last_update = datetime.now()

    def add_check_result(self, check: ConversationalHealthCheck):
        """添加检查结果

        Args:
            check: 健康检查记录
        """
        self.check_history.append(check)
        self.total_checks += 1
        self.last_update = datetime.now()

        # 更新计数
        if check.result == HealthCheckResult.SUCCESS:
            self.successful_checks += 1
            self.consecutive_successes += 1
            self.consecutive_failures = 0

            if check.response_time_ms:
                self.response_times.append(check.response_time_ms)

        elif check.result == HealthCheckResult.TIMEOUT:
            self.timeout_checks += 1
            self.failed_checks += 1
            self.consecutive_failures += 1
            self.consecutive_successes = 0

        elif check.result == HealthCheckResult.RATE_LIMITED:
            self.rate_limited_checks += 1
            # 限流不算完全失败，但重置连续成功
            self.consecutive_successes = 0

        else:
            self.failed_checks += 1
            self.consecutive_failures += 1
            self.consecutive_successes = 0

    @property
    def success_rate(self) -> float:
        """成功率 (0-100)

        Returns:
            成功率百分比
        """
        if self.total_checks == 0:
            return 0.0
        return (self.successful_checks / self.total_checks) * 100

    @property
    def recent_success_rate(self) -> float:
        """最近的成功率 (最近 20 次)

        Returns:
            最近成功率百分比
        """
        recent_checks = list(self.check_history)[-20:]
        if not recent_checks:
            return 0.0

        successes = sum(
            1 for check in recent_checks
            if check.result == HealthCheckResult.SUCCESS
        )
        return (successes / len(recent_checks)) * 100

    @property
    def avg_response_time(self) -> float:
        """平均响应时间（毫秒）

        Returns:
            平均响应时间
        """
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)

    @property
    def p95_response_time(self) -> float:
        """P95 响应时间（毫秒）

        Returns:
            P95 响应时间
        """
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[index] if index < len(sorted_times) else sorted_times[-1]

    @property
    def stability_score(self) -> float:
        """稳定性评分 (0-100)

        综合考虑成功率、响应时间稳定性、连续失败次数等因素。

        Returns:
            稳定性评分
        """
        if not self.response_times or self.total_checks == 0:
            return 0.0

        # 成功率权重 50%
        success_component = self.recent_success_rate * 0.5

        # 响应时间稳定性权重 30%
        if len(self.response_times) > 1:
            stdev = statistics.stdev(self.response_times)
            mean = statistics.mean(self.response_times)
            # 变异系数：标准差 / 平均值
            coefficient_of_variation = (stdev / mean) if mean > 0 else 1.0
            # 变异系数越小越稳定
            stability_component = max(0, (1 - coefficient_of_variation)) * 30
        else:
            stability_component = 30

        # 连续失败惩罚 20%
        # 每次连续失败扣 5 分
        failure_penalty = max(0, 20 - (self.consecutive_failures * 5))

        return min(100, success_component + stability_component + failure_penalty)

    def get_recent_checks(self, count: int = 10) -> List[ConversationalHealthCheck]:
        """获取最近的检查记录

        Args:
            count: 返回的记录数量

        Returns:
            最近的检查记录列表
        """
        return list(self.check_history)[-count:]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            包含所有指标的字典
        """
        return {
            'endpoint_id': self.endpoint_id,
            'total_checks': self.total_checks,
            'successful_checks': self.successful_checks,
            'failed_checks': self.failed_checks,
            'timeout_checks': self.timeout_checks,
            'rate_limited_checks': self.rate_limited_checks,
            'success_rate': round(self.success_rate, 2),
            'recent_success_rate': round(self.recent_success_rate, 2),
            'avg_response_time': round(self.avg_response_time, 2),
            'p95_response_time': round(self.p95_response_time, 2),
            'stability_score': round(self.stability_score, 2),
            'consecutive_successes': self.consecutive_successes,
            'consecutive_failures': self.consecutive_failures,
            'last_update': self.last_update.isoformat()
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"PerformanceMetrics("
            f"endpoint={self.endpoint_id}, "
            f"checks={self.total_checks}, "
            f"success_rate={self.success_rate:.1f}%, "
            f"avg_time={self.avg_response_time:.0f}ms)"
        )
