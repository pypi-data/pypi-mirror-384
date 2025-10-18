# QCC 智能健康检测系统 - 测试指南

本文档提供完整的测试方法和步骤。

---

## 🚀 快速开始

### 前提条件

```bash
# 确保在项目根目录
cd /Users/yxhpy/Desktop/project/qcc

# 激活虚拟环境
source venv/bin/activate
```

---

## 1️⃣ 单元测试（推荐）

### 运行所有测试

```bash
# 运行智能健康检测的所有测试
python -m pytest tests/test_intelligent_health_check.py -v

# 预期输出：20 passed in ~0.15s
```

### 运行特定测试类

```bash
# 只测试健康检查模型
python -m pytest tests/test_intelligent_health_check.py::TestHealthCheckModels -v

# 只测试性能指标
python -m pytest tests/test_intelligent_health_check.py::TestPerformanceMetrics -v

# 只测试权重调整器
python -m pytest tests/test_intelligent_health_check.py::TestWeightAdjuster -v

# 只测试对话检查器
python -m pytest tests/test_intelligent_health_check.py::TestConversationalHealthChecker -v
```

### 查看测试覆盖率

```bash
# 安装 coverage (如果还没安装)
pip install pytest-cov

# 运行测试并生成覆盖率报告
python -m pytest tests/test_intelligent_health_check.py --cov=fastcc.proxy --cov-report=term-missing

# 生成 HTML 报告
python -m pytest tests/test_intelligent_health_check.py --cov=fastcc.proxy --cov-report=html
# 然后打开 htmlcov/index.html 查看
```

---

## 2️⃣ 演示脚本

### 运行完整演示

```bash
# 运行演示脚本（展示所有功能）
PYTHONPATH=$PWD python examples/health_check_demo.py
```

**演示内容**:
1. ✅ 健康检查数据模型
2. ✅ 性能指标统计（模拟10次检查）
3. ✅ 动态权重调整（3种场景）
4. ✅ 对话式健康检查器配置
5. ✅ 功能总结

---

## 3️⃣ CLI 命令测试

### 查看帮助

```bash
# 本地开发测试
uvx --from . qcc health --help           # 查看 health 命令组
uvx --from . qcc health test --help      # 查看 test 子命令
uvx --from . qcc health metrics --help   # 查看 metrics 子命令

# 远程安装使用
uvx qcc health --help                    # 查看 health 命令组
uvx qcc health test --help               # 查看 test 子命令
uvx qcc health metrics --help            # 查看 metrics 子命令
```

### 测试命令（需要配置 endpoints）

```bash
# 注意：以下命令需要先配置 endpoints 才能真正使用

# 本地开发测试
uvx --from . qcc health test             # 执行健康测试
uvx --from . qcc health test endpoint-1  # 测试指定 endpoint
uvx --from . qcc health test -v          # 显示详细信息
uvx --from . qcc health metrics          # 查看性能指标
uvx --from . qcc health metrics endpoint-1  # 查看指定 endpoint 的指标

# 远程安装使用
uvx qcc health test                      # 执行健康测试
uvx qcc health test endpoint-1           # 测试指定 endpoint
uvx qcc health test -v                   # 显示详细信息
uvx qcc health metrics                   # 查看性能指标
uvx qcc health metrics endpoint-1        # 查看指定 endpoint 的指标
```

---

## 4️⃣ Python API 测试

### 快速验证导入

```bash
python -c "
from fastcc.proxy import (
    ConversationalHealthChecker,
    PerformanceMetrics,
    DynamicWeightAdjuster,
    HealthMonitor,
    ConversationalHealthCheck,
    HealthCheckResult
)
print('✅ 所有模块导入成功')
"
```

### 交互式测试

```python
# 启动 Python 解释器
python

# 然后在解释器中运行：
from fastcc.proxy import PerformanceMetrics, DynamicWeightAdjuster
from fastcc.proxy.health_check_models import ConversationalHealthCheck, HealthCheckResult
from fastcc.core.endpoint import Endpoint

# 创建性能指标
metrics = PerformanceMetrics("test-endpoint")

# 添加一些检查结果
for i in range(5):
    check = ConversationalHealthCheck("test-endpoint")
    check.result = HealthCheckResult.SUCCESS
    check.response_time_ms = 200.0 + i * 10
    metrics.add_check_result(check)

# 查看统计
print(f"成功率: {metrics.success_rate}%")
print(f"平均响应时间: {metrics.avg_response_time}ms")
print(f"稳定性评分: {metrics.stability_score}/100")

# 测试权重调整
adjuster = DynamicWeightAdjuster()
endpoint = Endpoint(base_url="https://test.com", api_key="test", weight=100)
new_weight = adjuster.calculate_new_weight(endpoint.id, 100, metrics)
print(f"新权重: {new_weight}")
```

---

## 5️⃣ 集成测试（需要真实 API）

如果你有真实的 Anthropic API Key，可以进行真实的对话测试：

### 创建测试脚本

```python
# test_real_api.py
import asyncio
from fastcc.proxy import ConversationalHealthChecker
from fastcc.core.endpoint import Endpoint

async def test_real_endpoint():
    # 替换为你的真实 API Key
    endpoint = Endpoint(
        base_url="https://api.anthropic.com",
        api_key="sk-ant-your-key-here",  # 替换为真实 Key
        weight=100
    )

    checker = ConversationalHealthChecker()

    print("🔍 开始真实 API 测试...")
    check = await checker.check_endpoint(endpoint)

    print(f"\n结果: {check.result.value}")
    print(f"响应时间: {check.response_time_ms:.0f}ms")
    print(f"测试消息: {check.test_message}")
    print(f"响应内容: {check.response_content}")
    print(f"质量评分: {check.response_score}/100")
    print(f"响应有效: {check.response_valid}")

if __name__ == "__main__":
    asyncio.run(test_real_endpoint())
```

### 运行真实 API 测试

```bash
PYTHONPATH=$PWD python test_real_api.py
```

---

## 6️⃣ 性能测试

### 测试并发性能

```python
# test_concurrent.py
import asyncio
import time
from fastcc.proxy import ConversationalHealthChecker
from fastcc.core.endpoint import Endpoint

async def test_concurrent_checks():
    # 创建多个测试 endpoint
    endpoints = [
        Endpoint(
            base_url=f"https://test-{i}.com",
            api_key="test-key",
            weight=100
        )
        for i in range(10)
    ]

    checker = ConversationalHealthChecker()

    print(f"🚀 开始并发测试 {len(endpoints)} 个 endpoints...")
    start_time = time.time()

    # 这里会失败因为是测试 URL，但可以测试并发性能
    try:
        results = await checker.check_all_endpoints(endpoints)
        elapsed = time.time() - start_time

        print(f"✅ 完成测试")
        print(f"⏱️  总耗时: {elapsed:.2f}秒")
        print(f"📊 平均每个: {elapsed/len(endpoints):.2f}秒")
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"⏱️  并发执行时间: {elapsed:.2f}秒")

if __name__ == "__main__":
    asyncio.run(test_concurrent_checks())
```

---

## 7️⃣ 持续集成测试

### GitHub Actions 配置示例

```yaml
# .github/workflows/test-health-check.yml
name: Test Intelligent Health Check

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest tests/test_intelligent_health_check.py -v --cov=fastcc.proxy

    - name: Run demo
      run: |
        PYTHONPATH=$PWD python examples/health_check_demo.py
```

---

## 📊 测试结果示例

### 单元测试输出

```
tests/test_intelligent_health_check.py::TestHealthCheckModels::test_conversational_health_check_creation PASSED
tests/test_intelligent_health_check.py::TestHealthCheckModels::test_conversational_health_check_to_dict PASSED
tests/test_intelligent_health_check.py::TestHealthCheckModels::test_conversational_health_check_from_dict PASSED
tests/test_intelligent_health_check.py::TestPerformanceMetrics::test_performance_metrics_creation PASSED
tests/test_intelligent_health_check.py::TestPerformanceMetrics::test_add_success_check_result PASSED
tests/test_intelligent_health_check.py::TestPerformanceMetrics::test_add_failure_check_result PASSED
tests/test_intelligent_health_check.py::TestPerformanceMetrics::test_success_rate_calculation PASSED
tests/test_intelligent_health_check.py::TestPerformanceMetrics::test_avg_response_time_calculation PASSED
tests/test_intelligent_health_check.py::TestPerformanceMetrics::test_p95_response_time_calculation PASSED
tests/test_intelligent_health_check.py::TestPerformanceMetrics::test_stability_score_all_success PASSED
tests/test_intelligent_health_check.py::TestWeightAdjuster::test_weight_adjustment_strategy_defaults PASSED
tests/test_intelligent_health_check.py::TestWeightAdjuster::test_calculate_response_score PASSED
tests/test_intelligent_health_check.py::TestWeightAdjuster::test_calculate_failure_penalty PASSED
tests/test_intelligent_health_check.py::TestWeightAdjuster::test_calculate_new_weight_good_performance PASSED
tests/test_intelligent_health_check.py::TestWeightAdjuster::test_calculate_new_weight_poor_performance PASSED
tests/test_intelligent_health_check.py::TestWeightAdjuster::test_adjust_endpoint_weight PASSED
tests/test_intelligent_health_check.py::TestConversationalHealthChecker::test_conversational_health_checker_creation PASSED
tests/test_intelligent_health_check.py::TestConversationalHealthChecker::test_validate_response PASSED
tests/test_intelligent_health_check.py::TestConversationalHealthChecker::test_calculate_response_score PASSED
tests/test_intelligent_health_check.py::test_end_to_end_health_check_flow PASSED

============================== 20 passed in 0.13s ==============================
```

### 演示脚本输出

```
🔍 测试场景: 快速稳定 (endpoint-fast)
   当前权重: 100
   新权重: 156.5 (+56.5, +56.5%)
   平均响应: 155ms
   成功率: 100%
   稳定性: 99/100
   ✅ 权重提升：性能优秀

🔍 测试场景: 不稳定 (endpoint-unstable)
   当前权重: 100
   新权重: 88.6 (-11.4, -11.4%)
   平均响应: 350ms
   成功率: 67%
   稳定性: 62/100
   ⚠️  权重降低：性能不佳
```

---

## 🐛 调试技巧

### 启用详细日志

```python
import logging

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

# 或者只启用特定模块的日志
logging.getLogger('fastcc.proxy.health_monitor').setLevel(logging.DEBUG)
logging.getLogger('fastcc.proxy.conversational_checker').setLevel(logging.DEBUG)
```

### 使用 pdb 调试

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或者在 pytest 中使用
pytest tests/test_intelligent_health_check.py --pdb
```

### 查看详细错误

```bash
# 显示完整的错误堆栈
pytest tests/test_intelligent_health_check.py -v --tb=long

# 只显示失败的测试
pytest tests/test_intelligent_health_check.py -v --tb=short -x
```

---

## ✅ 测试检查清单

在提交代码前，确保：

- [ ] 所有单元测试通过（20/20）
- [ ] 演示脚本运行成功
- [ ] CLI 命令帮助信息正确
- [ ] 代码通过 lint 检查
- [ ] 文档和注释完整
- [ ] 没有警告或错误输出

---

## 📞 获取帮助

如果遇到问题：

1. 查看测试输出的错误信息
2. 检查虚拟环境是否正确激活
3. 确认所有依赖已安装：`pip install -e .`
4. 查看实现报告：`tasks/intelligent-health-check-implementation.md`
5. 运行演示查看预期行为：`python examples/health_check_demo.py`

---

**测试指南版本**: v1.0
**创建日期**: 2025-10-16
**维护者**: QCC Development Team
