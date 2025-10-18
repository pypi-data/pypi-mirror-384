# 智能健康检测与动态权重调整 - 技术实现方案

## 📋 功能概述

通过真实的 AI 对话测试来评估 endpoint 的健康状态和性能，根据响应时间、错误率等指标动态调整权重，实现智能的负载均衡。

**版本**: v1.0
**创建日期**: 2025-10-16
**相关文档**: claude-code-proxy-development-plan.md, auto-failover-mechanism.md

---

## 🎯 核心需求

### 为什么需要真实对话测试？

**传统 ping 测试的局限性**:
- ❌ 只测试网络连通性，不测试 API 可用性
- ❌ 不能反映真实的 AI 响应质量
- ❌ 无法检测 API Key 是否有效
- ❌ 不能评估模型负载和限流情况

**真实对话测试的优势**:
- ✅ 测试完整的 API 调用流程
- ✅ 验证 API Key 的有效性
- ✅ 评估实际响应时间和质量
- ✅ 检测限流和配额问题
- ✅ 模拟真实使用场景

---

## 🏗️ 系统设计

### 1. 健康检测流程

```
┌─────────────────────────────────────────────────────────────┐
│              Health Check Scheduler (定时调度器)            │
│              - 每 60 秒执行一次                              │
│              - 并发检测所有 endpoint                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│           Conversational Health Checker (对话测试器)        │
│                                                              │
│  测试消息: "收到消息请回复 1"                                │
│                                                              │
│  检测指标:                                                   │
│  ├─ 响应时间 (Response Time)                                │
│  ├─ 是否成功 (Success/Failure)                              │
│  ├─ 响应内容 (Response Content)                             │
│  ├─ 错误类型 (Error Type)                                   │
│  └─ 限流检测 (Rate Limit Detection)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│         Performance Analyzer (性能分析器)                    │
│                                                              │
│  分析维度:                                                   │
│  ├─ 平均响应时间 (Avg Response Time)                        │
│  ├─ P95 响应时间 (P95 Latency)                              │
│  ├─ 成功率 (Success Rate)                                   │
│  ├─ 连续失败次数 (Consecutive Failures)                     │
│  ├─ 近期错误率 (Recent Error Rate)                          │
│  └─ 稳定性评分 (Stability Score)                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│      Dynamic Weight Adjuster (动态权重调整器)               │
│                                                              │
│  调整策略:                                                   │
│  ├─ 基于响应时间调整 (faster = higher weight)              │
│  ├─ 基于成功率调整 (more reliable = higher weight)         │
│  ├─ 惩罚连续失败 (consecutive failures → lower weight)     │
│  ├─ 奖励稳定表现 (stable performance → higher weight)      │
│  └─ 平滑调整避免震荡 (smooth adjustment)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│            Endpoint Weight Update (更新权重)                │
│                                                              │
│  endpoint-1: 100 → 120 (表现优秀，权重提升)                 │
│  endpoint-2: 100 → 80  (响应慢，权重降低)                   │
│  endpoint-3: 100 → 20  (频繁失败，权重大幅降低)             │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 数据结构设计

### 1. 健康检测记录

```python
# fastcc/proxy/health_check_record.py

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class HealthCheckResult(Enum):
    """健康检查结果"""
    SUCCESS = "success"              # 成功
    FAILURE = "failure"              # 失败
    TIMEOUT = "timeout"              # 超时
    RATE_LIMITED = "rate_limited"    # 被限流
    INVALID_KEY = "invalid_key"      # API Key 无效
    MODEL_ERROR = "model_error"      # 模型错误

class ConversationalHealthCheck:
    """对话式健康检查记录"""

    def __init__(self, endpoint_id: str):
        self.endpoint_id = endpoint_id
        self.check_id = str(uuid.uuid4())[:8]
        self.timestamp = datetime.now().isoformat()

        # 测试消息
        self.test_message = "收到消息请回复 1"

        # 检测结果
        self.result: HealthCheckResult = None
        self.response_time_ms: Optional[float] = None  # 响应时间（毫秒）
        self.response_content: Optional[str] = None
        self.error_message: Optional[str] = None
        self.error_code: Optional[str] = None

        # 响应质量评估
        self.response_valid: bool = False  # 响应是否符合预期
        self.response_score: float = 0.0   # 响应质量评分 (0-100)

        # 额外信息
        self.tokens_used: Optional[int] = None
        self.model_used: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'endpoint_id': self.endpoint_id,
            'check_id': self.check_id,
            'timestamp': self.timestamp,
            'test_message': self.test_message,
            'result': self.result.value if self.result else None,
            'response_time_ms': self.response_time_ms,
            'response_content': self.response_content,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'response_valid': self.response_valid,
            'response_score': self.response_score,
            'tokens_used': self.tokens_used,
            'model_used': self.model_used
        }
```

### 2. 性能指标模型

```python
# fastcc/proxy/performance_metrics.py

from collections import deque
from typing import List, Optional
import statistics

class PerformanceMetrics:
    """性能指标统计"""

    def __init__(self, endpoint_id: str, history_size: int = 100):
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
        """添加检查结果"""
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
            self.consecutive_failures += 1
            self.consecutive_successes = 0

        elif check.result == HealthCheckResult.RATE_LIMITED:
            self.rate_limited_checks += 1
            # 限流不算失败，但重置连续成功
            self.consecutive_successes = 0

        else:
            self.failed_checks += 1
            self.consecutive_failures += 1
            self.consecutive_successes = 0

    @property
    def success_rate(self) -> float:
        """成功率 (0-100)"""
        if self.total_checks == 0:
            return 0.0
        return (self.successful_checks / self.total_checks) * 100

    @property
    def recent_success_rate(self) -> float:
        """最近的成功率 (最近 20 次)"""
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
        """平均响应时间（毫秒）"""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)

    @property
    def p95_response_time(self) -> float:
        """P95 响应时间（毫秒）"""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[index] if index < len(sorted_times) else sorted_times[-1]

    @property
    def stability_score(self) -> float:
        """稳定性评分 (0-100)

        考虑因素:
        - 成功率
        - 响应时间的稳定性（标准差）
        - 连续失败次数
        """
        if not self.response_times:
            return 0.0

        # 成功率权重 50%
        success_component = self.recent_success_rate * 0.5

        # 响应时间稳定性权重 30%
        if len(self.response_times) > 1:
            stdev = statistics.stdev(self.response_times)
            mean = statistics.mean(self.response_times)
            coefficient_of_variation = (stdev / mean) if mean > 0 else 1.0
            stability_component = max(0, (1 - coefficient_of_variation)) * 30
        else:
            stability_component = 30

        # 连续失败惩罚 20%
        failure_penalty = max(0, 20 - (self.consecutive_failures * 5))

        return min(100, success_component + stability_component + failure_penalty)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'endpoint_id': self.endpoint_id,
            'total_checks': self.total_checks,
            'successful_checks': self.successful_checks,
            'failed_checks': self.failed_checks,
            'success_rate': round(self.success_rate, 2),
            'recent_success_rate': round(self.recent_success_rate, 2),
            'avg_response_time': round(self.avg_response_time, 2),
            'p95_response_time': round(self.p95_response_time, 2),
            'stability_score': round(self.stability_score, 2),
            'consecutive_successes': self.consecutive_successes,
            'consecutive_failures': self.consecutive_failures,
            'last_update': self.last_update.isoformat()
        }
```

### 3. 动态权重调整策略

```python
# fastcc/proxy/weight_adjuster.py

class WeightAdjustmentStrategy:
    """权重调整策略"""

    def __init__(self):
        # 调整参数
        self.base_weight = 100
        self.min_weight = 10
        self.max_weight = 200

        # 调整因子
        self.response_time_factor = 0.3    # 响应时间影响因子
        self.success_rate_factor = 0.4     # 成功率影响因子
        self.stability_factor = 0.2        # 稳定性影响因子
        self.consecutive_failure_penalty = 0.1  # 连续失败惩罚因子

        # 平滑调整
        self.smooth_factor = 0.7  # 新权重的平滑系数

class DynamicWeightAdjuster:
    """动态权重调整器"""

    def __init__(self, strategy: WeightAdjustmentStrategy = None):
        self.strategy = strategy or WeightAdjustmentStrategy()
        self.metrics_store: Dict[str, PerformanceMetrics] = {}

    def calculate_new_weight(
        self,
        endpoint_id: str,
        current_weight: float,
        metrics: PerformanceMetrics
    ) -> float:
        """计算新的权重

        算法:
        1. 基于响应时间: 越快权重越高
        2. 基于成功率: 成功率高权重高
        3. 基于稳定性: 稳定性好权重高
        4. 连续失败惩罚: 连续失败权重大幅降低
        """

        # 1. 响应时间评分 (0-100)
        # 假设理想响应时间为 200ms，每增加 100ms 减少 10 分
        response_score = max(
            0,
            100 - ((metrics.avg_response_time - 200) / 100) * 10
        )

        # 2. 成功率评分 (0-100)
        success_score = metrics.recent_success_rate

        # 3. 稳定性评分 (0-100)
        stability_score = metrics.stability_score

        # 4. 连续失败惩罚
        failure_penalty = 1.0
        if metrics.consecutive_failures > 0:
            # 连续失败 1 次: 0.8, 2 次: 0.6, 3 次: 0.4, 4+ 次: 0.2
            failure_penalty = max(0.2, 1.0 - (metrics.consecutive_failures * 0.2))

        # 综合计算新权重
        weighted_score = (
            response_score * self.strategy.response_time_factor +
            success_score * self.strategy.success_rate_factor +
            stability_score * self.strategy.stability_factor
        ) * failure_penalty

        # 将评分转换为权重（0-100 分 → min_weight-max_weight）
        new_weight = (
            self.strategy.min_weight +
            (weighted_score / 100) *
            (self.strategy.max_weight - self.strategy.min_weight)
        )

        # 平滑调整：新权重 = 旧权重 * (1 - α) + 新计算权重 * α
        smoothed_weight = (
            current_weight * (1 - self.strategy.smooth_factor) +
            new_weight * self.strategy.smooth_factor
        )

        # 限制范围
        final_weight = max(
            self.strategy.min_weight,
            min(self.strategy.max_weight, smoothed_weight)
        )

        return round(final_weight, 2)

    def adjust_endpoint_weight(
        self,
        endpoint: Endpoint,
        metrics: PerformanceMetrics
    ) -> float:
        """调整 endpoint 的权重"""

        current_weight = endpoint.weight
        new_weight = self.calculate_new_weight(
            endpoint.id,
            current_weight,
            metrics
        )

        # 记录权重变化
        if abs(new_weight - current_weight) > 1:
            change = new_weight - current_weight
            change_pct = (change / current_weight) * 100

            print(f"📊 权重调整: {endpoint.id}")
            print(f"   当前权重: {current_weight:.2f}")
            print(f"   新权重: {new_weight:.2f} ({change:+.2f}, {change_pct:+.1f}%)")
            print(f"   原因:")
            print(f"     - 平均响应: {metrics.avg_response_time:.0f}ms")
            print(f"     - 成功率: {metrics.recent_success_rate:.1f}%")
            print(f"     - 稳定性: {metrics.stability_score:.1f}")
            print(f"     - 连续失败: {metrics.consecutive_failures}")

        return new_weight
```

---

## 🔧 核心模块实现

### 1. 对话式健康检查器

```python
# fastcc/proxy/conversational_checker.py

import asyncio
import aiohttp
from typing import Optional
import time

class ConversationalHealthChecker:
    """对话式健康检查器"""

    def __init__(self):
        self.test_messages = [
            "收到消息请回复 1",
            "你好，请回复确认",
            "测试消息，请回答：1+1=?",
            "健康检查：请回复 OK"
        ]
        self.timeout = 30  # 30 秒超时
        self.max_tokens = 10  # 只需要简短回复

    async def check_endpoint(
        self,
        endpoint: Endpoint
    ) -> ConversationalHealthCheck:
        """检查单个 endpoint"""

        check = ConversationalHealthCheck(endpoint.id)

        # 随机选择一个测试消息（避免缓存）
        import random
        check.test_message = random.choice(self.test_messages)

        try:
            start_time = time.time()

            # 发送测试请求
            response = await self._send_test_message(
                endpoint,
                check.test_message
            )

            end_time = time.time()
            check.response_time_ms = (end_time - start_time) * 1000

            # 解析响应
            if response:
                check.result = HealthCheckResult.SUCCESS
                check.response_content = response.get('content', '')
                check.tokens_used = response.get('usage', {}).get('total_tokens', 0)
                check.model_used = response.get('model', '')

                # 验证响应质量
                check.response_valid = self._validate_response(
                    check.test_message,
                    check.response_content
                )
                check.response_score = self._calculate_response_score(
                    check.response_time_ms,
                    check.response_valid,
                    check.response_content
                )
            else:
                check.result = HealthCheckResult.FAILURE

        except asyncio.TimeoutError:
            check.result = HealthCheckResult.TIMEOUT
            check.error_message = "请求超时"

        except aiohttp.ClientError as e:
            error_str = str(e).lower()

            if 'rate limit' in error_str or '429' in error_str:
                check.result = HealthCheckResult.RATE_LIMITED
                check.error_message = "API 限流"
            elif 'unauthorized' in error_str or '401' in error_str:
                check.result = HealthCheckResult.INVALID_KEY
                check.error_message = "API Key 无效"
            else:
                check.result = HealthCheckResult.FAILURE
                check.error_message = str(e)

        except Exception as e:
            check.result = HealthCheckResult.FAILURE
            check.error_message = f"未知错误: {str(e)}"

        return check

    async def _send_test_message(
        self,
        endpoint: Endpoint,
        message: str
    ) -> Optional[Dict]:
        """发送测试消息到 endpoint"""

        # 构建 API 请求
        url = f"{endpoint.base_url}/v1/messages"

        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': endpoint.api_key,
            'anthropic-version': '2023-06-01'
        }

        payload = {
            'model': 'claude-3-haiku-20240307',  # 使用最快的模型
            'max_tokens': self.max_tokens,
            'messages': [
                {
                    'role': 'user',
                    'content': message
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'content': data.get('content', [{}])[0].get('text', ''),
                        'usage': data.get('usage', {}),
                        'model': data.get('model', '')
                    }
                elif response.status == 429:
                    raise aiohttp.ClientError("Rate limit exceeded")
                elif response.status == 401:
                    raise aiohttp.ClientError("Unauthorized")
                else:
                    error_text = await response.text()
                    raise aiohttp.ClientError(f"HTTP {response.status}: {error_text}")

    def _validate_response(self, test_message: str, response: str) -> bool:
        """验证响应是否合理"""
        if not response:
            return False

        # 简单验证：响应不为空且长度合理
        response_lower = response.lower().strip()

        # 对于 "收到消息请回复 1"，检查是否包含 "1"
        if "回复 1" in test_message or "回答：1" in test_message:
            return '1' in response_lower or 'one' in response_lower or 'ok' in response_lower

        # 对于 "1+1=?" 问题
        if "1+1" in test_message:
            return '2' in response_lower or 'two' in response_lower

        # 通用验证：有响应就认为是有效的
        return len(response) > 0 and len(response) < 200

    def _calculate_response_score(
        self,
        response_time: float,
        is_valid: bool,
        content: str
    ) -> float:
        """计算响应质量评分 (0-100)"""

        score = 0.0

        # 1. 响应有效性 (50 分)
        if is_valid:
            score += 50

        # 2. 响应时间 (30 分)
        # 优秀: < 500ms = 30 分
        # 良好: < 1000ms = 20 分
        # 一般: < 2000ms = 10 分
        # 较差: >= 2000ms = 0 分
        if response_time < 500:
            score += 30
        elif response_time < 1000:
            score += 20
        elif response_time < 2000:
            score += 10

        # 3. 响应内容 (20 分)
        if content:
            # 简洁的回答更好
            if len(content) < 50:
                score += 20
            elif len(content) < 100:
                score += 15
            else:
                score += 10

        return score

    async def check_all_endpoints(
        self,
        endpoints: List[Endpoint]
    ) -> List[ConversationalHealthCheck]:
        """并发检查所有 endpoint"""

        tasks = [
            self.check_endpoint(endpoint)
            for endpoint in endpoints
            if endpoint.enabled
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常
        valid_results = [
            r for r in results
            if isinstance(r, ConversationalHealthCheck)
        ]

        return valid_results
```

### 2. 集成到 Health Monitor

```python
# fastcc/proxy/health_monitor.py (扩展)

class HealthMonitor:
    """健康监控器（扩展版本）"""

    def __init__(self):
        self.conversational_checker = ConversationalHealthChecker()
        self.weight_adjuster = DynamicWeightAdjuster()
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}

        self.check_interval = 60  # 60 秒检查一次
        self.running = False

    async def start(self):
        """启动监控"""
        self.running = True
        print("✓ 智能健康监控已启动")
        print(f"  - 检查间隔: {self.check_interval}秒")
        print(f"  - 检测方式: 对话测试")
        print(f"  - 动态权重: 已启用")

        while self.running:
            await self.perform_health_check()
            await asyncio.sleep(self.check_interval)

    async def perform_health_check(self):
        """执行健康检查"""

        # 获取所有需要检查的 endpoint
        endpoints = self._get_all_endpoints()

        if not endpoints:
            return

        print(f"\n🔍 开始健康检查 ({len(endpoints)} 个 endpoint)")

        # 执行对话测试
        check_results = await self.conversational_checker.check_all_endpoints(endpoints)

        # 更新性能指标
        for check in check_results:
            self._update_metrics(check)

        # 调整权重
        await self._adjust_weights(endpoints)

        # 显示摘要
        self._print_check_summary(check_results)

    def _update_metrics(self, check: ConversationalHealthCheck):
        """更新性能指标"""

        endpoint_id = check.endpoint_id

        if endpoint_id not in self.performance_metrics:
            self.performance_metrics[endpoint_id] = PerformanceMetrics(endpoint_id)

        metrics = self.performance_metrics[endpoint_id]
        metrics.add_check_result(check)

    async def _adjust_weights(self, endpoints: List[Endpoint]):
        """调整 endpoint 权重"""

        for endpoint in endpoints:
            metrics = self.performance_metrics.get(endpoint.id)
            if not metrics or metrics.total_checks < 3:
                # 检查次数太少，不调整权重
                continue

            new_weight = self.weight_adjuster.adjust_endpoint_weight(
                endpoint,
                metrics
            )

            # 更新 endpoint 权重
            if abs(new_weight - endpoint.weight) > 1:
                endpoint.weight = new_weight
                # 持久化到配置
                self._save_endpoint_weight(endpoint)

    def _print_check_summary(self, results: List[ConversationalHealthCheck]):
        """打印检查摘要"""

        print(f"\n📊 健康检查完成:")

        for check in results:
            result_icon = {
                HealthCheckResult.SUCCESS: '✅',
                HealthCheckResult.FAILURE: '❌',
                HealthCheckResult.TIMEOUT: '⏱️',
                HealthCheckResult.RATE_LIMITED: '🚫',
                HealthCheckResult.INVALID_KEY: '🔑'
            }.get(check.result, '❓')

            metrics = self.performance_metrics.get(check.endpoint_id)

            if check.result == HealthCheckResult.SUCCESS:
                print(
                    f"  {result_icon} {check.endpoint_id}: "
                    f"{check.response_time_ms:.0f}ms "
                    f"(评分: {check.response_score:.0f}/100, "
                    f"权重: {metrics and self._get_endpoint_weight(check.endpoint_id)})"
                )
            else:
                print(
                    f"  {result_icon} {check.endpoint_id}: "
                    f"{check.result.value} - {check.error_message}"
                )
```

---

## 🖥️ CLI 命令扩展

```python
# fastcc/cli.py

@cli.group()
def health():
    """健康检测管理"""
    pass

@health.command('test')
@click.argument('endpoint_id', required=False)
@click.option('--verbose', '-v', is_flag=True, help='显示详细信息')
def health_test(endpoint_id, verbose):
    """执行对话测试

    示例:
        qcc health test                  # 测试所有 endpoint
        qcc health test endpoint-1       # 测试指定 endpoint
        qcc health test -v               # 显示详细信息
    """
    try:
        import asyncio

        checker = ConversationalHealthChecker()
        config_manager = ConfigManager()

        # 获取要测试的 endpoint
        if endpoint_id:
            endpoints = [config_manager.get_endpoint(endpoint_id)]
        else:
            endpoints = config_manager.get_all_endpoints()

        if not endpoints:
            print_status("没有可测试的 endpoint", "warning")
            return

        print_header("对话测试")
        print(f"测试 {len(endpoints)} 个 endpoint...\n")

        # 执行测试
        results = asyncio.run(checker.check_all_endpoints(endpoints))

        # 显示结果
        for check in results:
            result_icon = {
                HealthCheckResult.SUCCESS: '✅',
                HealthCheckResult.FAILURE: '❌',
                HealthCheckResult.TIMEOUT: '⏱️',
                HealthCheckResult.RATE_LIMITED: '🚫',
            }.get(check.result, '❓')

            print(f"{result_icon} {check.endpoint_id}")
            print(f"   测试消息: {check.test_message}")

            if check.result == HealthCheckResult.SUCCESS:
                print(f"   响应时间: {check.response_time_ms:.0f}ms")
                print(f"   响应内容: {check.response_content[:50]}...")
                print(f"   质量评分: {check.response_score:.0f}/100")
                print(f"   响应有效: {'是' if check.response_valid else '否'}")

                if verbose:
                    print(f"   完整响应: {check.response_content}")
                    print(f"   使用 Token: {check.tokens_used}")
                    print(f"   使用模型: {check.model_used}")
            else:
                print(f"   错误: {check.error_message}")

            print()

    except Exception as e:
        print_status(f"测试失败: {e}", "error")

@health.command('metrics')
@click.argument('endpoint_id', required=False)
def health_metrics(endpoint_id):
    """查看性能指标

    示例:
        qcc health metrics               # 查看所有 endpoint 指标
        qcc health metrics endpoint-1    # 查看指定 endpoint 指标
    """
    try:
        # 加载性能指标
        monitor = HealthMonitor()

        if endpoint_id:
            metrics = monitor.performance_metrics.get(endpoint_id)
            if not metrics:
                print_status(f"没有 '{endpoint_id}' 的性能数据", "warning")
                return

            _print_detailed_metrics(metrics)
        else:
            print_header("性能指标概览")

            for metrics in monitor.performance_metrics.values():
                _print_summary_metrics(metrics)

    except Exception as e:
        print_status(f"查看指标失败: {e}", "error")

def _print_detailed_metrics(metrics: PerformanceMetrics):
    """打印详细指标"""
    print_header(f"Endpoint: {metrics.endpoint_id}")

    print(f"📊 检查统计:")
    print(f"  总检查次数: {metrics.total_checks}")
    print(f"  成功次数: {metrics.successful_checks}")
    print(f"  失败次数: {metrics.failed_checks}")
    print(f"  超时次数: {metrics.timeout_checks}")
    print(f"  限流次数: {metrics.rate_limited_checks}")
    print()

    print(f"📈 性能指标:")
    print(f"  成功率: {metrics.success_rate:.1f}%")
    print(f"  近期成功率: {metrics.recent_success_rate:.1f}%")
    print(f"  平均响应时间: {metrics.avg_response_time:.0f}ms")
    print(f"  P95 响应时间: {metrics.p95_response_time:.0f}ms")
    print(f"  稳定性评分: {metrics.stability_score:.1f}/100")
    print()

    print(f"🔄 连续状态:")
    print(f"  连续成功: {metrics.consecutive_successes} 次")
    print(f"  连续失败: {metrics.consecutive_failures} 次")
    print()

    print(f"⏰ 最后更新: {metrics.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

def _print_summary_metrics(metrics: PerformanceMetrics):
    """打印简要指标"""
    status_icon = '✅' if metrics.recent_success_rate > 80 else '⚠️' if metrics.recent_success_rate > 50 else '❌'

    print(f"\n{status_icon} {metrics.endpoint_id}")
    print(f"   成功率: {metrics.recent_success_rate:.1f}% | "
          f"响应: {metrics.avg_response_time:.0f}ms | "
          f"稳定性: {metrics.stability_score:.0f}/100")
```

---

## 📚 完整使用示例

### 场景 1: 首次启动并测试

```bash
# 1. 创建配置并添加多个 endpoint
qcc add production
qcc endpoint add production -f work
qcc endpoint add production -f personal
qcc endpoint add production -f backup

# 2. 执行初始测试
qcc health test
# 输出:
# 🔍 对话测试
# 测试 3 个 endpoint...
#
# ✅ endpoint-1
#    测试消息: 收到消息请回复 1
#    响应时间: 320ms
#    响应内容: 1
#    质量评分: 95/100
#    响应有效: 是
#
# ✅ endpoint-2
#    测试消息: 收到消息请回复 1
#    响应时间: 850ms
#    响应内容: 收到，回复1
#    质量评分: 75/100
#    响应有效: 是
#
# ❌ endpoint-3
#    测试消息: 收到消息请回复 1
#    错误: 请求超时

# 3. 查看性能指标
qcc health metrics
# 输出:
# ✅ endpoint-1
#    成功率: 100.0% | 响应: 320ms | 稳定性: 95/100
#
# ⚠️  endpoint-2
#    成功率: 100.0% | 响应: 850ms | 稳定性: 70/100
#
# ❌ endpoint-3
#    成功率: 0.0% | 响应: 0ms | 稳定性: 0/100
```

### 场景 2: 启动代理，自动监控和调整权重

```bash
# 启动代理服务（自动启动健康监控）
qcc proxy start
# ✓ 代理服务器已启动: http://127.0.0.1:7860
# ✓ 智能健康监控已启动
#   - 检查间隔: 60秒
#   - 检测方式: 对话测试
#   - 动态权重: 已启用

# 60 秒后，自动执行第一次健康检查:
# 🔍 开始健康检查 (3 个 endpoint)
#
# 📊 健康检查完成:
#   ✅ endpoint-1: 310ms (评分: 95/100, 权重: 100)
#   ✅ endpoint-2: 920ms (评分: 70/100, 权重: 100)
#   ❌ endpoint-3: timeout - 请求超时

# 120 秒后，第二次健康检查，开始调整权重:
# 🔍 开始健康检查 (3 个 endpoint)
#
# 📊 权重调整: endpoint-1
#    当前权重: 100.00
#    新权重: 115.40 (+15.40, +15.4%)
#    原因:
#      - 平均响应: 315ms
#      - 成功率: 100.0%
#      - 稳定性: 95.0
#      - 连续失败: 0
#
# 📊 权重调整: endpoint-2
#    当前权重: 100.00
#    新权重: 85.60 (-14.40, -14.4%)
#    原因:
#      - 平均响应: 885ms
#      - 成功率: 100.0%
#      - 稳定性: 72.0
#      - 连续失败: 0
#
# 📊 权重调整: endpoint-3
#    当前权重: 100.00
#    新权重: 20.00 (-80.00, -80.0%)
#    原因:
#      - 平均响应: 0ms
#      - 成功率: 0.0%
#      - 稳定性: 0.0
#      - 连续失败: 2
#
# 📊 健康检查完成:
#   ✅ endpoint-1: 305ms (评分: 96/100, 权重: 115.4)
#   ✅ endpoint-2: 870ms (评分: 72/100, 权重: 85.6)
#   ❌ endpoint-3: timeout - 请求超时
```

### 场景 3: 查看详细性能报告

```bash
qcc health metrics endpoint-1
# 输出:
#
# ━━━━━━━━━━━━━━━━ Endpoint: endpoint-1 ━━━━━━━━━━━━━━━━
#
# 📊 检查统计:
#   总检查次数: 10
#   成功次数: 10
#   失败次数: 0
#   超时次数: 0
#   限流次数: 0
#
# 📈 性能指标:
#   成功率: 100.0%
#   近期成功率: 100.0%
#   平均响应时间: 315ms
#   P95 响应时间: 350ms
#   稳定性评分: 95.0/100
#
# 🔄 连续状态:
#   连续成功: 10 次
#   连续失败: 0 次
#
# ⏰ 最后更新: 2025-10-16 14:35:00
```

---

## 🧪 测试用例

```python
# tests/test_conversational_health_check.py

import pytest
import asyncio
from fastcc.proxy.conversational_checker import ConversationalHealthChecker
from fastcc.proxy.performance_metrics import PerformanceMetrics
from fastcc.proxy.weight_adjuster import DynamicWeightAdjuster

@pytest.mark.asyncio
async def test_health_check_success():
    """测试成功的健康检查"""
    checker = ConversationalHealthChecker()
    endpoint = create_test_endpoint()

    result = await checker.check_endpoint(endpoint)

    assert result.result == HealthCheckResult.SUCCESS
    assert result.response_time_ms > 0
    assert result.response_valid
    assert result.response_score > 0

@pytest.mark.asyncio
async def test_health_check_timeout():
    """测试超时的健康检查"""
    checker = ConversationalHealthChecker()
    checker.timeout = 1  # 设置很短的超时
    endpoint = create_slow_endpoint()

    result = await checker.check_endpoint(endpoint)

    assert result.result == HealthCheckResult.TIMEOUT

def test_performance_metrics_calculation():
    """测试性能指标计算"""
    metrics = PerformanceMetrics("test-endpoint")

    # 添加10次成功检查
    for i in range(10):
        check = create_success_check(response_time=300 + i * 10)
        metrics.add_check_result(check)

    assert metrics.success_rate == 100.0
    assert metrics.avg_response_time >= 300
    assert metrics.stability_score > 80

def test_weight_adjustment():
    """测试权重调整"""
    adjuster = DynamicWeightAdjuster()
    metrics = create_good_metrics()  # 表现良好的指标

    endpoint = Endpoint(
        base_url="https://test.com",
        api_key="test",
        weight=100
    )

    new_weight = adjuster.adjust_endpoint_weight(endpoint, metrics)

    # 表现好的 endpoint 权重应该增加
    assert new_weight > 100

def test_weight_penalty_for_failures():
    """测试失败的权重惩罚"""
    adjuster = DynamicWeightAdjuster()
    metrics = create_failing_metrics()  # 失败的指标

    endpoint = Endpoint(
        base_url="https://test.com",
        api_key="test",
        weight=100
    )

    new_weight = adjuster.adjust_endpoint_weight(endpoint, metrics)

    # 失败的 endpoint 权重应该大幅降低
    assert new_weight < 50
```

---

## 📊 性能优化建议

### 1. 并发检测

```python
# 使用 asyncio.gather 并发检测所有 endpoint
results = await asyncio.gather(
    *[checker.check_endpoint(ep) for ep in endpoints],
    return_exceptions=True
)
```

### 2. 缓存机制

```python
# 缓存最近的检查结果，避免频繁检测同一个 endpoint
cache_ttl = 30  # 30 秒缓存
```

### 3. 采样检测

```python
# 对于大量 endpoint，可以采样检测
if len(endpoints) > 10:
    import random
    endpoints_to_check = random.sample(endpoints, 10)
```

---

## 🎯 总结

通过**对话测试**实现智能健康检测:

1. **真实场景测试** - 发送实际的 AI 请求，而不是简单 ping
2. **多维度评估** - 响应时间、成功率、稳定性、响应质量
3. **动态权重调整** - 根据实际表现自动调整负载均衡权重
4. **智能故障检测** - 准确识别超时、限流、无效 Key 等问题
5. **持续监控** - 后台定时检测，实时调整

这种方式比传统的网络 ping 测试更能反映真实使用情况！

---

**文档版本**: v1.0
**最后更新**: 2025-10-16
**作者**: QCC Development Team
