"""QCC Failover Manager - 故障转移管理器"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FailoverManager:
    """故障转移管理器

    监控配置健康状态并在故障时自动切换。
    与 PriorityManager 协同工作，实现自动故障转移和恢复。
    """

    def __init__(
        self,
        config_manager=None,
        priority_manager=None,
        health_monitor=None,
        check_interval: int = 30
    ):
        """初始化故障转移管理器

        Args:
            config_manager: 配置管理器实例
            priority_manager: 优先级管理器实例
            health_monitor: 健康监控器实例
            check_interval: 健康检查间隔（秒）
        """
        self.config_manager = config_manager
        self.priority_manager = priority_manager
        self.health_monitor = health_monitor
        self.check_interval = check_interval
        self.running = False

        # 故障计数器 {profile_name: consecutive_failures}
        self.failure_counts: Dict[str, int] = {}

        # 最后检查时间 {profile_name: datetime}
        self.last_check_times: Dict[str, datetime] = {}

        # 恢复候选 {profile_name: last_failed_time}
        self.recovery_candidates: Dict[str, datetime] = {}

    async def start(self):
        """启动故障转移监控"""
        if self.running:
            logger.warning("故障转移管理器已经在运行")
            return

        if not self.priority_manager:
            logger.error("未配置 PriorityManager，无法启动故障转移监控")
            return

        self.running = True
        logger.info("[OK] 故障转移监控已启动")

        try:
            while self.running:
                await self._monitor_and_failover()
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.info("故障转移管理器收到停止信号")
        except Exception as e:
            logger.error(f"故障转移监控异常: {e}", exc_info=True)
        finally:
            logger.info("[OK] 故障转移管理器已停止")

    async def stop(self):
        """停止故障转移监控"""
        self.running = False

    async def _monitor_and_failover(self):
        """监控健康状态并执行故障转移"""
        if not self.priority_manager:
            return

        # 获取当前活跃配置
        active_profile_name = self.priority_manager.get_active_profile()
        if not active_profile_name:
            logger.debug("没有活跃配置")
            return

        # 检查活跃配置的健康状态
        is_healthy = await self._check_profile_health(active_profile_name)

        if not is_healthy:
            # 增加故障计数
            self.failure_counts[active_profile_name] = \
                self.failure_counts.get(active_profile_name, 0) + 1

            failure_count = self.failure_counts[active_profile_name]
            threshold = self.priority_manager.policy['failure_threshold']

            logger.warning(
                f"配置 {active_profile_name} 不健康 "
                f"({failure_count}/{threshold})"
            )

            # 达到故障阈值，触发故障转移
            if failure_count >= threshold:
                policy = self.priority_manager.policy
                if policy['auto_failover']:
                    await self.trigger_failover(
                        active_profile_name,
                        reason=f"连续 {failure_count} 次健康检查失败"
                    )
        else:
            # 健康，重置故障计数
            if active_profile_name in self.failure_counts:
                self.failure_counts[active_profile_name] = 0

        # 检查自动恢复
        await self._check_recovery()

    async def _check_profile_health(self, profile_name: str) -> bool:
        """检查配置的健康状态

        Args:
            profile_name: 配置名称

        Returns:
            是否健康
        """
        if not self.config_manager:
            return True

        try:
            profile = self.config_manager.get_profile(profile_name)
            if not profile:
                return False

            # 如果配置有 endpoints，检查是否有健康的 endpoint
            if hasattr(profile, 'endpoints') and profile.endpoints:
                healthy_count = 0
                for endpoint in profile.endpoints:
                    if endpoint.enabled and endpoint.is_healthy():
                        healthy_count += 1

                # 至少有一个健康的 endpoint
                return healthy_count > 0

            # 如果没有 endpoints，使用传统方式检查（调用健康检查器）
            if self.health_monitor:
                # TODO: 调用 health_monitor 检查单个配置
                return True

            # 默认认为健康
            return True

        except Exception as e:
            logger.error(f"检查配置 {profile_name} 健康状态失败: {e}")
            return False

    async def trigger_failover(self, from_profile: str, reason: str = "") -> bool:
        """触发故障转移

        Args:
            from_profile: 源配置名称
            reason: 故障原因

        Returns:
            是否成功故障转移
        """
        if not self.priority_manager:
            logger.error("未配置 PriorityManager，无法执行故障转移")
            return False

        logger.warning(f"[~] 触发故障转移: {from_profile}, 原因: {reason}")

        # 调用 PriorityManager 的故障转移逻辑
        success = self.priority_manager.trigger_failover(reason)

        if success:
            to_profile = self.priority_manager.get_active_profile()
            logger.warning(f"[~] 故障转移完成: {from_profile} → {to_profile}")
            print(f"\n[~] 故障转移: {from_profile} → {to_profile}")
            print(f"原因: {reason}")
            print("[OK] 故障转移完成\n")

            # 记录失败的配置，用于自动恢复
            self.recovery_candidates[from_profile] = datetime.now()

            # 重置新配置的故障计数
            self.failure_counts[to_profile] = 0

            return True
        else:
            logger.error("故障转移失败：没有可用的备用配置")
            print("\n✗ 故障转移失败：没有可用的备用配置\n")
            return False

    async def _check_recovery(self):
        """检查是否可以自动恢复到更高优先级的配置"""
        if not self.priority_manager:
            return

        policy = self.priority_manager.policy
        if not policy['auto_recovery']:
            return

        active_profile = self.priority_manager.get_active_profile()
        if not active_profile:
            return

        # 检查优先级更高的配置是否已恢复
        from fastcc.core.priority_manager import PriorityLevel

        active_level = self.priority_manager.get_level_by_profile(active_profile)
        if not active_level:
            return

        # 只在使用 secondary 或 fallback 时检查恢复
        if active_level == PriorityLevel.PRIMARY:
            return

        # 检查 PRIMARY 配置
        primary_profile = self.priority_manager.get_profile_by_level(
            PriorityLevel.PRIMARY
        )

        if primary_profile and primary_profile in self.recovery_candidates:
            # 检查冷却期
            last_failed = self.recovery_candidates[primary_profile]
            cooldown = policy['cooldown_period']

            if datetime.now() - last_failed < timedelta(seconds=cooldown):
                # 还在冷却期内
                return

            # 检查是否已恢复健康
            is_healthy = await self._check_profile_health(primary_profile)

            if is_healthy:
                logger.info(f"[OK] 配置 {primary_profile} 已恢复健康，准备切回")
                success = self.priority_manager.switch_to(
                    primary_profile,
                    reason="Auto recovery - primary profile recovered"
                )

                if success:
                    logger.info(f"[OK] 已自动恢复到主配置: {primary_profile}")
                    print(f"\n[OK] 自动恢复: {active_profile} → {primary_profile}")
                    print("原因: 主配置已恢复健康\n")

                    # 从恢复候选中移除
                    del self.recovery_candidates[primary_profile]
                    self.failure_counts[primary_profile] = 0

        # 如果当前是 FALLBACK，也检查 SECONDARY
        if active_level == PriorityLevel.FALLBACK:
            secondary_profile = self.priority_manager.get_profile_by_level(
                PriorityLevel.SECONDARY
            )

            if secondary_profile and secondary_profile in self.recovery_candidates:
                last_failed = self.recovery_candidates[secondary_profile]
                cooldown = policy['cooldown_period']

                if datetime.now() - last_failed < timedelta(seconds=cooldown):
                    return

                is_healthy = await self._check_profile_health(secondary_profile)

                if is_healthy:
                    logger.info(f"[OK] 配置 {secondary_profile} 已恢复健康，准备切回")
                    success = self.priority_manager.switch_to(
                        secondary_profile,
                        reason="Auto recovery - secondary profile recovered"
                    )

                    if success:
                        logger.info(f"[OK] 已自动恢复到次配置: {secondary_profile}")
                        print(f"\n[OK] 自动恢复: {active_profile} → {secondary_profile}")
                        print("原因: 次配置已恢复健康\n")

                        del self.recovery_candidates[secondary_profile]
                        self.failure_counts[secondary_profile] = 0

    def get_history(self) -> List[Dict[str, Any]]:
        """获取故障转移历史（委托给 PriorityManager）

        Returns:
            历史记录列表
        """
        if self.priority_manager:
            return self.priority_manager.get_history()
        return []

    def get_status(self) -> Dict[str, Any]:
        """获取故障转移管理器状态

        Returns:
            状态信息
        """
        active_profile = None
        policy = {}

        if self.priority_manager:
            active_profile = self.priority_manager.get_active_profile()
            policy = self.priority_manager.get_policy()

        return {
            'running': self.running,
            'active_profile': active_profile,
            'failure_counts': self.failure_counts.copy(),
            'recovery_candidates': {
                k: v.isoformat() for k, v in self.recovery_candidates.items()
            },
            'policy': policy
        }
