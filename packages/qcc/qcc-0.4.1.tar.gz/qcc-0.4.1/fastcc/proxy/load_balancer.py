"""QCC Load Balancer - 负载均衡器"""

import random
from typing import List, Optional
from enum import Enum


class LoadBalanceStrategy(Enum):
    """负载均衡策略"""
    WEIGHTED = "weighted"  # 加权轮询
    ROUND_ROBIN = "round_robin"  # 轮询
    RANDOM = "random"  # 随机
    LEAST_CONNECTIONS = "least_connections"  # 最少连接
    PRIORITY_FAILOVER = "priority_failover"  # 主备优先级（优先使用低priority值的节点）


class LoadBalancer:
    """负载均衡器

    支持多种负载均衡策略选择最佳 endpoint
    """

    def __init__(self, strategy: str = "weighted"):
        """初始化负载均衡器

        Args:
            strategy: 负载均衡策略
        """
        self.strategy = LoadBalanceStrategy(strategy)
        self.round_robin_index = 0

    async def select_endpoint(self, endpoints: List) -> Optional:
        """选择 endpoint

        Args:
            endpoints: 可用的 endpoint 列表

        Returns:
            选中的 endpoint，如果没有可用的返回 None
        """
        if not endpoints:
            return None

        # 过滤健康的 endpoint
        healthy_endpoints = [ep for ep in endpoints if ep.is_healthy()]

        if not healthy_endpoints:
            return None

        if self.strategy == LoadBalanceStrategy.WEIGHTED:
            return self._weighted_select(healthy_endpoints)
        elif self.strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin_select(healthy_endpoints)
        elif self.strategy == LoadBalanceStrategy.RANDOM:
            return self._random_select(healthy_endpoints)
        elif self.strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(healthy_endpoints)
        elif self.strategy == LoadBalanceStrategy.PRIORITY_FAILOVER:
            return self._priority_failover_select(healthy_endpoints)

        return healthy_endpoints[0]

    def _weighted_select(self, endpoints: List):
        """加权随机选择"""
        total_weight = sum(ep.weight for ep in endpoints)
        if total_weight == 0:
            return random.choice(endpoints)

        rand_weight = random.uniform(0, total_weight)
        cumulative_weight = 0

        for endpoint in endpoints:
            cumulative_weight += endpoint.weight
            if rand_weight <= cumulative_weight:
                return endpoint

        return endpoints[-1]

    def _round_robin_select(self, endpoints: List):
        """轮询选择"""
        endpoint = endpoints[self.round_robin_index % len(endpoints)]
        self.round_robin_index += 1
        return endpoint

    def _random_select(self, endpoints: List):
        """随机选择"""
        return random.choice(endpoints)

    def _least_connections_select(self, endpoints: List):
        """最少连接选择（基于总请求数）"""
        return min(endpoints, key=lambda ep: ep.health_status['total_requests'])

    def _priority_failover_select(self, endpoints: List):
        """主备优先级选择

        按照 priority 值从小到大排序，始终选择优先级最高（数字最小）的健康节点。
        只有当高优先级节点不健康时，才会自动切换到低优先级节点。
        一旦高优先级节点恢复健康，下次请求会立即切换回去。

        Args:
            endpoints: 健康的 endpoint 列表

        Returns:
            优先级最高的健康 endpoint
        """
        # 按 priority 值从小到大排序（数字越小优先级越高）
        sorted_endpoints = sorted(endpoints, key=lambda ep: ep.priority)

        # 返回优先级最高（priority 值最小）的节点
        return sorted_endpoints[0]
