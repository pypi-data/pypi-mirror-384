# Bug修复：失败队列重复计数问题

## 问题描述

在使用集群配置时，发现失败队列中显示的 endpoint 数量异常。例如，配置了1个主节点和1个副节点（共2个 endpoint），但验证失败的 endpoint 显示为 26 个。

## 根本原因

在 [fastcc/proxy/server.py](../fastcc/proxy/server.py) 中，有**3个地方**会调用 `add_failed_endpoint`：

1. **第438行**：响应失败（非200状态码）时
2. **第462行**：请求超时时
3. **第478行**：请求异常时

当同一个请求经历多次重试（最多3次尝试）时，可能触发多次失败条件：
- 第1次尝试：超时 → 调用 `add_failed_endpoint`
- 第2次尝试：返回500错误 → 再次调用 `add_failed_endpoint`
- 第3次尝试：网络异常 → 又调用 `add_failed_endpoint`

虽然 `failed_endpoints` 使用的是 `Set` 类型（自动去重），但存在以下问题：

1. **统计数据不准确**：`stats['total_failed']` 会累加，导致统计值远大于实际失败的 endpoint 数量
2. **日志重复**：同一个 endpoint 失败时会多次输出加入队列的日志
3. **用户困惑**：显示的失败数量与实际配置的 endpoint 数量不符

## 修复方案

在 [fastcc/proxy/failure_queue.py](../fastcc/proxy/failure_queue.py) 的 `add_failed_endpoint` 方法中添加去重逻辑：

```python
def add_failed_endpoint(self, endpoint_id: str, reason: str = ""):
    """将失败的 endpoint 加入队列"""
    if endpoint_id not in self.failed_endpoints:
        # 第一次添加：正常处理
        self.failed_endpoints.add(endpoint_id)
        self.last_check_times[endpoint_id] = datetime.now()
        self.stats['total_failed'] += 1
        logger.info(f"Endpoint {endpoint_id} 加入失败队列, 原因: {reason}")
        self._save()
    else:
        # 已存在：只记录日志，不重复计数
        logger.debug(
            f"Endpoint {endpoint_id} 已在失败队列中（原因: {reason}），跳过重复添加"
        )
```

## 修复效果

### 修复前
```
🔍 开始验证失败的 endpoint (26 个)
```
（实际只有2个 endpoint，但被重复计数了13次）

### 修复后
```
🔍 开始验证失败的 endpoint (2 个)
```
（正确显示实际失败的 endpoint 数量）

## 测试验证

创建了完整的单元测试 [tests/test_failure_queue_dedup.py](../tests/test_failure_queue_dedup.py) 验证以下场景：

1. ✅ 重复添加同一个 endpoint 不会被计数两次
2. ✅ 添加多个不同的 endpoint 正常计数
3. ✅ 移除后重新添加 endpoint 会重新计数
4. ✅ 持久化数据的去重正确性

所有测试均通过：

```
tests/test_failure_queue_dedup.py::test_duplicate_endpoint_not_counted_twice PASSED
tests/test_failure_queue_dedup.py::test_multiple_different_endpoints PASSED
tests/test_failure_queue_dedup.py::test_remove_and_readd_endpoint PASSED
tests/test_failure_queue_dedup.py::test_persistence_with_duplicates PASSED
```

## 影响范围

- 修改文件：`fastcc/proxy/failure_queue.py`
- 影响功能：失败队列的 endpoint 计数和统计
- 向后兼容：完全兼容，不影响现有功能
- 性能影响：无，仅增加一次 Set 查询

## 并发安全性增强（2025-10-17 补充修复）

### 新发现的问题

在多线程/协程并发调用同一个节点失败时，存在**竞态条件（Race Condition）**：

```python
# 并发场景问题：
协程1: if endpoint_id not in self.failed_endpoints:  # True
协程2: if endpoint_id not in self.failed_endpoints:  # True (还未被协程1添加)
协程1:     self.failed_endpoints.add(endpoint_id)
        self.stats['total_failed'] += 1  # 计数器 +1
协程2:     self.failed_endpoints.add(endpoint_id)  # Set去重，但...
        self.stats['total_failed'] += 1  # 计数器又 +1 ❌
```

### 并发安全修复

在 `FailureQueue` 中添加 `asyncio.Lock` 保护共享资源：

```python
class FailureQueue:
    def __init__(self, ...):
        self._lock = asyncio.Lock()  # 添加异步锁

    async def add_failed_endpoint(self, endpoint_id: str, reason: str = ""):
        async with self._lock:  # 使用锁保护
            if endpoint_id not in self.failed_endpoints:
                self.failed_endpoints.add(endpoint_id)
                self.stats['total_failed'] += 1
                # ...
```

### 修改内容

1. **添加异步锁**：`self._lock = asyncio.Lock()` ([failure_queue.py:55](../fastcc/proxy/failure_queue.py#L55))
2. **方法改为异步**：`add_failed_endpoint` 和 `remove_endpoint` 改为 `async` 方法
3. **使用锁保护**：所有修改共享状态的代码都在 `async with self._lock` 中执行
4. **更新调用点**：`server.py` 中的3处调用都改为 `await` 调用

### 新增并发测试

```python
@pytest.mark.asyncio
async def test_concurrent_add_same_endpoint():
    """10个协程同时添加同一个endpoint"""
    tasks = [queue.add_failed_endpoint("ep-1", f"Error {i}") for i in range(10)]
    await asyncio.gather(*tasks)

    # 验证：只计数一次
    assert queue.stats['total_failed'] == 1  # ✅ 不是 10
```

所有并发测试通过：
- ✅ 并发添加同一endpoint（10个协程）
- ✅ 并发添加不同endpoint（10个协程）
- ✅ 并发添加和移除操作

## 版本信息

- 修复版本：v0.4.1+
- 修复日期：2025-10-17
- 相关文件：
  - [fastcc/proxy/failure_queue.py](../fastcc/proxy/failure_queue.py) - 添加异步锁和线程安全保护
  - [fastcc/proxy/server.py](../fastcc/proxy/server.py) - 更新为异步调用
  - [tests/test_failure_queue_dedup.py](../tests/test_failure_queue_dedup.py) - 添加并发安全测试
  - [docs/concurrency_issue_analysis.md](concurrency_issue_analysis.md) - 并发问题详细分析
