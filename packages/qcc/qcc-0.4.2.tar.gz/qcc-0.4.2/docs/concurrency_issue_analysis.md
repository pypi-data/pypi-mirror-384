# 多线程并发问题分析

## 问题场景

当多个请求并发调用同一个 endpoint 失败时，会出现**竞态条件（Race Condition）**：

```
时间轴：
T1: 请求A → endpoint-1 失败 → update_health_status(consecutive_failures++)
T2: 请求B → endpoint-1 失败 → update_health_status(consecutive_failures++)
T3: 请求C → endpoint-1 失败 → update_health_status(consecutive_failures++)
T4: 请求D → endpoint-1 失败 → add_failed_endpoint()  ← 此时才加入失败队列
```

## 当前实现的问题

### 1. **endpoint.update_health_status() 不是线程安全的**

[fastcc/core/endpoint.py:184-232](../fastcc/core/endpoint.py#L184-L232) 中的健康状态更新：

```python
def update_health_status(self, ...):
    self.health_status['total_requests'] += 1  # ❌ 非原子操作
    if is_failure:
        self.health_status['failed_requests'] += 1  # ❌ 非原子操作
        self.health_status['consecutive_failures'] += 1  # ❌ 非原子操作
```

**问题**：多个协程并发修改同一字典，导致：
- 计数器丢失更新（Lost Update）
- 成功率计算错误
- 连续失败次数不准确

### 2. **failure_queue.add_failed_endpoint() 虽然去重，但统计仍有问题**

[fastcc/proxy/failure_queue.py:57-79](../fastcc/proxy/failure_queue.py#L57-L79) 虽然已修复重复计数，但在并发场景下：

```python
# 并发场景：
# 协程1: if endpoint_id not in self.failed_endpoints:  # True
# 协程2: if endpoint_id not in self.failed_endpoints:  # True (还未被协程1添加)
# 协程1:     self.failed_endpoints.add(endpoint_id)
# 协程2:     self.failed_endpoints.add(endpoint_id)  # Set 会去重，但...
# 协程1:     self.stats['total_failed'] += 1  # ❌ 竞态条件
# 协程2:     self.stats['total_failed'] += 1  # ❌ 又加了一次
```

### 3. **server.py 中多个地方调用 add_failed_endpoint**

[fastcc/proxy/server.py](../fastcc/proxy/server.py) 的3个调用点：
- 第438行：HTTP 非200状态码
- 第462行：超时
- 第478行：异常

在重试逻辑中，同一个请求可能依次经历这3种失败，导致同一个 endpoint 被多次添加。

## 影响

### 现象
```
配置：2个 endpoint (主节点 + 副节点)
并发请求：10个请求同时失败

可能的结果：
- failed_endpoints: {endpoint-1, endpoint-2}  ← 正确（Set去重）
- stats['total_failed']: 20  ← 错误！应该是2

日志输出：
Endpoint endpoint-1 加入失败队列, 原因: Timeout
Endpoint endpoint-1 加入失败队列, 原因: Timeout  ← 重复
Endpoint endpoint-1 加入失败队列, 原因: Timeout  ← 重复
...（共10次）
```

### 数据一致性问题
1. **统计数据不准确**：`total_failed` 可能远大于实际失败的 endpoint 数量
2. **健康状态混乱**：`consecutive_failures` 可能丢失更新
3. **成功率计算错误**：由于计数器竞态条件

## 解决方案

### 方案1: 使用 asyncio.Lock（推荐）

为每个需要保护的资源添加异步锁：

```python
# endpoint.py
class Endpoint:
    def __init__(self, ...):
        self._lock = asyncio.Lock()

    async def update_health_status(self, ...):
        async with self._lock:
            self.health_status['total_requests'] += 1
            # ... 其他操作
```

```python
# failure_queue.py
class FailureQueue:
    def __init__(self, ...):
        self._lock = asyncio.Lock()

    async def add_failed_endpoint(self, endpoint_id: str, reason: str = ""):
        async with self._lock:
            if endpoint_id not in self.failed_endpoints:
                self.failed_endpoints.add(endpoint_id)
                self.stats['total_failed'] += 1
                # ... 其他操作
```

### 方案2: 使用 threading.Lock（如果有多线程）

如果使用多线程（非 asyncio），需要使用线程锁：

```python
import threading

class Endpoint:
    def __init__(self, ...):
        self._lock = threading.Lock()

    def update_health_status(self, ...):
        with self._lock:
            self.health_status['total_requests'] += 1
```

### 方案3: 使用原子操作库（性能优化）

```python
from threading import Lock
from contextlib import contextmanager

class AtomicCounter:
    def __init__(self, initial=0):
        self._value = initial
        self._lock = Lock()

    def increment(self, delta=1):
        with self._lock:
            self._value += delta
            return self._value

    @property
    def value(self):
        return self._value
```

## 推荐实现

### 优先级
1. **立即修复**：failure_queue 的 add_failed_endpoint 添加 asyncio.Lock
2. **次要修复**：endpoint 的 update_health_status 添加 asyncio.Lock
3. **优化改进**：考虑使用原子计数器减少锁开销

### 测试验证

需要添加并发测试：

```python
@pytest.mark.asyncio
async def test_concurrent_add_failed_endpoint():
    """测试并发添加失败 endpoint"""
    queue = FailureQueue(...)

    # 10个协程同时添加同一个 endpoint
    tasks = [
        queue.add_failed_endpoint("endpoint-1", f"Error {i}")
        for i in range(10)
    ]

    await asyncio.gather(*tasks)

    # 验证：只应该计数一次
    assert len(queue.failed_endpoints) == 1
    assert queue.stats['total_failed'] == 1  # 不应该是10
```

## 性能影响

- **锁开销**：每次操作需要获取锁，轻微性能影响
- **并发度下降**：锁会序列化并发操作
- **建议**：对于高并发场景，考虑使用无锁数据结构或分段锁

## 相关文件

- [fastcc/core/endpoint.py](../fastcc/core/endpoint.py) - Endpoint 健康状态管理
- [fastcc/proxy/failure_queue.py](../fastcc/proxy/failure_queue.py) - 失败队列管理
- [fastcc/proxy/server.py](../fastcc/proxy/server.py) - 请求处理和重试逻辑

## 修复优先级

🔴 **Critical**: failure_queue.add_failed_endpoint() - 直接影响统计准确性
🟡 **Important**: endpoint.update_health_status() - 影响健康检测准确性
🟢 **Nice-to-have**: 性能优化（原子计数器、无锁数据结构）
