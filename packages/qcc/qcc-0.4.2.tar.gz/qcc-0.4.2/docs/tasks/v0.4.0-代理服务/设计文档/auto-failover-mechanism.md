# 自动故障转移机制 - 技术实现方案

## 📋 功能概述

实现智能的配置优先级管理和自动故障转移机制：当主要配置的所有 endpoint 都不可用时，系统自动切换到次要配置，确保服务持续可用。

**版本**: v1.0
**创建日期**: 2025-10-16
**相关文档**: claude-code-proxy-development-plan.md

---

## 🎯 核心需求

### 使用场景

**场景 1: 主配置全部失败，自动切换**
```
主配置 (production) - 所有 endpoint 失败
  ↓ 自动检测到故障
  ↓ 触发切换逻辑
次要配置 (backup) - 接管流量
  ↓ 继续提供服务
  ↓ 后台监控主配置恢复
主配置恢复 → 自动切回（可选）
```

**场景 2: 多层级故障转移**
```
Primary (主配置组)
  ├─ endpoint-1 ✗ 失败
  ├─ endpoint-2 ✗ 失败
  └─ endpoint-3 ✗ 失败
     ↓ 全部失败，切换
Secondary (次要配置组)
  ├─ endpoint-1 ✓ 可用
  └─ endpoint-2 ✓ 可用
     ↓ 继续服务
     ↓ 次要配置也失败
Fallback (兜底配置)
  └─ endpoint-1 ✓ 限流服务
```

**场景 3: 智能恢复**
```
当前使用: Secondary
主配置恢复检测:
  ├─ 连续 3 次健康检查通过
  ├─ 冷却期 (5分钟) 已过
  └─ 触发自动恢复
     ↓
切换回 Primary (可选)
```

---

## 🏗️ 系统架构

### 1. 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                  Claude Code Request                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   QCC Proxy Server                           │
│                                                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │          Request Router (路由器)                   │    │
│  │  - 接收请求                                         │    │
│  │  - 查询当前活跃配置                                 │    │
│  │  - 转发到 Endpoint Selector                        │    │
│  └─────────────────────┬──────────────────────────────┘    │
│                        │                                     │
│  ┌─────────────────────┴──────────────────────────────┐    │
│  │      Failover Manager (故障转移管理器)             │    │
│  │  - 监控配置组健康状态                               │    │
│  │  - 触发自动切换                                     │    │
│  │  - 管理切换策略                                     │    │
│  │  - 记录切换历史                                     │    │
│  └─────────────────────┬──────────────────────────────┘    │
│                        │                                     │
│  ┌─────────────────────┴──────────────────────────────┐    │
│  │      Priority Manager (优先级管理器)               │    │
│  │  - 管理配置优先级                                   │    │
│  │  - 获取当前活跃配置                                 │    │
│  │  - 切换配置组                                       │    │
│  └─────────────────────┬──────────────────────────────┘    │
│                        │                                     │
│  ┌─────────────────────┴──────────────────────────────┐    │
│  │      Health Monitor (健康监控器)                   │    │
│  │  - 定时检查所有配置                                 │    │
│  │  - 更新健康状态                                     │    │
│  │  - 触发故障事件                                     │    │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
┌────────────────┐ ┌────────────┐ ┌─────────────┐
│    Primary     │ │ Secondary  │ │  Fallback   │
│  Config Group  │ │   Config   │ │   Config    │
│  (endpoint-1)  │ │ (endpoint) │ │ (endpoint)  │
│  (endpoint-2)  │ │            │ │             │
└────────────────┘ └────────────┘ └─────────────┘
         │               │               │
         └───────────────┴───────────────┘
                         ↓
           Anthropic API Providers
```

---

## 💾 数据结构设计

### 1. 配置优先级模型

```python
# fastcc/core/priority.py

from enum import Enum
from typing import List, Optional, Dict
from datetime import datetime, timedelta

class ConfigPriority(Enum):
    """配置优先级枚举"""
    PRIMARY = "primary"      # 主配置
    SECONDARY = "secondary"  # 次要配置
    FALLBACK = "fallback"    # 兜底配置
    DISABLED = "disabled"    # 禁用

class PriorityGroup:
    """优先级配置组"""

    def __init__(
        self,
        priority: ConfigPriority,
        config_names: List[str],
        enabled: bool = True
    ):
        self.priority = priority
        self.config_names = config_names  # 该优先级下的配置列表
        self.enabled = enabled
        self.health_status = "unknown"  # unknown, healthy, degraded, unhealthy
        self.last_check = None
        self.active_config = None  # 当前活跃的配置名称

    def to_dict(self):
        return {
            'priority': self.priority.value,
            'config_names': self.config_names,
            'enabled': self.enabled,
            'health_status': self.health_status,
            'last_check': self.last_check,
            'active_config': self.active_config
        }

class FailoverPolicy:
    """故障转移策略"""

    def __init__(self):
        # 切换策略
        self.auto_failover_enabled = True  # 是否启用自动故障转移
        self.auto_recovery_enabled = False  # 是否启用自动恢复

        # 切换阈值
        self.failure_threshold = 3  # 连续失败多少次触发切换
        self.success_threshold = 3  # 连续成功多少次触发恢复

        # 时间控制
        self.check_interval = 60  # 健康检查间隔（秒）
        self.cooldown_period = 300  # 冷却期（秒），防止频繁切换
        self.recovery_delay = 600  # 恢复延迟（秒），主配置恢复后等待时间

        # 通知
        self.notify_on_failover = True  # 切换时是否通知
        self.notify_on_recovery = True  # 恢复时是否通知

        # 限制
        self.max_failovers_per_hour = 10  # 每小时最大切换次数

    def to_dict(self):
        return {
            'auto_failover_enabled': self.auto_failover_enabled,
            'auto_recovery_enabled': self.auto_recovery_enabled,
            'failure_threshold': self.failure_threshold,
            'success_threshold': self.success_threshold,
            'check_interval': self.check_interval,
            'cooldown_period': self.cooldown_period,
            'recovery_delay': self.recovery_delay,
            'notify_on_failover': self.notify_on_failover,
            'notify_on_recovery': self.notify_on_recovery,
            'max_failovers_per_hour': self.max_failovers_per_hour
        }

class FailoverEvent:
    """故障转移事件记录"""

    def __init__(
        self,
        event_type: str,  # failover, recovery, manual_switch
        from_config: str,
        to_config: str,
        reason: str,
        timestamp: Optional[str] = None
    ):
        self.event_id = str(uuid.uuid4())[:8]
        self.event_type = event_type
        self.from_config = from_config
        self.to_config = to_config
        self.reason = reason
        self.timestamp = timestamp or datetime.now().isoformat()
        self.success = True

    def to_dict(self):
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'from_config': self.from_config,
            'to_config': self.to_config,
            'reason': self.reason,
            'timestamp': self.timestamp,
            'success': self.success
        }
```

### 2. 配置健康状态

```python
class ConfigHealth:
    """配置健康状态"""

    def __init__(self, config_name: str):
        self.config_name = config_name
        self.status = "unknown"  # healthy, degraded, unhealthy, unknown
        self.healthy_endpoints = 0
        self.total_endpoints = 0
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_check = None
        self.last_failure = None
        self.last_success = None

    @property
    def health_percentage(self) -> float:
        """健康度百分比"""
        if self.total_endpoints == 0:
            return 0.0
        return (self.healthy_endpoints / self.total_endpoints) * 100

    @property
    def is_healthy(self) -> bool:
        """是否健康（至少有一个 endpoint 可用）"""
        return self.healthy_endpoints > 0

    @property
    def is_fully_healthy(self) -> bool:
        """是否完全健康（所有 endpoint 都可用）"""
        return self.healthy_endpoints == self.total_endpoints > 0

    def to_dict(self):
        return {
            'config_name': self.config_name,
            'status': self.status,
            'healthy_endpoints': self.healthy_endpoints,
            'total_endpoints': self.total_endpoints,
            'health_percentage': self.health_percentage,
            'consecutive_failures': self.consecutive_failures,
            'consecutive_successes': self.consecutive_successes,
            'last_check': self.last_check,
            'last_failure': self.last_failure,
            'last_success': self.last_success
        }
```

---

## 🔧 核心模块实现

### 1. Priority Manager (优先级管理器)

```python
# fastcc/core/priority_manager.py

from typing import List, Optional, Dict
from datetime import datetime
import json
from pathlib import Path

class PriorityManager:
    """配置优先级管理器"""

    def __init__(self, config_path: str = "~/.qcc/priority_config.json"):
        self.config_path = Path(config_path).expanduser()
        self.priority_groups: Dict[str, PriorityGroup] = {}
        self.current_active_priority = ConfigPriority.PRIMARY
        self.current_active_config = None
        self.load_config()

    def load_config(self):
        """加载优先级配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                self._parse_config(data)

    def save_config(self):
        """保存优先级配置"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'priority_groups': {
                k: v.to_dict() for k, v in self.priority_groups.items()
            },
            'current_active_priority': self.current_active_priority.value,
            'current_active_config': self.current_active_config
        }

        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def set_config_priority(
        self,
        config_name: str,
        priority: ConfigPriority
    ):
        """设置配置的优先级"""
        # 从所有组中移除该配置
        for group in self.priority_groups.values():
            if config_name in group.config_names:
                group.config_names.remove(config_name)

        # 添加到新的优先级组
        priority_key = priority.value
        if priority_key not in self.priority_groups:
            self.priority_groups[priority_key] = PriorityGroup(
                priority=priority,
                config_names=[]
            )

        self.priority_groups[priority_key].config_names.append(config_name)
        self.save_config()

    def get_config_priority(self, config_name: str) -> Optional[ConfigPriority]:
        """获取配置的优先级"""
        for group in self.priority_groups.values():
            if config_name in group.config_names:
                return group.priority
        return None

    def get_active_config(self) -> Optional[str]:
        """获取当前活跃的配置"""
        return self.current_active_config

    def get_next_priority_group(
        self,
        current_priority: ConfigPriority
    ) -> Optional[PriorityGroup]:
        """获取下一个优先级组（用于故障转移）"""
        priority_order = [
            ConfigPriority.PRIMARY,
            ConfigPriority.SECONDARY,
            ConfigPriority.FALLBACK
        ]

        try:
            current_index = priority_order.index(current_priority)
            if current_index < len(priority_order) - 1:
                next_priority = priority_order[current_index + 1]
                return self.priority_groups.get(next_priority.value)
        except ValueError:
            pass

        return None

    def get_priority_group(
        self,
        priority: ConfigPriority
    ) -> Optional[PriorityGroup]:
        """获取指定优先级的配置组"""
        return self.priority_groups.get(priority.value)

    def list_priority_groups(self) -> List[PriorityGroup]:
        """列出所有优先级组"""
        return list(self.priority_groups.values())
```

### 2. Failover Manager (故障转移管理器)

```python
# fastcc/proxy/failover_manager.py

import asyncio
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from collections import deque

class FailoverManager:
    """故障转移管理器"""

    def __init__(
        self,
        priority_manager: PriorityManager,
        config_manager: ConfigManager,
        health_monitor: 'HealthMonitor'
    ):
        self.priority_manager = priority_manager
        self.config_manager = config_manager
        self.health_monitor = health_monitor

        self.policy = FailoverPolicy()
        self.event_history: deque = deque(maxlen=1000)  # 最多保存 1000 条记录

        self.last_failover_time = None
        self.failover_count_hourly = deque(maxlen=100)

        self.running = False
        self.monitor_task = None

    async def start(self):
        """启动故障转移监控"""
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        print(f"✓ 故障转移监控已启动 (检查间隔: {self.policy.check_interval}秒)")

    async def stop(self):
        """停止故障转移监控"""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        print("✓ 故障转移监控已停止")

    async def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                await self._check_and_failover()
                await asyncio.sleep(self.policy.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"✗ 故障转移监控错误: {e}")
                await asyncio.sleep(self.policy.check_interval)

    async def _check_and_failover(self):
        """检查并执行故障转移"""
        if not self.policy.auto_failover_enabled:
            return

        # 获取当前活跃配置
        current_config_name = self.priority_manager.get_active_config()
        if not current_config_name:
            # 如果没有活跃配置，尝试激活主配置组
            await self._activate_primary_group()
            return

        # 检查当前配置的健康状态
        health = await self.health_monitor.get_config_health(current_config_name)

        if health and not health.is_healthy:
            # 当前配置不健康
            health.consecutive_failures += 1

            if health.consecutive_failures >= self.policy.failure_threshold:
                # 达到故障阈值，触发故障转移
                await self._trigger_failover(
                    current_config_name,
                    f"连续 {health.consecutive_failures} 次健康检查失败"
                )
        else:
            # 当前配置健康，重置失败计数
            if health:
                health.consecutive_failures = 0
                health.consecutive_successes += 1

        # 检查是否需要恢复到更高优先级的配置
        if self.policy.auto_recovery_enabled:
            await self._check_recovery()

    async def _trigger_failover(self, from_config: str, reason: str):
        """触发故障转移"""

        # 检查冷却期
        if not self._can_failover():
            print(f"⚠ 故障转移冷却期内，跳过切换")
            return

        # 检查每小时切换次数限制
        if not self._check_failover_rate_limit():
            print(f"⚠ 故障转移次数达到限制，跳过切换")
            return

        # 获取当前配置的优先级
        current_priority = self.priority_manager.get_config_priority(from_config)
        if not current_priority:
            print(f"✗ 配置 '{from_config}' 没有设置优先级")
            return

        # 获取下一个优先级组
        next_group = self.priority_manager.get_next_priority_group(current_priority)
        if not next_group or not next_group.config_names:
            print(f"✗ 没有可用的下一级配置，故障转移失败")
            self._notify_no_fallback(from_config, reason)
            return

        # 查找下一个健康的配置
        target_config = await self._find_healthy_config(next_group.config_names)
        if not target_config:
            print(f"✗ 下一级配置组中没有健康的配置")
            # 继续尝试更低优先级的配置
            lower_group = self.priority_manager.get_next_priority_group(next_group.priority)
            if lower_group and lower_group.config_names:
                target_config = await self._find_healthy_config(lower_group.config_names)

        if target_config:
            # 执行切换
            await self._switch_config(from_config, target_config, reason, "failover")
        else:
            print(f"✗ 所有备用配置都不可用，无法完成故障转移")
            self._notify_all_configs_down(from_config)

    async def _switch_config(
        self,
        from_config: str,
        to_config: str,
        reason: str,
        event_type: str = "failover"
    ):
        """执行配置切换"""

        print(f"\n{'='*60}")
        print(f"🔄 故障转移: {from_config} → {to_config}")
        print(f"原因: {reason}")
        print(f"{'='*60}\n")

        # 应用新配置
        if self.config_manager.apply_profile(to_config):
            # 更新活跃配置
            self.priority_manager.current_active_config = to_config
            self.priority_manager.save_config()

            # 记录事件
            event = FailoverEvent(
                event_type=event_type,
                from_config=from_config,
                to_config=to_config,
                reason=reason
            )
            self._record_event(event)

            # 更新故障转移时间
            self.last_failover_time = datetime.now()
            self.failover_count_hourly.append(datetime.now())

            # 发送通知
            if self.policy.notify_on_failover:
                self._notify_failover(event)

            print(f"✓ 故障转移完成，当前使用配置: {to_config}")
        else:
            print(f"✗ 应用配置 '{to_config}' 失败")

    async def _check_recovery(self):
        """检查是否可以恢复到更高优先级的配置"""

        current_config = self.priority_manager.get_active_config()
        if not current_config:
            return

        current_priority = self.priority_manager.get_config_priority(current_config)
        if not current_priority or current_priority == ConfigPriority.PRIMARY:
            return  # 已经是最高优先级，无需恢复

        # 检查更高优先级的配置组
        if current_priority == ConfigPriority.SECONDARY:
            primary_group = self.priority_manager.get_priority_group(ConfigPriority.PRIMARY)
        elif current_priority == ConfigPriority.FALLBACK:
            # 先尝试 Secondary，再尝试 Primary
            primary_group = self.priority_manager.get_priority_group(ConfigPriority.SECONDARY)
            if not primary_group:
                primary_group = self.priority_manager.get_priority_group(ConfigPriority.PRIMARY)
        else:
            return

        if not primary_group or not primary_group.config_names:
            return

        # 检查更高优先级的配置是否已恢复
        for config_name in primary_group.config_names:
            health = await self.health_monitor.get_config_health(config_name)
            if health and health.is_healthy:
                health.consecutive_successes += 1

                if health.consecutive_successes >= self.policy.success_threshold:
                    # 检查恢复延迟
                    if self._can_recover(health):
                        await self._trigger_recovery(current_config, config_name)
                        break

    async def _trigger_recovery(self, from_config: str, to_config: str):
        """触发恢复到更高优先级配置"""

        reason = f"主配置已恢复健康 (连续 {self.policy.success_threshold} 次检查通过)"
        await self._switch_config(from_config, to_config, reason, "recovery")

        if self.policy.notify_on_recovery:
            print(f"✓ 已恢复到主配置: {to_config}")

    async def _find_healthy_config(self, config_names: List[str]) -> Optional[str]:
        """在配置列表中查找健康的配置"""
        for config_name in config_names:
            health = await self.health_monitor.get_config_health(config_name)
            if health and health.is_healthy:
                return config_name
        return None

    async def _activate_primary_group(self):
        """激活主配置组"""
        primary_group = self.priority_manager.get_priority_group(ConfigPriority.PRIMARY)
        if primary_group and primary_group.config_names:
            target_config = await self._find_healthy_config(primary_group.config_names)
            if target_config:
                self.priority_manager.current_active_config = target_config
                self.priority_manager.save_config()
                print(f"✓ 已激活主配置: {target_config}")

    def _can_failover(self) -> bool:
        """检查是否可以执行故障转移（冷却期检查）"""
        if not self.last_failover_time:
            return True

        elapsed = (datetime.now() - self.last_failover_time).total_seconds()
        return elapsed >= self.policy.cooldown_period

    def _can_recover(self, health: ConfigHealth) -> bool:
        """检查是否可以执行恢复"""
        if not health.last_failure:
            return True

        last_failure_time = datetime.fromisoformat(health.last_failure)
        elapsed = (datetime.now() - last_failure_time).total_seconds()
        return elapsed >= self.policy.recovery_delay

    def _check_failover_rate_limit(self) -> bool:
        """检查故障转移频率限制"""
        # 清理 1 小时前的记录
        one_hour_ago = datetime.now() - timedelta(hours=1)
        while self.failover_count_hourly and self.failover_count_hourly[0] < one_hour_ago:
            self.failover_count_hourly.popleft()

        return len(self.failover_count_hourly) < self.policy.max_failovers_per_hour

    def _record_event(self, event: FailoverEvent):
        """记录故障转移事件"""
        self.event_history.append(event)

        # 持久化到文件
        event_file = Path("~/.qcc/failover_events.json").expanduser()
        event_file.parent.mkdir(parents=True, exist_ok=True)

        events_data = [e.to_dict() for e in self.event_history]
        with open(event_file, 'w') as f:
            json.dump(events_data, f, indent=2)

    def _notify_failover(self, event: FailoverEvent):
        """发送故障转移通知"""
        # 可以扩展为邮件、Slack、钉钉等通知方式
        print(f"\n📧 故障转移通知:")
        print(f"   类型: {event.event_type}")
        print(f"   从: {event.from_config}")
        print(f"   到: {event.to_config}")
        print(f"   原因: {event.reason}")
        print(f"   时间: {event.timestamp}\n")

    def _notify_no_fallback(self, from_config: str, reason: str):
        """通知没有可用的备用配置"""
        print(f"\n⚠️  严重警告: 没有可用的备用配置！")
        print(f"   失败配置: {from_config}")
        print(f"   原因: {reason}")
        print(f"   建议: 请立即检查所有配置状态\n")

    def _notify_all_configs_down(self, from_config: str):
        """通知所有配置都不可用"""
        print(f"\n🚨 紧急警告: 所有配置都不可用！")
        print(f"   当前配置: {from_config}")
        print(f"   状态: 服务将中断")
        print(f"   建议: 请立即检查网络和 API Key 状态\n")

    def get_event_history(self, limit: int = 100) -> List[FailoverEvent]:
        """获取故障转移历史"""
        return list(self.event_history)[-limit:]

    def manual_switch(self, to_config: str, reason: str = "手动切换"):
        """手动切换配置"""
        current_config = self.priority_manager.get_active_config()
        if current_config == to_config:
            print(f"当前已经是配置 '{to_config}'")
            return

        asyncio.create_task(
            self._switch_config(current_config or "none", to_config, reason, "manual")
        )
```

---

## 🖥️ CLI 命令实现

### priority 命令组

```python
# fastcc/cli.py

@cli.group()
def priority():
    """优先级和故障转移管理"""
    pass

@priority.command('set')
@click.argument('config_name')
@click.argument('priority_level', type=click.Choice(['primary', 'secondary', 'fallback']))
def priority_set(config_name, priority_level):
    """设置配置的优先级

    示例:
        qcc priority set production primary
        qcc priority set backup secondary
        qcc priority set emergency fallback
    """
    try:
        config_manager = ConfigManager()
        priority_manager = PriorityManager()

        # 检查配置是否存在
        if not config_manager.get_profile(config_name):
            print_status(f"配置 '{config_name}' 不存在", "error")
            return

        # 设置优先级
        priority = ConfigPriority(priority_level)
        priority_manager.set_config_priority(config_name, priority)

        print_status(
            f"已设置 '{config_name}' 为 {priority_level} 配置",
            "success"
        )

    except Exception as e:
        print_status(f"设置优先级失败: {e}", "error")

@priority.command('list')
def priority_list():
    """查看所有配置的优先级"""
    try:
        priority_manager = PriorityManager()

        print_header("配置优先级列表")

        for group in priority_manager.list_priority_groups():
            priority_icon = {
                'primary': '⭐',
                'secondary': '🔵',
                'fallback': '🟡'
            }.get(group.priority.value, '⚪')

            enabled_status = '✓' if group.enabled else '✗'

            print(f"\n{priority_icon} {group.priority.value.upper()} [{enabled_status}]")

            if group.config_names:
                for config_name in group.config_names:
                    is_active = (config_name == priority_manager.current_active_config)
                    active_marker = " (当前活跃)" if is_active else ""
                    print(f"  • {config_name}{active_marker}")
            else:
                print(f"  (暂无配置)")

        print()
        if priority_manager.current_active_config:
            print(f"当前活跃配置: {priority_manager.current_active_config}")

    except Exception as e:
        print_status(f"查看优先级失败: {e}", "error")

@priority.command('policy')
@click.option('--auto-failover/--no-auto-failover', default=None, help='是否启用自动故障转移')
@click.option('--auto-recovery/--no-auto-recovery', default=None, help='是否启用自动恢复')
@click.option('--failure-threshold', type=int, help='故障阈值（次数）')
@click.option('--cooldown', type=int, help='冷却期（秒）')
def priority_policy(auto_failover, auto_recovery, failure_threshold, cooldown):
    """配置故障转移策略

    示例:
        qcc priority policy --auto-failover --failure-threshold 3
        qcc priority policy --auto-recovery --cooldown 300
    """
    try:
        # TODO: 加载和更新 FailoverPolicy
        policy = FailoverPolicy()

        if auto_failover is not None:
            policy.auto_failover_enabled = auto_failover
        if auto_recovery is not None:
            policy.auto_recovery_enabled = auto_recovery
        if failure_threshold is not None:
            policy.failure_threshold = failure_threshold
        if cooldown is not None:
            policy.cooldown_period = cooldown

        # 保存策略
        # ... 保存逻辑

        print_status("故障转移策略已更新", "success")
        print(f"  自动故障转移: {'✓' if policy.auto_failover_enabled else '✗'}")
        print(f"  自动恢复: {'✓' if policy.auto_recovery_enabled else '✗'}")
        print(f"  故障阈值: {policy.failure_threshold} 次")
        print(f"  冷却期: {policy.cooldown_period} 秒")

    except Exception as e:
        print_status(f"配置策略失败: {e}", "error")

@priority.command('switch')
@click.argument('to_config')
@click.option('--reason', '-r', default='手动切换', help='切换原因')
def priority_switch(to_config, reason):
    """手动切换到指定配置

    示例:
        qcc priority switch backup --reason "主配置维护"
    """
    try:
        config_manager = ConfigManager()
        priority_manager = PriorityManager()

        # 检查目标配置是否存在
        if not config_manager.get_profile(to_config):
            print_status(f"配置 '{to_config}' 不存在", "error")
            return

        current_config = priority_manager.get_active_config()

        if current_config == to_config:
            print_status(f"当前已经是配置 '{to_config}'", "info")
            return

        # 执行切换
        print_status(f"切换配置: {current_config} → {to_config}", "loading")

        if config_manager.apply_profile(to_config):
            priority_manager.current_active_config = to_config
            priority_manager.save_config()

            print_status(f"已切换到配置 '{to_config}'", "success")
            print(f"原因: {reason}")
        else:
            print_status(f"切换失败", "error")

    except Exception as e:
        print_status(f"手动切换失败: {e}", "error")

@priority.command('history')
@click.option('--limit', '-n', default=20, help='显示记录数量')
def priority_history(limit):
    """查看故障转移历史

    示例:
        qcc priority history
        qcc priority history --limit 50
    """
    try:
        # 加载历史记录
        event_file = Path("~/.qcc/failover_events.json").expanduser()
        if not event_file.exists():
            print_status("暂无故障转移历史", "info")
            return

        with open(event_file, 'r') as f:
            events_data = json.load(f)

        events = events_data[-limit:]

        print_header(f"故障转移历史 (最近 {len(events)} 条)")

        for event in reversed(events):
            event_type_icon = {
                'failover': '🔄',
                'recovery': '✅',
                'manual': '👤'
            }.get(event['event_type'], '📝')

            print(f"\n{event_type_icon} {event['event_type'].upper()}")
            print(f"   时间: {event['timestamp']}")
            print(f"   从: {event['from_config']}")
            print(f"   到: {event['to_config']}")
            print(f"   原因: {event['reason']}")

    except Exception as e:
        print_status(f"查看历史失败: {e}", "error")
```

---

## 📚 使用示例

### 场景 1: 配置三级故障转移

```bash
# 步骤 1: 创建三个配置
qcc add production --description "生产环境主配置"
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
qcc priority policy --auto-failover --auto-recovery --failure-threshold 3 --cooldown 300

# 步骤 5: 启动代理服务（自动启动故障转移监控）
qcc proxy start
# ✓ 代理服务器已启动: http://127.0.0.1:7860
# ✓ 故障转移监控已启动 (检查间隔: 60秒)
```

### 场景 2: 模拟故障转移

```bash
# 当 production 配置的所有 endpoint 都失败时:
#
# ============================================================
# 🔄 故障转移: production → backup
# 原因: 连续 3 次健康检查失败
# ============================================================
#
# ✓ 故障转移完成，当前使用配置: backup
#
# 📧 故障转移通知:
#    类型: failover
#    从: production
#    到: backup
#    原因: 连续 3 次健康检查失败
#    时间: 2025-10-16T14:30:00

# 查看当前状态
qcc priority list
# 输出:
#   ⭐ PRIMARY [✓]
#     • production
#
#   🔵 SECONDARY [✓]
#     • backup (当前活跃)  ← 已自动切换
#
#   🟡 FALLBACK [✓]
#     • emergency
```

### 场景 3: 手动切换配置

```bash
# 因维护需要，手动切换到备用配置
qcc priority switch backup --reason "主配置计划维护"
# ✓ 已切换到配置 'backup'
# 原因: 主配置计划维护

# 维护完成后切换回主配置
qcc priority switch production --reason "维护完成"
```

### 场景 4: 查看故障转移历史

```bash
qcc priority history --limit 10
# 输出:
#
# 🔄 FAILOVER
#    时间: 2025-10-16T14:30:00
#    从: production
#    到: backup
#    原因: 连续 3 次健康检查失败
#
# ✅ RECOVERY
#    时间: 2025-10-16T15:00:00
#    从: backup
#    到: production
#    原因: 主配置已恢复健康 (连续 3 次检查通过)
#
# 👤 MANUAL
#    时间: 2025-10-16T16:00:00
#    从: production
#    到: backup
#    原因: 主配置计划维护
```

---

## 🧪 测试用例

### 单元测试

```python
# tests/test_failover.py

import pytest
import asyncio
from fastcc.core.priority_manager import PriorityManager, ConfigPriority
from fastcc.proxy.failover_manager import FailoverManager

@pytest.mark.asyncio
async def test_automatic_failover():
    """测试自动故障转移"""
    # 设置三个配置
    priority_manager = PriorityManager()
    priority_manager.set_config_priority("production", ConfigPriority.PRIMARY)
    priority_manager.set_config_priority("backup", ConfigPriority.SECONDARY)

    # 模拟主配置失败
    # ... 测试逻辑

    # 验证已切换到 backup
    assert priority_manager.get_active_config() == "backup"

@pytest.mark.asyncio
async def test_automatic_recovery():
    """测试自动恢复"""
    # 当前使用 backup
    # 主配置恢复健康
    # 验证自动切回主配置
    pass

def test_cooldown_period():
    """测试冷却期"""
    # 在冷却期内不应触发故障转移
    pass

def test_rate_limiting():
    """测试频率限制"""
    # 每小时故障转移次数不应超过限制
    pass
```

---

## 📊 监控和告警

### 监控指标

1. **配置健康度**: 各配置组的健康状态
2. **故障转移次数**: 每小时/每天的故障转移次数
3. **活跃配置**: 当前使用的配置
4. **平均恢复时间**: 从故障到恢复的平均时间

### 告警触发条件

1. 主配置失败触发故障转移
2. 所有配置都不可用
3. 故障转移频率异常（超过限制）
4. 长时间未恢复到主配置

---

## 🎯 最佳实践

1. **合理设置阈值**: 根据业务需求调整故障阈值和冷却期
2. **多层备份**: 至少配置 Primary + Secondary
3. **监控告警**: 配置故障转移通知
4. **定期测试**: 定期手动触发故障转移测试
5. **记录分析**: 定期查看故障转移历史，分析故障原因

---

**文档版本**: v1.0
**最后更新**: 2025-10-16
**作者**: QCC Development Team
