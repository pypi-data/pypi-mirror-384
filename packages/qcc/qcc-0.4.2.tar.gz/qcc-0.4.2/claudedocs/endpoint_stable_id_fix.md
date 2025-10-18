# Endpoint ID 稳定性修复

## 问题描述

### 原始问题
当使用 `test2` 配置（1 个主节点 + 2 个辅助节点）时，即使所有节点使用相同的 `base_url` 和 `api_key`，系统仍然显示 "🔍 开始验证失败的 endpoint (18 个)"，而不是预期的 1 个或 3 个。

### 根本原因
在修复之前，`Endpoint` 类的 ID 生成逻辑是：
```python
self.id = str(uuid.uuid4())[:8]  # 每次创建实例都生成随机 ID
```

这导致：
1. **每次创建** `Endpoint` 实例都会生成**新的随机 ID**
2. 即使 `base_url` 和 `api_key` 完全相同，ID 也不同
3. 失败队列使用 `endpoint.id` 作为唯一标识，导致重复计数
4. 虽然 `__hash__()` 和 `__eq__()` 基于 `(base_url, api_key)`，但 ID 不稳定

### 问题影响
- ❌ 相同配置的多个节点被当作不同的 endpoint
- ❌ 失败队列无法正确去重
- ❌ 健康检查会对相同 endpoint 重复验证
- ❌ 统计数据不准确（显示 18 个而不是实际数量）

## 解决方案

### 核心修改
将 ID 生成从**随机**改为**基于内容的哈希**：

```python
# 修改前
self.id = str(uuid.uuid4())[:8]  # ❌ 随机

# 修改后
self.id = self._generate_stable_id(base_url, api_key)  # ✅ 稳定
```

### 实现细节

#### 1. 新增静态方法生成稳定 ID
```python
@staticmethod
def _generate_stable_id(base_url: str, api_key: str) -> str:
    """基于 base_url 和 api_key 生成稳定的唯一 ID

    Args:
        base_url: API 基础 URL
        api_key: API Key

    Returns:
        8 字符的稳定 ID
    """
    # 使用 SHA256 哈希确保唯一性和稳定性
    content = f"{base_url}|{api_key}".encode('utf-8')
    hash_value = hashlib.sha256(content).hexdigest()
    return hash_value[:8]  # 取前 8 个字符作为短 ID
```

#### 2. 更新导入
```python
# 修改前
import uuid

# 修改后
import hashlib
```

#### 3. 更新文档注释
```python
class Endpoint:
    """Endpoint 配置模型

    代表一个 API endpoint，包含 URL、API Key、权重、优先级等配置信息。
    支持从现有 ConfigProfile 创建，记录来源配置以便追溯。

    注意：endpoint 的唯一性由 (base_url, api_key) 决定，ID 基于这两者的哈希值生成。
    """
```

## 验证测试

### 测试覆盖
创建了 7 个测试用例验证修复：

1. ✅ `test_stable_id_same_config` - 相同配置生成相同 ID
2. ✅ `test_stable_id_different_configs` - 不同配置生成不同 ID
3. ✅ `test_stable_id_with_different_metadata` - 元数据不影响 ID
4. ✅ `test_id_format` - ID 格式验证（8 字符十六进制）
5. ✅ `test_failure_queue_deduplication` - 失败队列去重
6. ✅ `test_from_dict_preserves_id` - 序列化/反序列化保持 ID
7. ✅ `test_equality_and_hash_consistency` - 相等性和哈希一致性

### 测试结果
```bash
$ uvx -n pytest tests/test_endpoint_stable_id.py -v

============================= test session starts =============================
tests/test_endpoint_stable_id.py::test_stable_id_same_config PASSED      [ 14%]
tests/test_endpoint_stable_id.py::test_stable_id_different_configs PASSED [ 28%]
tests/test_endpoint_stable_id.py::test_stable_id_with_different_metadata PASSED [ 42%]
tests/test_endpoint_stable_id.py::test_id_format PASSED                  [ 57%]
tests/test_endpoint_stable_id.py::test_failure_queue_deduplication PASSED [ 71%]
tests/test_endpoint_stable_id.py::test_from_dict_preserves_id PASSED     [ 85%]
tests/test_endpoint_stable_id.py::test_equality_and_hash_consistency PASSED [100%]

============================== 7 passed in 0.05s ==============================
```

### 实际场景验证

使用 `test2` 配置（1 主 + 2 辅助节点）：

```bash
$ uvx -n python test_stable_id_fix.py

============================================================
测试 Endpoint ID 稳定性修复
============================================================

📋 配置信息:
  Base URL: https://jp.duckcoding.com
  API Key: sk-7yVW8CrBSuYvV3sKd...wv26QHl12j

🔧 创建 3 个 endpoint 实例...

🔍 生成的 endpoint ID:
  Endpoint 1 (primary): 1e3e69eb
  Endpoint 2 (auxiliary-1): 1e3e69eb
  Endpoint 3 (auxiliary-2): 1e3e69eb

✅ 验证结果:
  ✓ 所有 endpoint 生成相同的 ID: 1e3e69eb
  ✓ 所有 endpoint 相等性检查通过
  ✓ 所有 endpoint 哈希值相同: 5579457589831227710

🗂️ 测试失败队列去重:
  添加 Endpoint 1 后队列大小: 1
  添加 Endpoint 2 后队列大小: 1
  添加 Endpoint 3 后队列大小: 1
  ✓ 失败队列去重成功，只有 1 个唯一 endpoint

============================================================
✅ 所有测试通过！修复成功！
============================================================
```

## 影响范围

### 正面影响
✅ **去重正确性** - 失败队列能够正确识别相同的 endpoint
✅ **统计准确性** - 显示真实的失败 endpoint 数量
✅ **性能优化** - 避免对相同 endpoint 重复健康检查
✅ **资源节省** - 减少不必要的网络请求
✅ **ID 稳定性** - 跨会话、跨重启保持一致

### 兼容性
✅ **向后兼容** - `from_dict()` 方法保留原有 ID（如果存在）
✅ **相等性保持** - `__eq__()` 和 `__hash__()` 逻辑不变
✅ **序列化不变** - `to_dict()` 方法无需修改

### 潜在风险
⚠️ **现有数据** - 如果有持久化的旧 ID，会自动迁移到新 ID
⚠️ **测试依赖** - 依赖随机 ID 的测试可能需要调整（暂未发现）

## 测试文件

### 核心测试
- [tests/test_endpoint_stable_id.py](../tests/test_endpoint_stable_id.py) - 单元测试套件
- [test_stable_id_fix.py](../test_stable_id_fix.py) - 实际场景验证脚本

### 测试命令
```bash
# 运行单元测试
uvx -n pytest tests/test_endpoint_stable_id.py -v

# 运行实际场景验证
uvx -n python test_stable_id_fix.py
```

## 修改文件

### 源代码
- [fastcc/core/endpoint.py](../fastcc/core/endpoint.py)
  - 将 `import uuid` 改为 `import hashlib`
  - 修改 `__init__()` 中的 ID 生成逻辑
  - 新增 `_generate_stable_id()` 静态方法
  - 更新类文档注释

## 结论

通过将 Endpoint ID 从随机生成改为基于 `(base_url, api_key)` 的哈希生成，成功解决了：

1. ✅ **去重问题** - 相同配置的节点现在共享相同 ID
2. ✅ **统计准确性** - 失败队列计数正确
3. ✅ **性能优化** - 避免重复健康检查
4. ✅ **稳定性** - ID 在会话间保持一致

这个修复是**完全向后兼容**的，不会破坏现有功能，同时显著改善了系统的准确性和效率。

---

**修复日期**: 2025-10-17
**版本**: v0.4.2-dev
**测试状态**: ✅ 所有测试通过
