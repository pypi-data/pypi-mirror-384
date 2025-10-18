# Endpoint 配置复用功能 - 技术实现方案

## 📋 功能概述

允许用户在为代理配置添加 endpoint 时，从现有的配置档案中选择并复用 `base_url` 和 `api_key`，避免重复输入，提高配置效率。

**文档版本**: v1.0
**创建日期**: 2025-10-16
**相关文档**: claude-code-proxy-development-plan.md

---

## 🎯 核心需求

### 用户场景

1. **场景 1: 构建高可用代理配置**
   - 用户有多个独立的 Claude 配置（work, personal, backup）
   - 想创建一个代理配置，整合这些 API Key
   - 不想重复输入已有的 base_url 和 api_key

2. **场景 2: 快速添加备份 endpoint**
   - 已有生产配置在使用
   - 需要快速添加备份 endpoint
   - 备份的 API Key 已经在其他配置中存在

3. **场景 3: 测试不同权重分配**
   - 同一个 API Key 想设置不同的权重
   - 测试不同的负载均衡策略
   - 快速调整 endpoint 参数

---

## 🏗️ 技术设计

### 1. 数据结构

#### ConfigProfile 扩展
```python
# fastcc/core/config.py

class ConfigProfile:
    """配置档案"""

    def __init__(self):
        self.name: str = ""
        self.description: str = ""
        self.base_url: str = ""           # 传统单 endpoint 字段（保持兼容）
        self.api_key: str = ""            # 传统单 endpoint 字段（保持兼容）
        self.endpoints: List[Endpoint] = []  # 新增：多 endpoint 支持
        self.priority: str = "primary"    # primary, secondary, fallback
        self.enabled: bool = True
        self.created_at: str = ""
        self.last_used: str = ""

    def to_dict(self):
        """转换为字典"""
        return {
            'name': self.name,
            'description': self.description,
            # 保持向后兼容：如果没有 endpoints，使用旧字段
            'base_url': self.base_url if not self.endpoints else self.endpoints[0].base_url,
            'api_key': self.api_key if not self.endpoints else self.endpoints[0].api_key,
            'endpoints': [ep.to_dict() for ep in self.endpoints],
            'priority': self.priority,
            'enabled': self.enabled,
            'created_at': self.created_at,
            'last_used': self.last_used
        }
```

#### Endpoint 数据模型
```python
# fastcc/core/endpoint.py

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

class Endpoint:
    """Endpoint 配置模型"""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        weight: int = 100,
        priority: int = 1,
        enabled: bool = True,
        max_failures: int = 3,
        timeout: int = 30,
        source_profile: Optional[str] = None,  # 🆕 来源配置名称
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())[:8]  # 短 ID
        self.base_url = base_url
        self.api_key = api_key
        self.weight = weight
        self.priority = priority
        self.enabled = enabled
        self.max_failures = max_failures
        self.timeout = timeout
        self.source_profile = source_profile  # 记录来源
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()

        # 健康状态
        self.health_status = {
            'status': 'unknown',  # unknown, healthy, degraded, unhealthy
            'last_check': None,
            'consecutive_failures': 0,
            'total_requests': 0,
            'failed_requests': 0,
            'success_rate': 100.0,
            'avg_response_time': 0
        }

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'base_url': self.base_url,
            'api_key': self.api_key,
            'weight': self.weight,
            'priority': self.priority,
            'enabled': self.enabled,
            'max_failures': self.max_failures,
            'timeout': self.timeout,
            'source_profile': self.source_profile,
            'metadata': self.metadata,
            'created_at': self.created_at,
            'health_status': self.health_status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建"""
        endpoint = cls(
            base_url=data['base_url'],
            api_key=data['api_key'],
            weight=data.get('weight', 100),
            priority=data.get('priority', 1),
            enabled=data.get('enabled', True),
            max_failures=data.get('max_failures', 3),
            timeout=data.get('timeout', 30),
            source_profile=data.get('source_profile'),
            metadata=data.get('metadata', {})
        )
        endpoint.id = data.get('id', endpoint.id)
        endpoint.created_at = data.get('created_at', endpoint.created_at)
        endpoint.health_status = data.get('health_status', endpoint.health_status)
        return endpoint

    @classmethod
    def from_profile(cls, profile: 'ConfigProfile', **kwargs):
        """从配置档案创建 Endpoint

        Args:
            profile: 源配置档案
            **kwargs: 覆盖参数（weight, priority 等）
        """
        return cls(
            base_url=profile.base_url,
            api_key=profile.api_key,
            source_profile=profile.name,
            metadata={
                'source_description': profile.description,
                'imported_at': datetime.now().isoformat()
            },
            **kwargs
        )

    def display_info(self, show_full_key: bool = False):
        """显示信息"""
        status_icon = {
            'healthy': '✓',
            'degraded': '⚠',
            'unhealthy': '✗',
            'unknown': '?'
        }.get(self.health_status['status'], '?')

        enabled_icon = '✓' if self.enabled else '✗'

        api_key_display = (
            self.api_key if show_full_key
            else f"{self.api_key[:10]}...{self.api_key[-4:]}"
        )

        info = [
            f"ID: {self.id}",
            f"URL: {self.base_url}",
            f"Key: {api_key_display}",
            f"权重: {self.weight}",
            f"优先级: {self.priority}",
            f"启用: {enabled_icon}",
            f"健康: {status_icon}",
        ]

        if self.source_profile:
            info.append(f"来源: {self.source_profile}")

        return " | ".join(info)
```

---

### 2. CLI 命令实现

#### endpoint add 命令
```python
# fastcc/cli.py

@cli.group()
def endpoint():
    """Endpoint 管理命令"""
    pass

@endpoint.command('add')
@click.argument('config_name')
@click.option('--from-profile', '-f', help='直接指定要复用的配置名称')
@click.option('--auto', '-a', is_flag=True, help='自动模式，使用默认参数')
def endpoint_add(config_name, from_profile, auto):
    """为配置添加 Endpoint

    支持三种方式:
    1. 从现有配置复用 (推荐)
    2. 手动输入新配置
    3. 从厂商快速配置
    """
    try:
        config_manager = ConfigManager()

        # 检查目标配置是否存在
        target_profile = config_manager.get_profile(config_name)
        if not target_profile:
            print_status(f"配置 '{config_name}' 不存在", "error")
            return

        print_header(f"为配置 '{config_name}' 添加 Endpoint")

        # 如果指定了 --from-profile，直接使用
        if from_profile:
            source_profile = config_manager.get_profile(from_profile)
            if not source_profile:
                print_status(f"源配置 '{from_profile}' 不存在", "error")
                return
            endpoint = create_endpoint_from_profile(source_profile, auto)
        else:
            # 交互式选择添加方式
            endpoint = interactive_add_endpoint(config_manager)

        if endpoint:
            # 添加到目标配置
            if not hasattr(target_profile, 'endpoints'):
                target_profile.endpoints = []
            target_profile.endpoints.append(endpoint)

            # 保存配置
            config_manager.save_profile(target_profile)

            print_status(f"Endpoint 添加成功！ID: {endpoint.id}", "success")
            print(f"\n{endpoint.display_info()}")
        else:
            print_status("操作取消", "warning")

    except Exception as e:
        print_status(f"添加 Endpoint 失败: {e}", "error")


def interactive_add_endpoint(config_manager: ConfigManager) -> Optional[Endpoint]:
    """交互式添加 Endpoint"""

    print_step(1, 3, "选择添加方式")

    choices = [
        "从现有配置复用 (推荐)",
        "手动输入新配置",
        "从厂商快速配置"
    ]

    choice_index = select_from_list(
        choices,
        "选择添加方式",
        timeout=30
    )

    if choice_index < 0:
        return None

    # 方式 1: 从现有配置复用
    if choice_index == 0:
        return add_endpoint_from_existing(config_manager)

    # 方式 2: 手动输入
    elif choice_index == 1:
        return add_endpoint_manual()

    # 方式 3: 从厂商快速配置
    elif choice_index == 2:
        return add_endpoint_from_provider()

    return None


def add_endpoint_from_existing(config_manager: ConfigManager) -> Optional[Endpoint]:
    """从现有配置复用"""

    print_step(2, 3, "选择源配置")

    # 获取所有配置
    profiles = config_manager.list_profiles()
    if not profiles:
        print_status("暂无可用配置", "warning")
        return None

    # 构建配置列表
    profile_display = []
    for profile in profiles:
        # 显示配置名称、描述和 base_url
        display = f"{profile.name}"
        if profile.description:
            display += f" - {profile.description}"
        display += f" ({profile.base_url})"
        profile_display.append(display)

    # 用户选择
    selected_index = select_from_list(
        profile_display,
        "选择要复用的配置",
        timeout=30
    )

    if selected_index < 0:
        return None

    source_profile = profiles[selected_index]

    # 显示选中的配置信息
    print_separator()
    print_status(f"已选择配置: {source_profile.name}", "info")
    print(f"  BASE_URL: {source_profile.base_url}")
    print(f"  API_KEY: {source_profile.api_key[:10]}...{source_profile.api_key[-4:]}")
    print()

    # 询问是否修改
    modify_url = input("是否修改 BASE_URL? (y/N): ").strip().lower() in ['y', 'yes']
    base_url = source_profile.base_url
    if modify_url:
        new_url = input(f"请输入新的 BASE_URL (留空保持原值): ").strip()
        if new_url:
            base_url = new_url

    modify_key = input("是否修改 API_KEY? (y/N): ").strip().lower() in ['y', 'yes']
    api_key = source_profile.api_key
    if modify_key:
        new_key = input(f"请输入新的 API_KEY (留空保持原值): ").strip()
        if new_key:
            api_key = new_key

    print_step(3, 3, "设置 Endpoint 参数")

    # 设置参数
    weight = input("设置权重 (默认 100): ").strip()
    weight = int(weight) if weight else 100

    priority = input("设置优先级 (默认 1): ").strip()
    priority = int(priority) if priority else 1

    timeout = input("设置超时时间/秒 (默认 30): ").strip()
    timeout = int(timeout) if timeout else 30

    # 创建 Endpoint
    endpoint = Endpoint.from_profile(
        source_profile,
        base_url=base_url,
        api_key=api_key,
        weight=weight,
        priority=priority,
        timeout=timeout
    )

    return endpoint


def add_endpoint_manual() -> Optional[Endpoint]:
    """手动输入 Endpoint 配置"""

    print_step(2, 3, "输入 Endpoint 配置")

    try:
        base_url = input("请输入 BASE_URL: ").strip()
        if not base_url:
            print_status("BASE_URL 不能为空", "error")
            return None

        api_key = input("请输入 API_KEY: ").strip()
        if not api_key:
            print_status("API_KEY 不能为空", "error")
            return None

        print_step(3, 3, "设置 Endpoint 参数")

        weight = input("设置权重 (默认 100): ").strip()
        weight = int(weight) if weight else 100

        priority = input("设置优先级 (默认 1): ").strip()
        priority = int(priority) if priority else 1

        timeout = input("设置超时时间/秒 (默认 30): ").strip()
        timeout = int(timeout) if timeout else 30

        # 创建 Endpoint
        endpoint = Endpoint(
            base_url=base_url,
            api_key=api_key,
            weight=weight,
            priority=priority,
            timeout=timeout
        )

        return endpoint

    except (ValueError, KeyboardInterrupt):
        print_status("操作取消", "warning")
        return None


def add_endpoint_from_provider() -> Optional[Endpoint]:
    """从厂商快速配置创建 Endpoint"""

    print_status("此功能将集成 'qcc fc' 厂商快速配置", "info")
    print("敬请期待...")
    return None


def create_endpoint_from_profile(
    source_profile: ConfigProfile,
    auto: bool = False
) -> Endpoint:
    """从配置档案创建 Endpoint（命令行模式）"""

    if auto:
        # 自动模式，使用默认参数
        return Endpoint.from_profile(source_profile)
    else:
        # 交互式设置参数
        print(f"从配置 '{source_profile.name}' 创建 Endpoint")

        weight = input("设置权重 (默认 100): ").strip()
        weight = int(weight) if weight else 100

        priority = input("设置优先级 (默认 1): ").strip()
        priority = int(priority) if priority else 1

        return Endpoint.from_profile(
            source_profile,
            weight=weight,
            priority=priority
        )
```

#### endpoint list 命令
```python
@endpoint.command('list')
@click.argument('config_name')
@click.option('--verbose', '-v', is_flag=True, help='显示详细信息')
def endpoint_list(config_name, verbose):
    """列出配置的所有 Endpoint"""
    try:
        config_manager = ConfigManager()
        profile = config_manager.get_profile(config_name)

        if not profile:
            print_status(f"配置 '{config_name}' 不存在", "error")
            return

        if not hasattr(profile, 'endpoints') or not profile.endpoints:
            print_status(f"配置 '{config_name}' 暂无 Endpoint", "warning")
            return

        print_header(f"{config_name} 的 Endpoint 列表")

        for i, ep in enumerate(profile.endpoints, 1):
            print(f"\n{i}. {ep.display_info(show_full_key=verbose)}")

            if verbose:
                # 显示健康状态详情
                health = ep.health_status
                print(f"   健康状态: {health['status']}")
                print(f"   成功率: {health['success_rate']:.1f}%")
                print(f"   平均响应时间: {health['avg_response_time']}ms")
                print(f"   总请求数: {health['total_requests']}")
                print(f"   失败请求数: {health['failed_requests']}")

        print()
        print(f"共 {len(profile.endpoints)} 个 Endpoint")

    except Exception as e:
        print_status(f"列出 Endpoint 失败: {e}", "error")
```

#### endpoint remove 命令
```python
@endpoint.command('remove')
@click.argument('config_name')
@click.argument('endpoint_id', required=False)
def endpoint_remove(config_name, endpoint_id):
    """删除 Endpoint"""
    try:
        config_manager = ConfigManager()
        profile = config_manager.get_profile(config_name)

        if not profile:
            print_status(f"配置 '{config_name}' 不存在", "error")
            return

        if not hasattr(profile, 'endpoints') or not profile.endpoints:
            print_status(f"配置 '{config_name}' 暂无 Endpoint", "warning")
            return

        # 如果没有指定 endpoint_id，交互式选择
        if not endpoint_id:
            print_header(f"选择要删除的 Endpoint")

            endpoint_display = [ep.display_info() for ep in profile.endpoints]
            selected_index = select_from_list(
                endpoint_display,
                "选择要删除的 Endpoint",
                timeout=30
            )

            if selected_index < 0:
                print_status("操作取消", "warning")
                return

            selected_endpoint = profile.endpoints[selected_index]
        else:
            # 根据 ID 查找
            selected_endpoint = None
            for ep in profile.endpoints:
                if ep.id == endpoint_id:
                    selected_endpoint = ep
                    break

            if not selected_endpoint:
                print_status(f"Endpoint '{endpoint_id}' 不存在", "error")
                return

        # 确认删除
        print_separator()
        print_status(f"即将删除 Endpoint: {selected_endpoint.id}", "warning")
        print(f"{selected_endpoint.display_info()}")
        print()

        if not confirm_action("确认删除？", default=False):
            print_status("操作取消", "info")
            return

        # 删除
        profile.endpoints.remove(selected_endpoint)
        config_manager.save_profile(profile)

        print_status(f"Endpoint '{selected_endpoint.id}' 已删除", "success")

    except Exception as e:
        print_status(f"删除 Endpoint 失败: {e}", "error")
```

---

### 3. ConfigManager 扩展

```python
# fastcc/core/config.py

class ConfigManager:
    """配置管理器 - 扩展支持 Endpoint 管理"""

    def save_profile(self, profile: ConfigProfile):
        """保存配置档案（支持 endpoints）"""
        # 将 profile 转换为字典
        profile_data = profile.to_dict()

        # 更新到 profiles 列表
        existing = False
        for i, p in enumerate(self.profiles):
            if p['name'] == profile.name:
                self.profiles[i] = profile_data
                existing = True
                break

        if not existing:
            self.profiles.append(profile_data)

        # 保存到本地缓存
        self.save_cache()

        # 同步到云端
        if self.storage_backend and self.settings.get('auto_sync', True):
            self.sync_to_cloud()

    def get_all_endpoints(self) -> List[Endpoint]:
        """获取所有配置的所有 Endpoint"""
        all_endpoints = []

        for profile_data in self.profiles:
            if 'endpoints' in profile_data and profile_data['endpoints']:
                for ep_data in profile_data['endpoints']:
                    all_endpoints.append(Endpoint.from_dict(ep_data))

        return all_endpoints

    def find_endpoints_by_url(self, base_url: str) -> List[Endpoint]:
        """根据 base_url 查找 Endpoint"""
        result = []
        for ep in self.get_all_endpoints():
            if ep.base_url == base_url:
                result.append(ep)
        return result

    def deduplicate_endpoints(self, profile: ConfigProfile):
        """去重 Endpoint（根据 base_url + api_key）"""
        if not hasattr(profile, 'endpoints') or not profile.endpoints:
            return

        seen = set()
        unique_endpoints = []

        for ep in profile.endpoints:
            key = (ep.base_url, ep.api_key)
            if key not in seen:
                seen.add(key)
                unique_endpoints.append(ep)

        profile.endpoints = unique_endpoints
```

---

## 🧪 测试用例

### 单元测试
```python
# tests/test_endpoint_reuse.py

import pytest
from fastcc.core.endpoint import Endpoint
from fastcc.core.config import ConfigProfile, ConfigManager

def test_endpoint_from_profile():
    """测试从配置档案创建 Endpoint"""
    profile = ConfigProfile()
    profile.name = "test"
    profile.base_url = "https://api.test.com"
    profile.api_key = "sk-test-123"
    profile.description = "Test profile"

    endpoint = Endpoint.from_profile(profile, weight=50, priority=2)

    assert endpoint.base_url == profile.base_url
    assert endpoint.api_key == profile.api_key
    assert endpoint.source_profile == profile.name
    assert endpoint.weight == 50
    assert endpoint.priority == 2


def test_endpoint_to_dict():
    """测试 Endpoint 序列化"""
    endpoint = Endpoint(
        base_url="https://api.test.com",
        api_key="sk-test-123",
        weight=100,
        priority=1
    )

    data = endpoint.to_dict()

    assert data['base_url'] == "https://api.test.com"
    assert data['api_key'] == "sk-test-123"
    assert data['weight'] == 100
    assert data['priority'] == 1
    assert 'id' in data
    assert 'health_status' in data


def test_endpoint_from_dict():
    """测试 Endpoint 反序列化"""
    data = {
        'id': 'test-id',
        'base_url': "https://api.test.com",
        'api_key': "sk-test-123",
        'weight': 100,
        'priority': 1,
        'enabled': True,
        'source_profile': 'original'
    }

    endpoint = Endpoint.from_dict(data)

    assert endpoint.id == 'test-id'
    assert endpoint.base_url == data['base_url']
    assert endpoint.api_key == data['api_key']
    assert endpoint.source_profile == 'original'


def test_config_manager_save_profile_with_endpoints():
    """测试保存包含 endpoints 的配置"""
    manager = ConfigManager()

    profile = ConfigProfile()
    profile.name = "test-proxy"
    profile.description = "Test proxy config"
    profile.endpoints = [
        Endpoint(
            base_url="https://api1.test.com",
            api_key="sk-test-1",
            weight=100
        ),
        Endpoint(
            base_url="https://api2.test.com",
            api_key="sk-test-2",
            weight=50
        )
    ]

    manager.save_profile(profile)

    # 验证保存成功
    loaded = manager.get_profile("test-proxy")
    assert loaded is not None
    assert len(loaded.endpoints) == 2


def test_deduplicate_endpoints():
    """测试 Endpoint 去重"""
    manager = ConfigManager()

    profile = ConfigProfile()
    profile.name = "test"
    profile.endpoints = [
        Endpoint(base_url="https://api.test.com", api_key="sk-test-1"),
        Endpoint(base_url="https://api.test.com", api_key="sk-test-1"),  # 重复
        Endpoint(base_url="https://api.test.com", api_key="sk-test-2"),
    ]

    manager.deduplicate_endpoints(profile)

    assert len(profile.endpoints) == 2
```

---

## 📚 使用文档

### 快速开始

#### 1. 从现有配置复用 (推荐)

```bash
# 场景：已有多个配置，想整合到一个代理配置
qcc list
# 输出:
#   work - 工作配置
#   personal - 个人配置
#   backup - 备份配置

# 创建代理配置
qcc add my-proxy --description "多 API Key 代理"

# 方法 1: 交互式添加
qcc endpoint add my-proxy
# 选择: 从现有配置复用
# 选择配置: work
# 设置权重: 100, 优先级: 1

# 方法 2: 命令行直接指定
qcc endpoint add my-proxy --from-profile work
# 使用默认参数

# 方法 3: 命令行指定 + 自动模式
qcc endpoint add my-proxy -f personal --auto
```

#### 2. 查看 Endpoint 列表

```bash
# 简单查看
qcc endpoint list my-proxy

# 详细查看（包含健康状态）
qcc endpoint list my-proxy --verbose
```

#### 3. 管理 Endpoint

```bash
# 启用/禁用
qcc endpoint enable my-proxy endpoint-1
qcc endpoint disable my-proxy endpoint-2

# 删除
qcc endpoint remove my-proxy endpoint-3

# 测试连通性
qcc endpoint test my-proxy endpoint-1
```

---

## 🔍 实现要点

### 1. 向后兼容性

保持与现有单 endpoint 配置的兼容：

```python
# 旧配置格式（仍然支持）
{
    "name": "old-config",
    "base_url": "https://api.anthropic.com",
    "api_key": "sk-ant-xxxxx"
}

# 新配置格式（推荐）
{
    "name": "new-config",
    "endpoints": [
        {
            "id": "ep-1",
            "base_url": "https://api.anthropic.com",
            "api_key": "sk-ant-xxxxx",
            "weight": 100
        }
    ]
}

# 混合模式（自动迁移）
# 如果 base_url 和 api_key 存在但没有 endpoints
# 自动创建一个 endpoint
```

### 2. 数据迁移

为现有配置自动创建 endpoint：

```python
def migrate_profile_to_endpoints(profile: ConfigProfile):
    """迁移旧配置到 endpoints 模式"""
    if profile.base_url and profile.api_key:
        if not hasattr(profile, 'endpoints') or not profile.endpoints:
            # 创建默认 endpoint
            profile.endpoints = [
                Endpoint(
                    base_url=profile.base_url,
                    api_key=profile.api_key,
                    weight=100,
                    priority=1
                )
            ]
```

### 3. 安全性考虑

- API Key 显示时默认脱敏
- 配置文件权限: 600 (仅所有者可读写)
- 云端存储加密
- 支持 `--verbose` 选项显示完整 Key（需要确认）

### 4. 用户体验优化

- 提供三种添加方式（复用/手动/厂商）
- 默认推荐"从现有配置复用"
- 支持命令行快捷参数（`-f`, `--auto`）
- 交互式提示清晰易懂
- 支持超时自动选择默认值

---

## 🎯 里程碑

### Phase 1: 基础实现 (3-5 天)
- [ ] Endpoint 数据模型
- [ ] ConfigProfile 扩展
- [ ] endpoint add 命令（复用功能）
- [ ] endpoint list 命令
- [ ] 单元测试

### Phase 2: 完善功能 (2-3 天)
- [ ] endpoint remove 命令
- [ ] endpoint enable/disable 命令
- [ ] 数据迁移逻辑
- [ ] 向后兼容性测试

### Phase 3: 优化体验 (2-3 天)
- [ ] 命令行快捷参数
- [ ] 交互式 UI 优化
- [ ] 错误处理和提示
- [ ] 使用文档和示例

---

## 📝 总结

"从现有配置复用" 功能通过以下设计实现：

1. **数据模型**: 新增 `Endpoint` 类，支持从 `ConfigProfile` 创建
2. **CLI 命令**: `qcc endpoint add` 提供三种添加方式，默认推荐复用
3. **交互体验**: 清晰的步骤提示，支持快捷参数
4. **向后兼容**: 保持与现有单 endpoint 配置的兼容
5. **安全性**: API Key 脱敏显示，配置文件加密存储

这个功能将大大提高用户配置代理的效率，特别是在整合多个 API Key 时。

---

**文档版本**: v1.0
**最后更新**: 2025-10-16
**作者**: QCC Development Team
