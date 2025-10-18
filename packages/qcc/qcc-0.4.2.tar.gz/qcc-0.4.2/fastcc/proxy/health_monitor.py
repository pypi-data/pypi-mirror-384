"""QCC Health Monitor - 智能健康监控器

通过真实的 AI 对话测试来评估 endpoint 的健康状态和性能，
并根据性能表现动态调整权重，实现智能负载均衡。
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime

from .conversational_checker import ConversationalHealthChecker
from .performance_metrics import PerformanceMetrics
from .weight_adjuster import DynamicWeightAdjuster
from .health_check_models import HealthCheckResult

logger = logging.getLogger(__name__)


class HealthMonitor:
    """智能健康监控器

    定时使用对话测试检查所有 endpoint 的健康状态，
    收集性能指标，并动态调整权重。
    """

    def __init__(
        self,
        check_interval: int = 60,
        enable_weight_adjustment: bool = True,
        min_checks_before_adjustment: int = 3
    ):
        """初始化健康监控器

        Args:
            check_interval: 检查间隔（秒）
            enable_weight_adjustment: 是否启用动态权重调整
            min_checks_before_adjustment: 调整权重前的最少检查次数
        """
        self.check_interval = check_interval
        self.enable_weight_adjustment = enable_weight_adjustment
        self.min_checks_before_adjustment = min_checks_before_adjustment
        self.running = False

        # 核心组件
        self.conversational_checker = ConversationalHealthChecker()
        self.weight_adjuster = DynamicWeightAdjuster()
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}

        # 统计信息
        self.total_checks = 0
        self.last_check_time: Optional[datetime] = None

    async def start(self, endpoints: List = None):
        """启动健康监控

        Args:
            endpoints: 需要监控的 endpoint 列表
        """
        if self.running:
            logger.warning("健康监控器已经在运行")
            return

        self.running = True

        logger.info("[OK] 智能健康监控已启动")
        logger.info(f"  - 检查间隔: {self.check_interval}秒")
        logger.info(f"  - 检测方式: 对话测试")
        logger.info(
            f"  - 动态权重: {'已启用' if self.enable_weight_adjustment else '已禁用'}"
        )

        try:
            while self.running:
                if endpoints:
                    await self.perform_health_check(endpoints)
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.info("健康监控器收到停止信号")
        finally:
            await self.stop()

    async def stop(self):
        """停止健康监控"""
        self.running = False
        logger.info("[OK] 健康监控器已停止")

    async def perform_health_check(self, endpoints: List):
        """执行健康检查

        Args:
            endpoints: Endpoint 列表
        """
        if not endpoints:
            return

        enabled_endpoints = [ep for ep in endpoints if ep.enabled]
        if not enabled_endpoints:
            logger.debug("没有启用的 endpoint 需要检查")
            return

        logger.info(f"\n🔍 开始健康检查 ({len(enabled_endpoints)} 个 endpoint)")

        # 执行对话测试
        check_results = await self.conversational_checker.check_all_endpoints(
            enabled_endpoints
        )

        # 更新 endpoint 健康状态和性能指标
        for check in check_results:
            # 更新性能指标
            self._update_metrics(check)

            # 更新 endpoint 健康状态
            await self._update_endpoint_health(check, enabled_endpoints)

        # 调整权重
        if self.enable_weight_adjustment:
            await self._adjust_weights(endpoints)

        # 显示摘要
        self._print_check_summary(check_results)

        # 更新统计
        self.total_checks += 1
        self.last_check_time = datetime.now()

    def _update_metrics(self, check):
        """更新性能指标

        Args:
            check: ConversationalHealthCheck 实例
        """
        endpoint_id = check.endpoint_id

        if endpoint_id not in self.performance_metrics:
            self.performance_metrics[endpoint_id] = PerformanceMetrics(endpoint_id)

        metrics = self.performance_metrics[endpoint_id]
        metrics.add_check_result(check)

    async def _update_endpoint_health(self, check, endpoints: List):
        """根据检查结果更新 endpoint 健康状态

        Args:
            check: ConversationalHealthCheck 实例
            endpoints: Endpoint 列表
        """
        # 查找对应的 endpoint
        endpoint = None
        for ep in endpoints:
            if ep.id == check.endpoint_id:
                endpoint = ep
                break

        if not endpoint:
            return

        # 根据检查结果更新健康状态
        # 判断真正健康：需要同时满足 result=SUCCESS 和 response_valid=True
        if check.result == HealthCheckResult.SUCCESS and check.response_valid:
            # 成功：设置为健康状态
            await endpoint.update_health_status(
                status='healthy',
                increment_requests=True,
                is_failure=False,
                response_time=check.response_time_ms
            )
            logger.debug(f"Endpoint {endpoint.id} 健康")
        elif check.result == HealthCheckResult.SUCCESS and not check.response_valid:
            # HTTP 200 但响应无效（例如：没有返回验证码）
            await endpoint.update_health_status(
                status='unhealthy',
                increment_requests=True,
                is_failure=True
            )
            logger.warning(
                f"Endpoint {endpoint.id} 响应无效（未包含验证码）"
            )

        elif check.result in [HealthCheckResult.TIMEOUT, HealthCheckResult.FAILURE]:
            # 超时或失败：设置为不健康状态
            await endpoint.update_health_status(
                status='unhealthy',
                increment_requests=True,
                is_failure=True
            )
            logger.warning(
                f"Endpoint {endpoint.id} 不健康 "
                f"(连续失败 {endpoint.health_status['consecutive_failures']} 次)"
            )

        elif check.result == HealthCheckResult.RATE_LIMITED:
            # 限流：设置为降级状态
            await endpoint.update_health_status(
                status='degraded',
                increment_requests=True,
                is_failure=False
            )
            logger.info(f"Endpoint {endpoint.id} 被限流，降级")

        elif check.result == HealthCheckResult.INVALID_KEY:
            # API Key 无效：禁用 endpoint
            await endpoint.update_health_status(
                status='unhealthy',
                increment_requests=True,
                is_failure=True
            )
            endpoint.enabled = False
            logger.error(
                f"Endpoint {endpoint.id} API Key 无效，已自动禁用"
            )

    async def _adjust_weights(self, endpoints: List):
        """调整 endpoint 权重

        Args:
            endpoints: Endpoint 列表
        """
        for endpoint in endpoints:
            metrics = self.performance_metrics.get(endpoint.id)

            # 检查次数太少时不调整权重
            if not metrics or metrics.total_checks < self.min_checks_before_adjustment:
                continue

            new_weight = self.weight_adjuster.adjust_endpoint_weight(
                endpoint,
                metrics
            )

            # 更新 endpoint 权重
            if abs(new_weight - endpoint.weight) > 1:
                endpoint.weight = new_weight
                # TODO: 持久化到配置
                # self._save_endpoint_weight(endpoint)

    def _print_check_summary(self, results: List):
        """打印检查摘要

        Args:
            results: ConversationalHealthCheck 列表
        """
        logger.info(f"\n[#] 健康检查完成:")

        for check in results:
            result_icon = {
                HealthCheckResult.SUCCESS: '[OK]',
                HealthCheckResult.FAILURE: '[X]',
                HealthCheckResult.TIMEOUT: '⏱️',
                HealthCheckResult.RATE_LIMITED: '🚫',
                HealthCheckResult.INVALID_KEY: '🔑'
            }.get(check.result, '❓')

            metrics = self.performance_metrics.get(check.endpoint_id)

            # 检查是否真正成功（result=SUCCESS 且 response_valid=True）
            if check.result == HealthCheckResult.SUCCESS and check.response_valid:
                weight_info = f"权重: {self._get_endpoint_weight(check.endpoint_id)}" if metrics else ""
                logger.info(
                    f"  {result_icon} {check.endpoint_id}: "
                    f"{check.response_time_ms:.0f}ms "
                    f"(评分: {check.response_score:.0f}/100, {weight_info})"
                )
            elif check.result == HealthCheckResult.SUCCESS and not check.response_valid:
                # HTTP 200 但响应无效
                logger.info(
                    f"  [X] {check.endpoint_id}: "
                    f"响应无效（未包含验证码）"
                )
            else:
                logger.info(
                    f"  {result_icon} {check.endpoint_id}: "
                    f"{check.result.value} - {check.error_message}"
                )

    def _get_endpoint_weight(self, endpoint_id: str) -> str:
        """获取 endpoint 权重信息

        Args:
            endpoint_id: Endpoint ID

        Returns:
            权重信息字符串
        """
        # TODO: 从实际的 endpoint 对象获取权重
        return "N/A"

    def get_metrics(self, endpoint_id: Optional[str] = None) -> Dict:
        """获取性能指标

        Args:
            endpoint_id: Endpoint ID，如果为 None 则返回所有指标

        Returns:
            性能指标字典
        """
        if endpoint_id:
            metrics = self.performance_metrics.get(endpoint_id)
            return metrics.to_dict() if metrics else {}
        else:
            return {
                ep_id: metrics.to_dict()
                for ep_id, metrics in self.performance_metrics.items()
            }

    async def check_all_endpoints(self, endpoints: List):
        """检查所有 endpoint（兼容旧接口）

        Args:
            endpoints: Endpoint 列表
        """
        await self.perform_health_check(endpoints)

    async def check_endpoint(self, endpoint):
        """检查单个 endpoint（兼容旧接口）

        Args:
            endpoint: Endpoint 实例

        Returns:
            ConversationalHealthCheck 实例
        """
        return await self.conversational_checker.check_endpoint(endpoint)
