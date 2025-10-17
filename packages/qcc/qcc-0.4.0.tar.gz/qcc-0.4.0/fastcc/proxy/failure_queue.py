"""QCC Failure Queue - 失败 Endpoint 验证队列

专门用于验证失败的 endpoint 是否已恢复，而不是重试失败的请求。
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Set, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class FailureQueue:
    """失败 Endpoint 验证队列

    管理失败的 endpoint，定期验证是否已恢复健康。
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        config_manager=None,
        conversational_checker=None
    ):
        """初始化失败队列

        Args:
            storage_path: 队列持久化存储路径
            config_manager: 配置管理器（用于获取 endpoint）
            conversational_checker: 对话检查器（用于验证 endpoint）
        """
        self.storage_path = storage_path or Path.home() / '.qcc' / 'failure_endpoints.json'
        self.config_manager = config_manager
        self.conversational_checker = conversational_checker
        self.running = False

        # 失败的 endpoint ID 集合
        self.failed_endpoints: Set[str] = set()

        # 上次验证时间记录
        self.last_check_times: Dict[str, datetime] = {}

        # 统计信息
        self.stats = {
            'total_failed': 0,
            'total_verified': 0,
            'total_recovered': 0,
            'total_still_failed': 0
        }

        # 加载持久化数据
        self._load()

    def add_failed_endpoint(self, endpoint_id: str, reason: str = ""):
        """将失败的 endpoint 加入队列

        Args:
            endpoint_id: Endpoint ID
            reason: 失败原因
        """
        if endpoint_id not in self.failed_endpoints:
            self.failed_endpoints.add(endpoint_id)
            self.last_check_times[endpoint_id] = datetime.now()
            self.stats['total_failed'] += 1

            logger.info(
                f"Endpoint {endpoint_id} 加入失败队列, 原因: {reason}"
            )

            # 持久化
            self._save()

    def remove_endpoint(self, endpoint_id: str):
        """从队列中移除 endpoint

        Args:
            endpoint_id: Endpoint ID
        """
        if endpoint_id in self.failed_endpoints:
            self.failed_endpoints.remove(endpoint_id)
            self.last_check_times.pop(endpoint_id, None)
            logger.info(f"Endpoint {endpoint_id} 已从失败队列移除")
            self._save()

    async def process_queue(self, all_endpoints: List = None):
        """处理队列中的 endpoint（后台任务）

        Args:
            all_endpoints: 所有 endpoint 列表
        """
        self.running = True
        logger.info("[OK] 失败队列处理器已启动")
        logger.info("  - 检查间隔: 60秒")
        logger.info("  - 功能: 验证失败的 endpoint 是否已恢复")

        try:
            while self.running:
                if self.failed_endpoints and all_endpoints:
                    await self._verify_failed_endpoints(all_endpoints)
                await asyncio.sleep(60)  # 每60秒检查一次（1分钟）
        except asyncio.CancelledError:
            logger.info("失败队列处理器收到停止信号")
        finally:
            logger.info("[OK] 失败队列处理器已停止")

    async def _verify_failed_endpoints(self, all_endpoints: List):
        """验证失败的 endpoint

        Args:
            all_endpoints: 所有 endpoint 列表
        """
        if not self.conversational_checker:
            logger.warning("没有配置对话检查器，无法验证 endpoint")
            return

        logger.info(f"\n🔍 开始验证失败的 endpoint ({len(self.failed_endpoints)} 个)")

        endpoints_to_verify = []
        for endpoint in all_endpoints:
            if endpoint.id in self.failed_endpoints:
                endpoints_to_verify.append(endpoint)

        if not endpoints_to_verify:
            logger.debug("没有需要验证的 endpoint")
            return

        # 逐个验证
        for endpoint in endpoints_to_verify:
            self.stats['total_verified'] += 1

            logger.info(f"验证 endpoint {endpoint.id} ({endpoint.base_url})")

            # 使用对话检查器验证
            check = await self.conversational_checker.check_endpoint(endpoint)

            # 更新上次检查时间
            self.last_check_times[endpoint.id] = datetime.now()

            # 导入 HealthCheckResult
            from .health_check_models import HealthCheckResult

            if check.result == HealthCheckResult.SUCCESS:
                # 恢复健康
                endpoint.update_health_status(
                    status='healthy',
                    increment_requests=False,
                    is_failure=False,
                    response_time=check.response_time_ms
                )
                self.remove_endpoint(endpoint.id)
                self.stats['total_recovered'] += 1
                logger.info(
                    f"[OK] Endpoint {endpoint.id} 已恢复健康 "
                    f"({check.response_time_ms:.0f}ms)"
                )
            else:
                # 仍然失败
                self.stats['total_still_failed'] += 1
                logger.warning(
                    f"[X] Endpoint {endpoint.id} 仍然不健康: {check.error_message}"
                )

        # 持久化
        self._save()

    async def stop(self):
        """停止处理队列"""
        self.running = False

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'failed_endpoints_count': len(self.failed_endpoints),
            'failed_endpoints': list(self.failed_endpoints)
        }

    def clear(self):
        """清空队列"""
        self.failed_endpoints.clear()
        self.last_check_times.clear()
        self._save()
        logger.info("失败队列已清空")

    def _save(self):
        """保存队列到文件"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'failed_endpoints': list(self.failed_endpoints),
                'last_check_times': {
                    ep_id: dt.isoformat()
                    for ep_id, dt in self.last_check_times.items()
                },
                'stats': self.stats,
                'updated_at': datetime.now().isoformat()
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"失败队列已保存到: {self.storage_path}")

        except Exception as e:
            logger.error(f"保存失败队列失败: {e}")

    def _load(self):
        """从文件加载队列"""
        try:
            if not self.storage_path.exists():
                logger.debug("失败队列文件不存在，使用空队列")
                return

            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 加载失败的 endpoint
            self.failed_endpoints = set(data.get('failed_endpoints', []))

            # 加载上次检查时间
            for ep_id, time_str in data.get('last_check_times', {}).items():
                self.last_check_times[ep_id] = datetime.fromisoformat(time_str)

            # 加载统计信息
            self.stats = data.get('stats', self.stats)

            logger.debug(
                f"失败队列已加载: {self.storage_path}, "
                f"队列大小: {len(self.failed_endpoints)}"
            )

        except Exception as e:
            logger.error(f"加载失败队列失败: {e}")
