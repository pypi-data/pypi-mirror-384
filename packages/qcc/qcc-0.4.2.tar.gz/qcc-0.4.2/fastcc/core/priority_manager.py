"""优先级管理器 - Priority Manager

管理配置的优先级体系：Primary（主）→ Secondary（次）→ Fallback（兜底）
支持自动故障转移和手动切换
"""

import json
import logging
from enum import Enum
from typing import Optional, Dict, List, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class PriorityLevel(Enum):
    """优先级级别"""
    PRIMARY = "primary"      # 主配置
    SECONDARY = "secondary"  # 次配置
    FALLBACK = "fallback"    # 兜底配置


class PriorityManager:
    """优先级管理器

    管理配置的优先级，支持三级优先级体系和自动故障转移。
    """

    def __init__(self, config_manager=None, storage_path: Optional[Path] = None):
        """初始化优先级管理器

        Args:
            config_manager: 配置管理器实例
            storage_path: 存储路径（用于持久化优先级配置）
        """
        self.config_manager = config_manager
        self.storage_path = storage_path or Path.home() / '.qcc' / 'priority.json'

        # 优先级配置 {level: profile_name}
        self.priority_map: Dict[str, Optional[str]] = {
            PriorityLevel.PRIMARY.value: None,
            PriorityLevel.SECONDARY.value: None,
            PriorityLevel.FALLBACK.value: None,
        }

        # 当前活跃的配置
        self.active_profile: Optional[str] = None

        # 切换历史
        self.switch_history: List[Dict[str, Any]] = []

        # 策略配置
        self.policy = {
            'auto_failover': False,        # 自动故障转移
            'auto_recovery': False,        # 自动恢复
            'failure_threshold': 3,        # 故障阈值
            'cooldown_period': 300,        # 冷却期（秒）
        }

        # 加载持久化数据
        self._load()

    def set_priority(self, profile_name: str, level: PriorityLevel) -> bool:
        """设置配置的优先级

        Args:
            profile_name: 配置名称
            level: 优先级级别

        Returns:
            是否设置成功
        """
        # 验证配置是否存在
        if self.config_manager:
            if not self.config_manager.has_profile(profile_name):
                logger.error(f"配置不存在: {profile_name}")
                return False

        # 检查是否已经分配给其他级别
        for existing_level, existing_profile in self.priority_map.items():
            if existing_profile == profile_name and existing_level != level.value:
                logger.warning(
                    f"配置 {profile_name} 已分配给 {existing_level}，"
                    f"将移除旧分配"
                )
                self.priority_map[existing_level] = None

        # 设置新的优先级
        self.priority_map[level.value] = profile_name

        # 如果是第一次设置或当前无活跃配置，自动激活
        if not self.active_profile and level == PriorityLevel.PRIMARY:
            self.active_profile = profile_name
            self._add_history(
                from_profile=None,
                to_profile=profile_name,
                reason="Initial activation",
                switch_type="manual"
            )

        self._save()
        logger.info(f"✓ 已设置 {profile_name} 为 {level.value} 配置")
        return True

    def remove_priority(self, level: PriorityLevel) -> bool:
        """移除指定级别的优先级配置

        Args:
            level: 优先级级别

        Returns:
            是否移除成功
        """
        profile_name = self.priority_map.get(level.value)
        if not profile_name:
            logger.warning(f"{level.value} 级别未配置")
            return False

        self.priority_map[level.value] = None

        # 如果移除的是当前活跃配置，需要切换
        if self.active_profile == profile_name:
            self._activate_next_available()

        self._save()
        logger.info(f"✓ 已移除 {level.value} 配置: {profile_name}")
        return True

    def get_profile_by_level(self, level: PriorityLevel) -> Optional[str]:
        """获取指定级别的配置名称

        Args:
            level: 优先级级别

        Returns:
            配置名称，如果未设置则返回 None
        """
        return self.priority_map.get(level.value)

    def get_level_by_profile(self, profile_name: str) -> Optional[PriorityLevel]:
        """获取配置的优先级级别

        Args:
            profile_name: 配置名称

        Returns:
            优先级级别，如果未设置则返回 None
        """
        for level, name in self.priority_map.items():
            if name == profile_name:
                return PriorityLevel(level)
        return None

    def switch_to(self, profile_name: str, reason: str = "") -> bool:
        """手动切换到指定配置

        Args:
            profile_name: 目标配置名称
            reason: 切换原因

        Returns:
            是否切换成功
        """
        # 验证配置是否存在
        if self.config_manager:
            if not self.config_manager.has_profile(profile_name):
                logger.error(f"配置不存在: {profile_name}")
                return False

        # 验证配置是否在优先级列表中
        if profile_name not in self.priority_map.values():
            logger.error(f"配置 {profile_name} 未设置优先级")
            return False

        old_profile = self.active_profile
        self.active_profile = profile_name

        self._add_history(
            from_profile=old_profile,
            to_profile=profile_name,
            reason=reason or "Manual switch",
            switch_type="manual"
        )

        self._save()
        logger.info(f"✓ 已切换到配置: {profile_name}")
        return True

    def get_active_profile(self) -> Optional[str]:
        """获取当前活跃的配置名称

        Returns:
            活跃配置名称
        """
        return self.active_profile

    def get_next_available_profile(self) -> Optional[str]:
        """获取下一个可用的配置（按优先级顺序）

        Returns:
            下一个可用的配置名称
        """
        # 按优先级顺序查找
        order = [PriorityLevel.PRIMARY, PriorityLevel.SECONDARY, PriorityLevel.FALLBACK]

        for level in order:
            profile_name = self.priority_map.get(level.value)
            if profile_name and profile_name != self.active_profile:
                # 如果有 config_manager，检查配置是否健康
                if self.config_manager:
                    profile = self.config_manager.get_profile(profile_name)
                    if profile and self._is_profile_healthy(profile):
                        return profile_name
                else:
                    return profile_name

        return None

    def trigger_failover(self, reason: str = "") -> bool:
        """触发故障转移

        Args:
            reason: 故障原因

        Returns:
            是否成功切换到下一个配置
        """
        next_profile = self.get_next_available_profile()

        if not next_profile:
            logger.error("没有可用的备用配置进行故障转移")
            return False

        old_profile = self.active_profile
        self.active_profile = next_profile

        self._add_history(
            from_profile=old_profile,
            to_profile=next_profile,
            reason=reason or "Auto failover",
            switch_type="failover"
        )

        self._save()
        logger.warning(f"🔄 故障转移: {old_profile} → {next_profile}")
        return True

    def get_priority_list(self) -> List[Dict[str, Any]]:
        """获取优先级配置列表

        Returns:
            优先级配置列表
        """
        result = []
        for level in [PriorityLevel.PRIMARY, PriorityLevel.SECONDARY, PriorityLevel.FALLBACK]:
            profile_name = self.priority_map.get(level.value)
            result.append({
                'level': level.value,
                'profile': profile_name,
                'active': profile_name == self.active_profile
            })
        return result

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取切换历史

        Args:
            limit: 返回的历史记录数量

        Returns:
            历史记录列表
        """
        return self.switch_history[-limit:] if self.switch_history else []

    def set_policy(
        self,
        auto_failover: Optional[bool] = None,
        auto_recovery: Optional[bool] = None,
        failure_threshold: Optional[int] = None,
        cooldown_period: Optional[int] = None
    ):
        """设置故障转移策略

        Args:
            auto_failover: 是否启用自动故障转移
            auto_recovery: 是否启用自动恢复
            failure_threshold: 故障阈值
            cooldown_period: 冷却期（秒）
        """
        if auto_failover is not None:
            self.policy['auto_failover'] = auto_failover
        if auto_recovery is not None:
            self.policy['auto_recovery'] = auto_recovery
        if failure_threshold is not None:
            self.policy['failure_threshold'] = failure_threshold
        if cooldown_period is not None:
            self.policy['cooldown_period'] = cooldown_period

        self._save()
        logger.info("✓ 故障转移策略已更新")

    def get_policy(self) -> Dict[str, Any]:
        """获取当前策略配置

        Returns:
            策略配置字典
        """
        return self.policy.copy()

    def _activate_next_available(self):
        """激活下一个可用的配置"""
        next_profile = self.get_next_available_profile()
        if next_profile:
            old_profile = self.active_profile
            self.active_profile = next_profile
            self._add_history(
                from_profile=old_profile,
                to_profile=next_profile,
                reason="Previous profile removed",
                switch_type="auto"
            )
            logger.info(f"✓ 已自动激活配置: {next_profile}")
        else:
            self.active_profile = None
            logger.warning("没有可用的配置")

    def _is_profile_healthy(self, profile) -> bool:
        """检查配置是否健康

        Args:
            profile: 配置对象

        Returns:
            是否健康
        """
        # 如果配置有 endpoints，检查是否有健康的 endpoint
        if hasattr(profile, 'endpoints') and profile.endpoints:
            healthy_endpoints = [
                ep for ep in profile.endpoints
                if ep.enabled and ep.is_healthy()
            ]
            return len(healthy_endpoints) > 0

        # 如果没有 endpoints，认为配置是健康的
        return True

    def _add_history(
        self,
        from_profile: Optional[str],
        to_profile: str,
        reason: str,
        switch_type: str
    ):
        """添加切换历史记录

        Args:
            from_profile: 源配置
            to_profile: 目标配置
            reason: 切换原因
            switch_type: 切换类型 (manual/failover/auto)
        """
        self.switch_history.append({
            'timestamp': datetime.now().isoformat(),
            'from': from_profile,
            'to': to_profile,
            'reason': reason,
            'type': switch_type
        })

        # 限制历史记录数量
        if len(self.switch_history) > 100:
            self.switch_history = self.switch_history[-100:]

    def _save(self):
        """保存优先级配置到文件"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'priority_map': self.priority_map,
                'active_profile': self.active_profile,
                'policy': self.policy,
                'switch_history': self.switch_history,
                'updated_at': datetime.now().isoformat()
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"优先级配置已保存到: {self.storage_path}")

        except Exception as e:
            logger.error(f"保存优先级配置失败: {e}")

    def _load(self):
        """从文件加载优先级配置"""
        try:
            if not self.storage_path.exists():
                logger.debug("优先级配置文件不存在，使用默认配置")
                return

            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.priority_map = data.get('priority_map', self.priority_map)
            self.active_profile = data.get('active_profile')
            self.policy = data.get('policy', self.policy)
            self.switch_history = data.get('switch_history', [])

            logger.debug(f"优先级配置已加载: {self.storage_path}")

        except Exception as e:
            logger.error(f"加载优先级配置失败: {e}")

    def reset(self):
        """重置所有优先级配置"""
        self.priority_map = {level: None for level in self.priority_map.keys()}
        self.active_profile = None
        self.switch_history = []
        self._save()
        logger.info("✓ 优先级配置已重置")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）

        Returns:
            配置字典
        """
        return {
            'priority_map': self.priority_map,
            'active_profile': self.active_profile,
            'policy': self.policy,
            'history_count': len(self.switch_history)
        }
