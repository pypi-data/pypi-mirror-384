# QCC Claude Code 代理服务开发计划

## 📋 项目概述

为 QCC 添加 Claude Code 代理服务功能，实现多 API Key 配置管理、主次配置策略、后台健康检测及自动故障转移机制。

**版本**: v0.4.0
**创建日期**: 2025-10-16
**预计完成时间**: 2-3 周

---

## 🎯 核心功能需求

### 1. Claude Code 代理服务

**目标**: 提供本地代理服务器,拦截 Claude Code 的 API 请求并转发到配置的后端

#### 功能点:
- ✅ 启动本地 HTTP/HTTPS 代理服务器 (默认端口: 7860)
- ✅ 拦截 Claude Code 的 Anthropic API 调用
- ✅ 实现请求转发和响应处理
- ✅ 支持流式响应 (SSE - Server-Sent Events)
- ✅ 请求/响应日志记录
- ✅ 透明代理模式 (可选)

#### 技术方案:
```python
# 代理服务架构
fastcc/
├── proxy/
│   ├── __init__.py
│   ├── server.py           # 代理服务器主逻辑
│   ├── handler.py          # 请求处理器
│   ├── forwarder.py        # 请求转发器
│   └── middleware.py       # 中间件 (日志、认证等)
```

#### CLI 命令:
```bash
qcc proxy start              # 启动代理服务
qcc proxy stop               # 停止代理服务
qcc proxy status             # 查看代理状态
qcc proxy logs               # 查看代理日志
qcc proxy restart            # 重启代理服务
```

---

### 2. 多 API Key 配置管理

**目标**: 支持用户为每个配置档案添加多个 API Key 和 Base URL

#### 数据结构设计:
```json
{
  "name": "my-config",
  "description": "主配置",
  "priority": "primary",
  "endpoints": [
    {
      "id": "endpoint-1",
      "base_url": "https://api.anthropic.com",
      "api_key": "sk-ant-xxxxx",
      "weight": 100,
      "enabled": true,
      "priority": 1,
      "max_failures": 3,
      "timeout": 30,
      "metadata": {
        "provider": "anthropic-official",
        "region": "us-east-1",
        "rate_limit": 60
      }
    },
    {
      "id": "endpoint-2",
      "base_url": "https://backup.api.com",
      "api_key": "sk-backup-xxxxx",
      "weight": 50,
      "enabled": true,
      "priority": 2,
      "max_failures": 3,
      "timeout": 30
    }
  ],
  "load_balancing": {
    "strategy": "weighted",  # weighted, round-robin, failover
    "health_check_interval": 60
  }
}
```

#### 功能点:
- ✅ 为配置添加多个 endpoint (API Key + Base URL 组合)
- ✅ **从现有配置选择复用** - 快速复用已有的 base_url 和 api_key
- ✅ 支持 endpoint 的启用/禁用
- ✅ 支持设置优先级 (priority)
- ✅ 支持设置权重 (weight) 用于负载均衡
- ✅ 支持 endpoint 元数据 (厂商、区域等)

#### 添加 Endpoint 交互流程:
```
qcc endpoint add <config-name>

1️⃣ 选择添加方式:
   [ ] 从现有配置复用 (推荐)
   [ ] 手动输入新配置
   [ ] 从厂商快速配置 (qcc fc)

2️⃣ 如果选择"从现有配置复用":
   - 显示所有可用的配置列表
   - 用户选择要复用的配置
   - 自动提取 base_url 和 api_key
   - 询问是否修改 (可选)
   - 设置权重、优先级等参数

3️⃣ 如果选择"手动输入新配置":
   - 输入 base_url
   - 输入 api_key
   - 设置权重、优先级等参数

4️⃣ 确认并保存
```

#### CLI 命令扩展:
```bash
qcc endpoint add <config-name>           # 为配置添加 endpoint
qcc endpoint list <config-name>          # 查看配置的所有 endpoint
qcc endpoint remove <config-name> <id>   # 删除 endpoint
qcc endpoint enable <config-name> <id>   # 启用 endpoint
qcc endpoint disable <config-name> <id>  # 禁用 endpoint
qcc endpoint test <config-name> <id>     # 测试 endpoint 连通性
```

---

### 3. 主次配置策略

**目标**: 实现配置档案的主次优先级管理和智能切换

#### 配置层级:
```
1. Primary Configs (主配置组)
   - 优先使用
   - 高可用性要求
   - 多个 endpoint 负载均衡

2. Secondary Configs (次配置组)
   - 备份配置
   - 主配置全部失败时启用
   - 按优先级依次尝试

3. Fallback Configs (兜底配置)
   - 最后的保障
   - 只读或限制功能
```

#### 数据结构:
```json
{
  "profile_groups": {
    "primary": ["config-1", "config-2"],
    "secondary": ["config-3", "config-4"],
    "fallback": ["config-5"]
  },
  "switching_policy": {
    "auto_switch": true,
    "switch_threshold": 3,
    "cooldown_period": 300,
    "fallback_enabled": true
  }
}
```

#### 功能点:
- ✅ 设置配置为主配置/次配置/兜底配置
- ✅ 配置组管理
- ✅ **自动故障转移** - 主配置失败时自动切换到次配置
- ✅ **自动恢复** - 主配置恢复后自动切回（可选）
- ✅ **智能切换策略** - 故障阈值、冷却期、频率限制
- ✅ 切换历史记录和事件追踪
- ✅ 手动切换和强制恢复
- ✅ 实时监控和告警通知

#### CLI 命令:
```bash
qcc priority set <name> primary|secondary|fallback   # 设置配置优先级
qcc priority list                                     # 查看优先级配置
qcc priority switch <to-config>                       # 手动切换配置
qcc priority policy [options]                         # 配置故障转移策略
qcc priority history                                  # 查看故障转移历史

# 策略配置选项:
qcc priority policy --auto-failover                   # 启用自动故障转移
qcc priority policy --auto-recovery                   # 启用自动恢复
qcc priority policy --failure-threshold 3             # 设置故障阈值
qcc priority policy --cooldown 300                    # 设置冷却期（秒）
```

---

### 4. 后台健康检测机制

**目标**: 实现后台定时健康检测,自动发现和标记失败的 endpoint

#### 检测策略:
```python
class HealthChecker:
    """健康检测器"""

    def __init__(self):
        self.check_interval = 60  # 检测间隔 (秒)
        self.timeout = 10         # 超时时间
        self.retry_count = 3      # 重试次数

    async def check_endpoint(self, endpoint):
        """检测单个 endpoint"""
        # 1. 连接性测试
        # 2. API 测试 (轻量级请求)
        # 3. 响应时间测试
        # 4. 更新健康状态
        pass

    async def check_all_endpoints(self):
        """并发检测所有 endpoint"""
        pass
```

#### 健康状态模型:
```json
{
  "endpoint_id": "endpoint-1",
  "health_status": {
    "status": "healthy",  # healthy, degraded, unhealthy
    "last_check": "2025-10-16T12:00:00Z",
    "consecutive_failures": 0,
    "total_requests": 1000,
    "failed_requests": 5,
    "success_rate": 99.5,
    "avg_response_time": 250,
    "last_error": null,
    "last_success": "2025-10-16T11:59:00Z"
  }
}
```

#### 功能点:
- ✅ 定时健康检测 (可配置间隔)
- ✅ 多层次检测 (连接、API、性能)
- ✅ 健康状态持久化
- ✅ 健康度评分系统
- ✅ 检测结果通知 (可选)

#### CLI 命令:
```bash
qcc health check                    # 立即执行健康检测
qcc health status                   # 查看所有 endpoint 健康状态
qcc health history <endpoint-id>    # 查看历史健康记录
qcc health config                   # 配置健康检测参数
```

---

### 5. 故障转移队列

**目标**: 实现失败请求的队列管理和自动重试机制

#### 队列架构:
```python
class FailureQueue:
    """失败队列管理器"""

    def __init__(self):
        self.max_queue_size = 1000
        self.retry_strategies = {
            'exponential_backoff': ExponentialBackoffStrategy,
            'fixed_interval': FixedIntervalStrategy,
            'immediate': ImmediateRetryStrategy
        }

    async def enqueue(self, request, reason):
        """入队失败请求"""
        pass

    async def retry_failed_requests(self):
        """重试队列中的请求"""
        pass
```

#### 队列数据结构:
```json
{
  "queue_id": "queue-20251016",
  "requests": [
    {
      "request_id": "req-12345",
      "original_endpoint": "endpoint-1",
      "request_data": {...},
      "failure_reason": "timeout",
      "enqueued_at": "2025-10-16T12:00:00Z",
      "retry_count": 2,
      "max_retries": 5,
      "next_retry_at": "2025-10-16T12:05:00Z",
      "status": "pending"  # pending, retrying, success, failed
    }
  ]
}
```

#### 重试策略:
1. **指数退避** (Exponential Backoff)
   - 首次重试: 5秒
   - 第二次: 10秒
   - 第三次: 20秒
   - 最大等待: 300秒

2. **固定间隔** (Fixed Interval)
   - 每次重试间隔固定时间

3. **立即重试** (Immediate)
   - 失败后立即重试
   - 适用于瞬时故障

#### 功能点:
- ✅ 失败请求自动入队
- ✅ 多种重试策略
- ✅ 队列持久化
- ✅ 优先级队列 (重要请求优先)
- ✅ 队列监控和告警
- ✅ 手动重试/清空队列

#### CLI 命令:
```bash
qcc queue status                     # 查看队列状态
qcc queue list                       # 列出队列中的请求
qcc queue retry <request-id>         # 手动重试某个请求
qcc queue retry-all                  # 重试所有失败请求
qcc queue clear                      # 清空队列
qcc queue config                     # 配置重试策略
```

---

### 6. 终端配置管理

**目标**: 所有功能都可通过终端命令配置

#### 配置系统架构:
```python
class ConfigurationManager:
    """统一配置管理器"""

    def __init__(self):
        self.config_schema = {...}
        self.validators = {...}
        self.config_path = "~/.qcc/config.json"

    def get(self, key, default=None):
        """获取配置"""
        pass

    def set(self, key, value):
        """设置配置"""
        pass

    def validate(self, key, value):
        """验证配置"""
        pass
```

#### 配置项分类:
1. **代理配置** (`proxy.*`)
   - `proxy.host`: 代理监听地址
   - `proxy.port`: 代理端口
   - `proxy.ssl_enabled`: 是否启用 HTTPS
   - `proxy.log_level`: 日志级别

2. **健康检测配置** (`health.*`)
   - `health.check_interval`: 检测间隔
   - `health.timeout`: 超时时间
   - `health.retry_count`: 重试次数
   - `health.alert_enabled`: 是否启用告警

3. **队列配置** (`queue.*`)
   - `queue.max_size`: 队列最大长度
   - `queue.retry_strategy`: 重试策略
   - `queue.max_retries`: 最大重试次数
   - `queue.persistence_enabled`: 是否持久化

4. **负载均衡配置** (`loadbalancer.*`)
   - `loadbalancer.strategy`: 负载均衡策略
   - `loadbalancer.health_aware`: 是否健康感知
   - `loadbalancer.sticky_session`: 会话保持

#### CLI 命令:
```bash
qcc config get <key>                 # 获取配置项
qcc config set <key> <value>         # 设置配置项
qcc config list                      # 列出所有配置
qcc config reset [key]               # 重置配置 (全部或指定项)
qcc config export <file>             # 导出配置
qcc config import <file>             # 导入配置
qcc config validate                  # 验证配置
```

---

## 🏗️ 技术架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Code Client                    │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────┐
│                   QCC Proxy Server                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │          Request Handler & Router                │  │
│  └─────────────────────┬────────────────────────────┘  │
│                        │                                 │
│  ┌─────────────────────┴────────────────────────────┐  │
│  │          Load Balancer & Endpoint Selector       │  │
│  └─────────────────────┬────────────────────────────┘  │
│                        │                                 │
│  ┌─────────────────────┴────────────────────────────┐  │
│  │               Health Monitor                     │  │
│  └──────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Primary    │ │  Secondary   │ │   Fallback   │
│   Endpoint   │ │   Endpoint   │ │   Endpoint   │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        ↓               ↓               ↓
┌─────────────────────────────────────────────────────────┐
│              Anthropic API Providers                     │
└─────────────────────────────────────────────────────────┘
```

### 核心模块说明

#### 1. Proxy Server 模块
```python
# fastcc/proxy/server.py
from aiohttp import web
import asyncio

class ProxyServer:
    """代理服务器"""

    def __init__(self, host='127.0.0.1', port=7860):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        """设置路由"""
        self.app.router.add_route('*', '/{path:.*}', self.handle_request)

    async def handle_request(self, request):
        """处理请求"""
        # 1. 解析请求
        # 2. 选择 endpoint
        # 3. 转发请求
        # 4. 返回响应
        pass

    async def start(self):
        """启动服务器"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
```

#### 2. Load Balancer 模块
```python
# fastcc/proxy/load_balancer.py

class LoadBalancer:
    """负载均衡器"""

    strategies = {
        'weighted': WeightedStrategy,
        'round_robin': RoundRobinStrategy,
        'least_connections': LeastConnectionsStrategy,
        'failover': FailoverStrategy
    }

    def __init__(self, strategy='weighted'):
        self.strategy = self.strategies[strategy]()

    async def select_endpoint(self, endpoints):
        """选择 endpoint"""
        # 1. 过滤健康的 endpoint
        # 2. 应用负载均衡策略
        # 3. 返回最优 endpoint
        pass
```

#### 3. Health Monitor 模块
```python
# fastcc/proxy/health_monitor.py
import asyncio
from datetime import datetime

class HealthMonitor:
    """健康监控器"""

    def __init__(self):
        self.endpoints = {}
        self.check_interval = 60
        self.running = False

    async def start(self):
        """启动监控"""
        self.running = True
        while self.running:
            await self.check_all_endpoints()
            await asyncio.sleep(self.check_interval)

    async def check_endpoint(self, endpoint):
        """检测单个 endpoint"""
        try:
            # 发送测试请求
            result = await self.send_health_check(endpoint)
            self.update_health_status(endpoint, 'healthy', result)
        except Exception as e:
            self.update_health_status(endpoint, 'unhealthy', str(e))
```

#### 4. Failure Queue 模块
```python
# fastcc/proxy/failure_queue.py
from collections import deque
import asyncio

class FailureQueue:
    """失败队列"""

    def __init__(self, max_size=1000):
        self.queue = deque(maxlen=max_size)
        self.retry_strategy = ExponentialBackoffStrategy()

    async def enqueue(self, request, reason):
        """入队"""
        retry_item = {
            'request': request,
            'reason': reason,
            'enqueued_at': datetime.now(),
            'retry_count': 0
        }
        self.queue.append(retry_item)

    async def process_queue(self):
        """处理队列"""
        while True:
            if self.queue:
                item = self.queue.popleft()
                await self.retry_request(item)
            await asyncio.sleep(1)
```

#### 5. 异步运行时管理器 (新增)
```python
# fastcc/proxy/runtime_manager.py
import asyncio
from typing import List, Dict, Any
import signal

class AsyncRuntimeManager:
    """统一管理所有异步任务的运行时

    解决问题:
    - 统一事件循环管理
    - 优雅的启动和关闭
    - 任务生命周期管理
    - 异常处理和日志
    """

    def __init__(self):
        self.loop = None
        self.tasks: List[asyncio.Task] = []
        self.services: Dict[str, Any] = {}
        self.running = False

    async def start_all(self):
        """启动所有服务"""
        self.running = True

        # 启动代理服务器
        from fastcc.proxy.server import ProxyServer
        proxy_server = ProxyServer()
        self.services['proxy'] = proxy_server
        self.tasks.append(asyncio.create_task(proxy_server.start()))

        # 启动健康监控
        from fastcc.proxy.health_monitor import HealthMonitor
        health_monitor = HealthMonitor()
        self.services['health'] = health_monitor
        self.tasks.append(asyncio.create_task(health_monitor.start()))

        # 启动故障转移管理器
        from fastcc.proxy.failover_manager import FailoverManager
        failover_manager = FailoverManager()
        self.services['failover'] = failover_manager
        self.tasks.append(asyncio.create_task(failover_manager.start()))

        # 启动失败队列处理器
        from fastcc.proxy.failure_queue import FailureQueue
        failure_queue = FailureQueue()
        self.services['queue'] = failure_queue
        self.tasks.append(asyncio.create_task(failure_queue.process_queue()))

        print("✓ 所有服务已启动")

        # 等待所有任务完成或被取消
        await asyncio.gather(*self.tasks, return_exceptions=True)

    async def stop_all(self):
        """停止所有服务"""
        self.running = False

        print("\n正在停止所有服务...")

        # 先停止接收新请求
        for name, service in self.services.items():
            if hasattr(service, 'stop'):
                await service.stop()
                print(f"✓ {name} 已停止")

        # 取消所有任务
        for task in self.tasks:
            task.cancel()

        # 等待所有任务清理完成
        await asyncio.gather(*self.tasks, return_exceptions=True)

        print("✓ 所有服务已停止")

    def run(self):
        """主运行方法"""
        # 设置信号处理
        signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(self.stop_all()))
        signal.signal(signal.SIGTERM, lambda s, f: asyncio.create_task(self.stop_all()))

        try:
            asyncio.run(self.start_all())
        except KeyboardInterrupt:
            print("\n收到中断信号")
        finally:
            print("运行时已清理")
```

#### 6. 并发控制器 (新增)
```python
# fastcc/proxy/concurrency_control.py
import asyncio
from collections import deque
from datetime import datetime, timedelta

class ConcurrencyController:
    """并发请求控制器

    解决问题:
    - 限制最大并发请求数
    - 请求排队和优先级
    - 速率限制
    - 资源保护
    """

    def __init__(self, max_concurrent=100, rate_limit=None):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # 速率限制 (requests per second)
        self.rate_limit = rate_limit
        self.request_times = deque(maxlen=1000)

        # 统计
        self.total_requests = 0
        self.active_requests = 0
        self.queued_requests = 0
        self.rejected_requests = 0

    async def acquire(self, priority=0):
        """获取执行许可

        Args:
            priority: 请求优先级 (数字越大优先级越高)
        """
        self.queued_requests += 1

        try:
            # 检查速率限制
            if self.rate_limit:
                await self._check_rate_limit()

            # 获取信号量
            await self.semaphore.acquire()

            self.active_requests += 1
            self.total_requests += 1
            self.queued_requests -= 1
            self.request_times.append(datetime.now())

        except Exception as e:
            self.queued_requests -= 1
            self.rejected_requests += 1
            raise

    def release(self):
        """释放执行许可"""
        self.semaphore.release()
        self.active_requests -= 1

    async def _check_rate_limit(self):
        """检查速率限制"""
        if not self.rate_limit:
            return

        now = datetime.now()
        one_second_ago = now - timedelta(seconds=1)

        # 清理超过1秒的记录
        while self.request_times and self.request_times[0] < one_second_ago:
            self.request_times.popleft()

        # 如果超过速率限制,等待
        if len(self.request_times) >= self.rate_limit:
            oldest = self.request_times[0]
            wait_time = 1 - (now - oldest).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

    async def __aenter__(self):
        """上下文管理器入口"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release()

    def get_stats(self):
        """获取统计信息"""
        return {
            'max_concurrent': self.max_concurrent,
            'active_requests': self.active_requests,
            'queued_requests': self.queued_requests,
            'total_requests': self.total_requests,
            'rejected_requests': self.rejected_requests,
            'current_rps': len(self.request_times)
        }

# 使用示例
async def handle_request_with_concurrency_control(request):
    """带并发控制的请求处理"""
    controller = ConcurrencyController(max_concurrent=100, rate_limit=50)

    async with controller:
        # 处理请求
        response = await process_request(request)
        return response
```

---

## 📦 依赖包更新

需要在 `pyproject.toml` 中添加以下依赖:

```toml
# Python 版本要求
requires-python = ">=3.9"

dependencies = [
    # 现有依赖
    "click>=8.0.0",
    "requests>=2.25.0",
    "cryptography>=3.4.0",
    "rich>=12.0.0",
    "prompt_toolkit>=3.0.0",

    # 新增依赖
    "aiohttp>=3.8.0",          # 异步 HTTP 客户端/服务器
    "aiohttp-cors>=0.7.0",     # CORS 支持
    # 注意: asyncio 是 Python 标准库,无需添加为依赖
    "pydantic>=2.0.0",         # 数据验证
    "tenacity>=8.0.0",         # 重试机制
    "psutil>=5.9.0",           # 系统进程管理
]
```

**⚠️ 重要说明**:
- 移除了 `asyncio` 和 `schedule` 依赖(asyncio 是标准库,schedule 功能由 asyncio 实现)
- Python 版本要求 >= 3.9(支持现代异步特性)
- 使用 asyncio 内置的定时任务功能,不需要额外的调度库

---

## 🗂️ 文件结构

```
fastcc/
├── __init__.py
├── cli.py                     # CLI 主入口 (扩展)
├── proxy/                     # 🆕 代理服务模块
│   ├── __init__.py
│   ├── server.py              # 代理服务器
│   ├── handler.py             # 请求处理器
│   ├── forwarder.py           # 请求转发器
│   ├── middleware.py          # 中间件
│   ├── load_balancer.py       # 负载均衡器
│   ├── health_monitor.py      # 健康监控器
│   ├── failure_queue.py       # 失败队列
│   ├── failover_manager.py    # 🆕 故障转移管理器
│   ├── runtime_manager.py     # 🆕 异步运行时管理器
│   ├── concurrency_control.py # 🆕 并发控制器
│   └── strategies.py          # 各种策略实现
├── core/
│   ├── __init__.py
│   ├── config.py              # 配置管理 (扩展)
│   ├── endpoint.py            # 🆕 Endpoint 模型
│   ├── priority.py            # 🆕 优先级管理
│   └── priority_manager.py    # 🆕 优先级管理器
├── storage/
│   └── ... (现有文件)
├── providers/
│   └── ... (现有文件)
├── auth/
│   └── ... (现有文件)
└── utils/
    ├── __init__.py
    ├── crypto.py
    ├── ui.py
    ├── logger.py              # 🆕 日志工具
    └── validator.py           # 🆕 验证工具

tests/
├── __init__.py
├── test_proxy_server.py       # 🆕 代理服务器测试
├── test_load_balancer.py      # 🆕 负载均衡测试
├── test_health_monitor.py     # 🆕 健康监控测试
├── test_failure_queue.py      # 🆕 失败队列测试
├── test_failover.py           # 🆕 故障转移测试
├── test_endpoint.py           # 🆕 Endpoint 测试
├── test_runtime_manager.py    # 🆕 运行时管理器测试
└── test_concurrency.py        # 🆕 并发控制测试

tasks/
├── claude-code-proxy-development-plan.md        # 本文档
├── endpoint-reuse-implementation.md             # Endpoint 复用实现
├── auto-failover-mechanism.md                   # 自动故障转移机制
├── intelligent-health-check.md                  # 智能健康检测
├── concurrency-control-design.md                # 🆕 并发控制设计
├── config-validation-rollback.md                # 🆕 配置校验和回滚
└── deployment-troubleshooting-guide.md          # 🆕 部署和故障排查
```

---

## 📅 开发里程碑

### 第一阶段: 基础架构 (Week 1)

**目标**: 搭建代理服务基础架构

- [ ] 1.1 创建代理服务器基础框架
- [ ] 1.2 实现基本的请求拦截和转发
- [ ] 1.3 添加 Endpoint 数据模型
- [ ] 1.4 扩展配置管理支持多 endpoint
- [ ] 1.5 编写基础单元测试

**交付物**:
- 可运行的基础代理服务器
- 支持单个 endpoint 的请求转发
- Endpoint 数据模型和 CRUD 操作

---

### 第二阶段: 负载均衡与健康检测 (Week 2)

**目标**: 实现负载均衡和健康检测功能

- [ ] 2.1 实现负载均衡器框架
- [ ] 2.2 实现多种负载均衡策略
  - [ ] 加权轮询 (Weighted Round Robin)
  - [ ] 最少连接 (Least Connections)
  - [ ] 故障转移 (Failover)
- [ ] 2.3 实现健康监控器
- [ ] 2.4 实现健康检测逻辑
- [ ] 2.5 健康状态持久化
- [ ] 2.6 添加相关 CLI 命令
- [ ] 2.7 编写测试用例

**交付物**:
- 完整的负载均衡系统
- 自动健康检测机制
- 健康状态查看和管理命令

---

### 第三阶段: 故障转移与队列管理 (Week 2-3)

**目标**: 实现故障转移和失败请求队列

- [ ] 3.1 设计失败队列数据结构
- [ ] 3.2 实现失败队列管理器
- [ ] 3.3 实现多种重试策略
  - [ ] 指数退避
  - [ ] 固定间隔
  - [ ] 立即重试
- [ ] 3.4 队列持久化
- [ ] 3.5 添加队列管理 CLI 命令
- [ ] 3.6 编写测试用例

**交付物**:
- 完整的失败队列系统
- 自动重试机制
- 队列管理命令

---

### 第四阶段: 配置管理与优化 (Week 3)

**目标**: 完善配置管理和系统优化

- [ ] 4.1 实现主次配置优先级管理
- [ ] 4.2 实现配置组管理
- [ ] 4.3 完善终端配置命令
- [ ] 4.4 性能优化
  - [ ] 连接池管理
  - [ ] 请求缓存
  - [ ] 并发控制
- [ ] 4.5 添加监控和统计
- [ ] 4.6 完善文档
- [ ] 4.7 全面测试

**交付物**:
- 完整的配置管理系统
- 性能优化的代理服务
- 完善的文档和测试

---

## 🧪 测试计划

### 测试规范 (遵循 CLAUDE.md)

**测试流程**:
1. 单元测试放到 `tests/` 目录下
2. 必须使用 `virtualenv` 创建 `venv` 虚拟环境
3. 先测试再发布
4. **测试时一定使用 uvx 进行测试**

### 单元测试

```python
# tests/test_proxy_server.py
def test_proxy_server_start()
def test_proxy_server_request_handling()
def test_proxy_server_response_forwarding()

# tests/test_load_balancer.py
def test_weighted_strategy()
def test_round_robin_strategy()
def test_failover_strategy()
def test_health_aware_selection()

# tests/test_health_monitor.py
def test_health_check_execution()
def test_health_status_update()
def test_unhealthy_endpoint_detection()

# tests/test_failure_queue.py
def test_enqueue_failed_request()
def test_retry_strategy_exponential()
def test_retry_strategy_fixed()
def test_queue_persistence()

# tests/test_endpoint.py
def test_endpoint_creation()
def test_endpoint_validation()
def test_endpoint_priority()

# tests/test_runtime_manager.py
def test_async_runtime_lifecycle()
def test_concurrent_task_management()
def test_graceful_shutdown()
```

### 集成测试

```bash
# 每个功能完成后的测试流程

# 1. 在虚拟环境中运行单元测试
source venv/bin/activate
pytest tests/test_proxy_server.py -v
pytest tests/ -v

# 2. 使用 uvx 测试 CLI 功能
uvx --from . qcc proxy start
uvx --from . qcc health check
uvx --from . qcc endpoint list production
uvx --from . qcc priority list

# 3. 集成测试场景
uvx --from . qcc init                    # 初始化测试
uvx --from . qcc add test-config         # 配置管理测试
uvx --from . qcc endpoint add test-config  # Endpoint 测试
uvx --from . qcc proxy start              # 代理启动测试
```

### 测试清单

- [ ] 代理服务器与 Claude Code 集成测试
- [ ] 多 endpoint 负载均衡测试
- [ ] 故障转移场景测试
- [ ] 健康检测实时性测试
- [ ] 队列重试机制测试
- [ ] **uvx 命令行测试** (必须)
- [ ] 虚拟环境兼容性测试

### 性能测试

```bash
# 使用 uvx 进行性能测试
uvx --from . qcc benchmark --concurrent 50 --duration 60
uvx --from . qcc benchmark --requests 1000
```

- [ ] 并发请求压力测试 (目标: > 100 并发)
- [ ] 响应时间测试 (目标: < 50ms 延迟)
- [ ] 内存占用测试
- [ ] 长时间运行稳定性测试 (24小时)

---

## 📊 成功指标

1. **功能完整性**
   - ✅ 所有核心功能实现
   - ✅ CLI 命令覆盖所有功能
   - ✅ 测试覆盖率 > 80%

2. **性能指标**
   - 代理延迟 < 50ms
   - 支持并发请求 > 100
   - 健康检测周期 < 60s
   - 故障转移时间 < 5s

3. **稳定性指标**
   - 7x24小时稳定运行
   - 内存泄漏检测通过
   - 异常处理覆盖全面

4. **用户体验**
   - 配置简单直观
   - 命令语义清晰
   - 文档详细完整

---

## 🔧 配置示例

### 完整配置文件示例

```json
{
  "version": "0.4.0",
  "user_id": "github-123456",
  "profiles": [
    {
      "name": "production",
      "description": "生产环境配置",
      "priority": "primary",
      "enabled": true,
      "endpoints": [
        {
          "id": "prod-1",
          "base_url": "https://api.anthropic.com",
          "api_key": "sk-ant-xxxxx",
          "weight": 100,
          "priority": 1,
          "enabled": true,
          "max_failures": 3,
          "timeout": 30,
          "metadata": {
            "provider": "anthropic-official",
            "region": "us-east-1"
          }
        },
        {
          "id": "prod-2",
          "base_url": "https://api.claudeplus.com",
          "api_key": "sk-cp-xxxxx",
          "weight": 50,
          "priority": 2,
          "enabled": true,
          "max_failures": 3,
          "timeout": 30,
          "metadata": {
            "provider": "claude-plus",
            "region": "us-west-1"
          }
        }
      ],
      "load_balancing": {
        "strategy": "weighted",
        "health_aware": true,
        "sticky_session": false
      }
    },
    {
      "name": "backup",
      "description": "备份配置",
      "priority": "secondary",
      "enabled": true,
      "endpoints": [
        {
          "id": "backup-1",
          "base_url": "https://backup-api.com",
          "api_key": "sk-backup-xxxxx",
          "weight": 100,
          "priority": 1,
          "enabled": true
        }
      ]
    }
  ],
  "proxy": {
    "host": "127.0.0.1",
    "port": 7860,
    "ssl_enabled": false,
    "log_level": "INFO",
    "access_log": true,
    "max_connections": 100
  },
  "health": {
    "enabled": true,
    "check_interval": 60,
    "timeout": 10,
    "retry_count": 3,
    "alert_enabled": true,
    "alert_threshold": 3
  },
  "queue": {
    "enabled": true,
    "max_size": 1000,
    "retry_strategy": "exponential_backoff",
    "max_retries": 5,
    "persistence_enabled": true,
    "persistence_path": "~/.qcc/failure_queue.json"
  },
  "switching_policy": {
    "auto_switch": true,
    "switch_threshold": 3,
    "cooldown_period": 300,
    "fallback_enabled": true
  }
}
```

---

## 📚 使用示例

### 基础使用流程

```bash
# 1. 初始化 (如果还没有)
qcc init

# 2. 添加配置并设置多个 endpoint
qcc add production --description "生产环境"

# 3. 为配置添加多个 endpoint (从现有配置复用)
qcc endpoint add production
#
# 💡 选择添加方式:
#   1. 从现有配置复用 (推荐) ⭐
#   2. 手动输入新配置
#   3. 从厂商快速配置
# 请选择 (1-3): 1
#
# 📋 可用配置列表:
#   1. work - 工作配置 (https://api.anthropic.com)
#   2. backup - 备份配置 (https://api.claudeplus.com)
#   3. personal - 个人配置 (https://api.custom.com)
# 请选择配置 (1-3): 1
#
# ✅ 已选择配置: work
#   BASE_URL: https://api.anthropic.com
#   API_KEY: sk-ant-xxxxx...yyyy
#
# 是否修改 BASE_URL? (y/N): n
# 是否修改 API_KEY? (y/N): n
#
# 设置权重 (默认 100): 100
# 设置优先级 (默认 1): 1
# 设置超时时间/秒 (默认 30): 30
#
# ✅ Endpoint 添加成功！

# 4. 添加第二个 endpoint (手动输入)
qcc endpoint add production
# 选择添加方式: 2 (手动输入)
# 输入 BASE_URL: https://api.backup.com
# 输入 API_KEY: sk-backup-xxxxx
# 设置权重: 50
# 设置优先级: 2

# 5. 查看 endpoint 列表
qcc endpoint list production

# 5. 测试 endpoint 连通性
qcc endpoint test production prod-1

# 6. 配置负载均衡策略
qcc config set loadbalancer.strategy weighted
qcc config set loadbalancer.health_aware true

# 7. 启动代理服务
qcc proxy start

# 8. 查看代理状态
qcc proxy status

# 9. 查看健康状态
qcc health status

# 10. 配置环境变量让 Claude Code 使用代理
export ANTHROPIC_BASE_URL=http://127.0.0.1:7860
export ANTHROPIC_API_KEY=proxy-managed

# 11. 启动 Claude Code
qcc use production
# 或者
claude
```

### 高级场景

#### 场景 1: 多配置主次切换

```bash
# 设置主配置
qcc priority set production primary

# 设置次配置
qcc priority set backup secondary

# 设置兜底配置
qcc priority set emergency fallback

# 查看优先级配置
qcc priority list

# 配置自动切换策略
qcc priority policy
# 交互式配置: 切换阈值、冷却时间等
```

#### 场景 2: 故障排查

```bash
# 查看失败队列
qcc queue status

# 查看队列详情
qcc queue list

# 查看某个 endpoint 的健康历史
qcc health history prod-1

# 手动重试失败的请求
qcc queue retry req-12345

# 重试所有失败请求
qcc queue retry-all

# 清空失败队列
qcc queue clear
```

#### 场景 3: 从现有配置快速构建代理配置

```bash
# 假设你已经有多个独立的配置
qcc list
# 输出:
#   ⭐ work - 工作配置
#      personal - 个人配置
#      backup - 备份配置
#      emergency - 应急配置

# 创建一个新的代理配置，复用现有的 API Key
qcc add proxy-prod --description "生产代理配置"

# 从 work 配置复用第一个 endpoint (主要)
qcc endpoint add proxy-prod
# 选择: 1 (从现有配置复用)
# 选择配置: work
# 权重: 100, 优先级: 1

# 从 personal 配置复用第二个 endpoint (次要)
qcc endpoint add proxy-prod
# 选择: 1 (从现有配置复用)
# 选择配置: personal
# 权重: 50, 优先级: 2

# 从 backup 配置复用第三个 endpoint (备份)
qcc endpoint add proxy-prod
# 选择: 1 (从现有配置复用)
# 选择配置: backup
# 权重: 30, 优先级: 3

# 查看构建好的代理配置
qcc endpoint list proxy-prod
# 输出:
#   📋 proxy-prod 的 Endpoint 列表:
#   1. endpoint-1 [✓] - https://api.anthropic.com (权重:100, 优先级:1)
#   2. endpoint-2 [✓] - https://api.custom.com (权重:50, 优先级:2)
#   3. endpoint-3 [✓] - https://api.backup.com (权重:30, 优先级:3)

# 设置为主配置并启动代理
qcc priority set proxy-prod primary
qcc proxy start
```

#### 场景 4: 配置自动故障转移

```bash
# 步骤 1: 创建多个配置
qcc add production --description "生产主配置"
qcc add backup --description "备用配置"
qcc add emergency --description "应急配置"

# 步骤 2: 设置优先级
qcc priority set production primary
qcc priority set backup secondary
qcc priority set emergency fallback

# 步骤 3: 查看优先级配置
qcc priority list
# 输出:
#   ⭐ PRIMARY [✓]
#     • production (当前活跃)
#
#   🔵 SECONDARY [✓]
#     • backup
#
#   🟡 FALLBACK [✓]
#     • emergency

# 步骤 4: 配置故障转移策略
qcc priority policy --auto-failover --auto-recovery \
  --failure-threshold 3 --cooldown 300
# ✓ 故障转移策略已更新
#   自动故障转移: ✓
#   自动恢复: ✓
#   故障阈值: 3 次
#   冷却期: 300 秒

# 步骤 5: 启动代理服务（自动启动故障转移监控）
qcc proxy start
# ✓ 代理服务器已启动: http://127.0.0.1:7860
# ✓ 故障转移监控已启动 (检查间隔: 60秒)

# 当 production 配置失败时，自动触发故障转移:
# ============================================================
# 🔄 故障转移: production → backup
# 原因: 连续 3 次健康检查失败
# ============================================================
# ✓ 故障转移完成，当前使用配置: backup

# 查看故障转移历史
qcc priority history
# 输出:
#   🔄 FAILOVER
#      时间: 2025-10-16T14:30:00
#      从: production
#      到: backup
#      原因: 连续 3 次健康检查失败

# 手动切换到应急配置
qcc priority switch emergency --reason "测试应急配置"
# ✓ 已切换到配置 'emergency'
```

#### 场景 5: 性能监控

```bash
# 查看代理日志
qcc proxy logs

# 查看实时统计
qcc proxy stats

# 导出监控数据
qcc proxy export-stats stats.json

# 查看 endpoint 性能
qcc endpoint stats production
```

---

## 🚀 部署建议

### 开发环境

```bash
# 1. 克隆仓库
git clone https://github.com/lghguge520/qcc.git
cd qcc

# 2. 创建虚拟环境 (遵循项目规范: 必须使用 virtualenv, venv 命名)
virtualenv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 3. 安装开发依赖
pip install -e ".[dev]"

# 4. 运行单元测试 (在虚拟环境中)
pytest tests/ -v

# 5. 使用 uvx 测试 (遵循项目规范: 先测试再发布, 测试时必须使用 uvx)
uvx --from . qcc --help
uvx --from . qcc init
uvx --from . qcc list
```

**🔧 开发规范** (根据 CLAUDE.md):
- ✅ 必须使用 `virtualenv` 创建虚拟环境
- ✅ 虚拟环境必须命名为 `venv`
- ✅ 先测试再发布
- ✅ 测试时一定使用 `uvx` 进行测试

### 生产环境

```bash
# 1. 安装 qcc
uv tool install qcc

# 2. 初始化配置
qcc init

# 3. 配置生产环境 endpoint
qcc add production
qcc endpoint add production
# ... 添加多个 endpoint

# 4. 配置健康检测和重试
qcc config set health.enabled true
qcc config set queue.enabled true

# 5. 启动代理服务 (后台运行)
qcc proxy start --daemon

# 6. 配置开机自启 (systemd)
qcc proxy install-service
systemctl enable qcc-proxy
systemctl start qcc-proxy
```

---

## 🐛 已知问题和限制

1. **SSL/TLS 支持**
   - 当前版本仅支持 HTTP 代理
   - HTTPS 代理需要证书管理 (计划在 v0.5.0 实现)

2. **并发限制**
   - 默认最大并发连接数: 100
   - 可通过配置调整,但受系统资源限制

3. **请求缓存**
   - 当前版本不支持请求缓存
   - 计划在后续版本实现智能缓存

4. **跨平台兼容性**
   - Windows 系统需要额外配置
   - 某些系统工具可能不可用

---

## 📖 参考资料

- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference)
- [aiohttp Documentation](https://docs.aiohttp.org/)
- [Load Balancing Algorithms](https://en.wikipedia.org/wiki/Load_balancing_(computing))
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Exponential Backoff](https://en.wikipedia.org/wiki/Exponential_backoff)

---

## 💡 未来规划

### v0.5.0 - 高级功能
- [ ] HTTPS 代理支持
- [ ] 请求缓存机制
- [ ] API 限流控制
- [ ] 成本统计和优化
- [ ] Web 管理界面

### v0.6.0 - 企业功能
- [ ] 团队协作功能
- [ ] 权限管理
- [ ] 审计日志
- [ ] 合规性检查
- [ ] SLA 监控

### v1.0.0 - 稳定版本
- [ ] 完整的生产环境支持
- [ ] 高可用部署方案
- [ ] 性能优化和调优
- [ ] 完善的监控告警
- [ ] 详细的运维文档

---

## 👥 贡献指南

欢迎贡献代码和建议！请参考以下流程:

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 📞 联系方式

- GitHub Issues: [https://github.com/lghguge520/qcc/issues](https://github.com/lghguge520/qcc/issues)
- 项目主页: [https://github.com/lghguge520/qcc](https://github.com/lghguge520/qcc)

---

**文档版本**: v1.0
**最后更新**: 2025-10-16
**作者**: QCC Development Team
