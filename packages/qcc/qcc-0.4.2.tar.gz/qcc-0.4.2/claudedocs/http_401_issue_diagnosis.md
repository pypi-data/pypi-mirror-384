# HTTP 401 错误重复使用问题诊断

## 📋 问题描述

**现象**：返回 401 错误的 endpoint，仍然在被持续选中使用

**日志示例**：
```log
2025-10-17 17:24:12,192 - [req-31] 选中 endpoint: 5005ac67 (https://q.quuvv.cn)
2025-10-17 17:24:12,448 - [req-31] 响应失败: 401, 耗时: 255.99ms
2025-10-17 17:24:12,450 - Endpoint 5005ac67 加入失败队列, 原因: HTTP 401
2025-10-17 17:24:12,455 - [req-31] 重试 1/2, 选中 endpoint: 464c7ca1
2025-10-17 17:24:12,700 - [req-31] 响应失败: 401, 耗时: 244.63ms
2025-10-17 17:24:12,701 - Endpoint 464c7ca1 加入失败队列, 原因: HTTP 401
2025-10-17 17:24:12,702 - [req-31] 重试 2/2, 选中 endpoint: 1ca7bbf7
2025-10-17 17:24:12,961 - [req-31] 响应失败: 401, 耗时: 258.04ms
```

## 🔍 诊断步骤

### 步骤 1：检查 endpoint 健康状态

运行以下命令查看所有 endpoints 的健康状态：

```bash
# 假设有 cluster status 命令
qcc cluster status <cluster-name>
```

**期望输出**：
- 返回 401 的 endpoints 应该显示为 `unhealthy`
- `is_healthy()` 应该返回 `False`

### 步骤 2：检查 endpoint 配置

查看配置文件，确认是否有重复的 endpoints：

```bash
# 查看配置
cat ~/.qcc/config.yaml  # 或相应的配置文件
```

**检查项**：
- 是否有相同 `base_url` + `api_key` 的多个 endpoints
- 这些 endpoints 的 ID 是否相同

### 步骤 3：添加调试日志

在 `server.py` 的 `_select_endpoint()` 方法中添加调试日志：

```python
async def _select_endpoint(self):
    """选择 endpoint（通过负载均衡器）"""
    if self.load_balancer and self.config_manager:
        endpoints = self._get_active_endpoints()

        # 🔍 添加调试日志
        logger.debug(f"可用 endpoints: {len(endpoints)}")
        for ep in endpoints:
            logger.debug(
                f"  - {ep.id}: status={ep.health_status['status']}, "
                f"is_healthy={ep.is_healthy()}, "
                f"failures={ep.health_status['consecutive_failures']}"
            )

        if endpoints:
            selected = await self.load_balancer.select_endpoint(endpoints)
            logger.debug(f"选中: {selected.id if selected else 'None'}")
            return selected
```

### 步骤 4：检查 endpoint 对象引用

验证负载均衡器使用的 endpoint 对象，是否和被标记为 unhealthy 的是同一个实例：

```python
# 在 _forward_request 中添加日志
logger.debug(f"Endpoint {endpoint.id} 对象 ID: {id(endpoint)}")
```

## 🐛 可能的问题原因

### 原因 1：endpoint 对象不是同一个实例

**问题**：
- `_forward_request()` 标记的 endpoint 对象
- `_select_endpoint()` 使用的 endpoint 列表
- 这两者可能不是同一个对象引用

**验证方法**：
```python
# 检查对象 ID
print(f"Object ID: {id(endpoint)}")
```

**解决方案**：
- 确保 `_get_active_endpoints()` 返回的是配置中的实际 endpoint 对象
- 不要创建新的 endpoint 实例

### 原因 2：健康状态更新时机问题

**问题**：
- 健康状态在 `_forward_request()` 中更新
- 但 `_select_endpoint()` 在更新之前就已经获取了 endpoints 列表

**时间线**：
```
T1: _select_endpoint() 获取 endpoints (包含 EP1, EP2, EP3)
T2: EP1 返回 401
T3: 更新 EP1 状态为 unhealthy
T4: 重试时再次 _select_endpoint() → 应该过滤掉 EP1
```

**验证方法**：
- 在 T4 时检查 EP1 的 `is_healthy()` 是否返回 `False`

### 原因 3：`is_healthy()` 逻辑问题

**当前逻辑**：
```python
def is_healthy(self) -> bool:
    return (
        self.enabled and
        self.health_status['status'] in ['healthy', 'unknown'] and
        self.health_status['consecutive_failures'] < self.max_failures
    )
```

**可能的问题**：
- `status='unhealthy'` 时，第二个条件就是 `False`
- **BUT**：如果 `status` 没有被正确更新呢？

**验证方法**：
```python
# 添加断言
assert endpoint.health_status['status'] == 'unhealthy', \
    f"Expected 'unhealthy' but got '{endpoint.health_status['status']}'"
```

### 原因 4：配置持久化问题

**问题**：
- Endpoint 健康状态被更新
- 但配置没有被持久化
- 下次获取 endpoints 时，又读取了旧的健康状态

**验证方法**：
- 检查是否有配置保存逻辑
- 查看配置文件中的健康状态是否实时更新

## 🎯 临时解决方案

### 方案 1：立即禁用返回 401 的 endpoint

修改 [server.py:291-317](c:\project\qcc\fastcc\proxy\server.py#L291-L317)：

```python
# 检查状态码
is_success = response.status == 200

# 特殊处理 401/403（认证错误）
if response.status in [401, 403]:
    # 直接禁用 endpoint
    endpoint.enabled = False
    endpoint.update_health_status(
        status='unhealthy',
        increment_requests=True,
        is_failure=True,
        response_time=response_time
    )
    logger.error(
        f"[{request_id}] Endpoint {endpoint.id} 认证失败 ({response.status}), "
        f"已禁用"
    )
else:
    # 正常处理其他状态码
    endpoint.update_health_status(
        status='healthy' if is_success else 'unhealthy',
        increment_requests=True,
        is_failure=not is_success,
        response_time=response_time
    )
```

### 方案 2：增强 `is_healthy()` 检查

修改 [endpoint.py:252-262](c:\project\qcc\fastcc\core\endpoint.py#L252-L262)：

```python
def is_healthy(self) -> bool:
    """检查 endpoint 是否健康"""
    # 如果被禁用，立即返回 False
    if not self.enabled:
        return False

    # 如果状态是 unhealthy，立即返回 False
    if self.health_status['status'] == 'unhealthy':
        return False

    # 检查连续失败次数
    if self.health_status['consecutive_failures'] >= self.max_failures:
        return False

    # 只有 healthy 或 unknown 才返回 True
    return self.health_status['status'] in ['healthy', 'unknown']
```

### 方案 3：添加 401 错误的特殊标记

在 health_status 中添加一个标记：

```python
# 在 __init__ 中添加
self.health_status = {
    'status': 'unknown',
    'auth_failed': False,  # 🆕 认证失败标记
    ...
}

# 在 is_healthy() 中检查
def is_healthy(self) -> bool:
    if self.health_status.get('auth_failed', False):
        return False  # 认证失败，永久不健康
    ...
```

## 📝 下一步行动

1. **添加调试日志**：按照步骤 3 添加详细的调试日志
2. **运行测试**：使用返回 401 的 endpoint 进行测试
3. **分析日志**：查看 `is_healthy()` 的返回值和 endpoint 选择过程
4. **确认根因**：根据日志确定是哪个原因导致的问题
5. **应用修复**：选择合适的解决方案

## 🔗 相关文档

- [响应有效性检查修复](./response_valid_check_fix.md)
- [验证码健康检查机制](./verification_code_health_check.md)
- [Endpoint 稳定 ID 修复](./endpoint_stable_id_fix.md)
