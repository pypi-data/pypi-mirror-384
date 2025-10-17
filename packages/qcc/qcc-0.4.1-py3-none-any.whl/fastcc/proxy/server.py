"""QCC Proxy Server - 代理服务器主逻辑"""

import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any
from aiohttp import web, ClientSession, ClientTimeout
from datetime import datetime
from pathlib import Path
import signal

logger = logging.getLogger(__name__)


class ProxyServer:
    """QCC 代理服务器

    拦截 Claude Code 的 API 请求并转发到配置的后端 endpoint。
    支持多 endpoint 负载均衡、健康检测和自动故障转移。
    """

    def __init__(
        self,
        host: str = '127.0.0.1',
        port: int = 7860,
        config_manager=None,
        load_balancer=None,
        priority_manager=None,
        failover_manager=None,
        health_monitor=None,
        failure_queue=None,
        cluster_name: str = None
    ):
        """初始化代理服务器

        Args:
            host: 监听地址 (默认 127.0.0.1)
            port: 监听端口 (默认 7860)
            config_manager: 配置管理器实例
            load_balancer: 负载均衡器实例
            priority_manager: 优先级管理器实例
            failover_manager: 故障转移管理器实例
            health_monitor: 健康监控器实例
            failure_queue: 失败队列实例
            cluster_name: 集群配置名称（可选）
        """
        self.host = host
        self.port = port
        self.config_manager = config_manager
        self.load_balancer = load_balancer
        self.priority_manager = priority_manager
        self.failover_manager = failover_manager
        self.health_monitor = health_monitor
        self.failure_queue = failure_queue
        self.cluster_name = cluster_name

        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.client_session: Optional[ClientSession] = None
        self.running = False
        self._shutting_down = False  # 防止重复关闭

        # 后台任务
        self._health_monitor_task: Optional[asyncio.Task] = None
        self._failover_manager_task: Optional[asyncio.Task] = None
        self._failure_queue_task: Optional[asyncio.Task] = None

        # PID 文件路径
        self.pid_file = Path.home() / '.qcc' / 'proxy.pid'
        self.log_file = Path.home() / '.qcc' / 'proxy.log'

        # 统计信息
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'start_time': None,
            'uptime': 0
        }

        self._setup_routes()
        self._setup_signal_handlers()

    def _setup_routes(self):
        """设置路由"""
        # 捕获所有路径的所有 HTTP 方法
        self.app.router.add_route('*', '/{path:.*}', self.handle_request)

    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            if self._shutting_down:
                logger.debug(f"已在关闭中，忽略信号 {signum}")
                return
            logger.info(f"收到信号 {signum}，准备关闭服务器...")
            self._shutting_down = True
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def handle_request(self, request: web.Request) -> web.Response:
        """处理代理请求，支持自动重试和故障转移

        Args:
            request: 客户端请求

        Returns:
            代理响应
        """
        self.stats['total_requests'] += 1
        request_id = f"req-{self.stats['total_requests']}"

        try:
            logger.info(f"[{request_id}] {request.method} {request.path}")

            # 1. 读取请求体
            body = await request.read()

            # 2. 重试逻辑：最多尝试 3 次（初始 + 2 次重试）
            max_retries = 2
            last_response = None
            last_endpoint = None

            for retry_count in range(max_retries + 1):
                # 选择 endpoint（通过负载均衡器）
                endpoint = await self._select_endpoint()
                if not endpoint:
                    logger.error(f"[{request_id}] 没有可用的 endpoint")
                    self.stats['failed_requests'] += 1
                    return web.Response(
                        status=503,
                        text=json.dumps({'error': 'No available endpoints'}),
                        content_type='application/json'
                    )

                if retry_count > 0:
                    logger.info(f"[{request_id}] 重试 {retry_count}/{max_retries}, 选中 endpoint: {endpoint.id}")
                else:
                    logger.info(f"[{request_id}] 选中 endpoint: {endpoint.id} ({endpoint.base_url})")

                last_endpoint = endpoint

                # 3. 转发请求
                response = await self._forward_request(
                    endpoint=endpoint,
                    method=request.method,
                    path=request.path,
                    headers=dict(request.headers),
                    body=body,
                    request_id=request_id,
                    original_request=request
                )

                if response:
                    last_response = response
                    # 检查是否成功（只有 200 才算成功）
                    if response.status == 200:
                        self.stats['successful_requests'] += 1
                        logger.info(f"[{request_id}] 请求成功: {response.status}")
                        return response
                    else:
                        # 非 200 状态码，继续重试
                        logger.warning(
                            f"[{request_id}] 收到非成功响应: {response.status}, "
                            f"剩余重试次数: {max_retries - retry_count}"
                        )
                        if retry_count < max_retries:
                            continue  # 重试
                        else:
                            # 重试次数用完，返回最后一次响应
                            self.stats['failed_requests'] += 1
                            logger.error(f"[{request_id}] 重试 {max_retries} 次后仍失败，状态码: {response.status}")
                            return response
                else:
                    # 请求失败（超时或异常）
                    logger.error(f"[{request_id}] 请求失败，endpoint: {endpoint.id}")
                    if retry_count < max_retries:
                        continue  # 重试
                    else:
                        # 重试次数用完
                        self.stats['failed_requests'] += 1
                        logger.error(f"[{request_id}] 重试 {max_retries} 次后仍失败")
                        return web.Response(
                            status=502,
                            text=json.dumps({'error': 'Bad Gateway - All retries failed'}),
                            content_type='application/json'
                        )

            # 理论上不应该到这里
            return last_response if last_response else web.Response(
                status=502,
                text=json.dumps({'error': 'Bad Gateway'}),
                content_type='application/json'
            )

        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"[{request_id}] 处理请求异常: {e}", exc_info=True)
            return web.Response(
                status=500,
                text=json.dumps({'error': str(e)}),
                content_type='application/json'
            )

    async def _select_endpoint(self):
        """选择 endpoint（通过负载均衡器）"""
        if self.load_balancer and self.config_manager:
            # 获取当前活跃配置的所有 endpoint
            endpoints = self._get_active_endpoints()
            if endpoints:
                return await self.load_balancer.select_endpoint(endpoints)

        # 如果没有负载均衡器，使用简单的单配置模式
        if self.config_manager:
            default_profile = self.config_manager.get_default_profile()
            if default_profile:
                # 如果配置有 endpoints，使用第一个
                if hasattr(default_profile, 'endpoints') and default_profile.endpoints:
                    return default_profile.endpoints[0]
                # 否则从传统字段创建临时 endpoint
                from fastcc.core.endpoint import Endpoint
                return Endpoint(
                    base_url=default_profile.base_url,
                    api_key=default_profile.api_key
                )

        return None

    def _get_active_endpoints(self):
        """获取当前活跃配置的所有健康 endpoint"""
        endpoints = []
        if not self.config_manager:
            return endpoints

        # 如果指定了集群配置，使用该配置的 endpoints
        if self.cluster_name:
            profile = self.config_manager.get_profile(self.cluster_name)
            if profile and hasattr(profile, 'endpoints') and profile.endpoints:
                # 只返回启用且健康的 endpoint
                endpoints = [
                    ep for ep in profile.endpoints
                    if ep.enabled and ep.is_healthy()
                ]
                return endpoints

        # 否则，优先使用 priority_manager 获取活跃配置
        profile_name = None
        if self.priority_manager:
            profile_name = self.priority_manager.get_active_profile()

        # 如果没有优先级配置，使用默认配置
        if not profile_name:
            profile = self.config_manager.get_default_profile()
        else:
            profile = self.config_manager.get_profile(profile_name)

        if not profile:
            return endpoints

        # 获取配置的 endpoints
        if hasattr(profile, 'endpoints') and profile.endpoints:
            # 只返回启用且健康的 endpoint
            endpoints = [
                ep for ep in profile.endpoints
                if ep.enabled and ep.is_healthy()
            ]

        return endpoints

    def _get_all_endpoints(self):
        """获取所有 endpoint（包括不健康的）

        Returns:
            所有 endpoint 列表
        """
        endpoints = []
        if not self.config_manager:
            return endpoints

        # 如果指定了集群配置，使用该配置的 endpoints
        if self.cluster_name:
            profile = self.config_manager.get_profile(self.cluster_name)
            if profile and hasattr(profile, 'endpoints') and profile.endpoints:
                # 返回所有 endpoint（不过滤健康状态）
                return list(profile.endpoints)

        # 否则，优先使用 priority_manager 获取活跃配置
        profile_name = None
        if self.priority_manager:
            profile_name = self.priority_manager.get_active_profile()

        # 如果没有优先级配置，使用默认配置
        if not profile_name:
            profile = self.config_manager.get_default_profile()
        else:
            profile = self.config_manager.get_profile(profile_name)

        if not profile:
            return endpoints

        # 获取配置的 endpoints
        if hasattr(profile, 'endpoints') and profile.endpoints:
            # 返回所有 endpoint（不过滤健康状态）
            endpoints = list(profile.endpoints)

        return endpoints

    async def _forward_request(
        self,
        endpoint,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: bytes,
        request_id: str,
        original_request: web.Request = None
    ) -> Optional[web.Response]:
        """转发请求到目标 endpoint

        Args:
            endpoint: 目标 endpoint
            method: HTTP 方法
            path: 请求路径
            headers: 请求头
            body: 请求体
            request_id: 请求 ID
            original_request: 原始 Request 对象（用于流式响应）

        Returns:
            代理响应，失败返回 None
        """
        if not self.client_session:
            self.client_session = ClientSession(
                timeout=ClientTimeout(total=300)  # 增加默认超时到 5 分钟
            )

        try:
            # 构建目标 URL
            target_url = f"{endpoint.base_url}{path}"

            # 修改请求头：同时支持 Anthropic 和 OpenAI 格式
            forward_headers = headers.copy()

            # 同时发送两种认证方式，确保兼容性
            # Anthropic 原生格式
            forward_headers['x-api-key'] = endpoint.api_key
            forward_headers['anthropic-version'] = '2023-06-01'

            # OpenAI 兼容格式
            forward_headers['Authorization'] = f'Bearer {endpoint.api_key}'

            # 移除不需要的头
            forward_headers.pop('Host', None)
            forward_headers.pop('Connection', None)

            # 记录请求开始时间
            start_time = datetime.now()

            # 发送请求
            async with self.client_session.request(
                method=method,
                url=target_url,
                headers=forward_headers,
                data=body,
                timeout=ClientTimeout(total=300, sock_read=60)  # 总超时 5 分钟，读取超时 1 分钟
            ) as response:
                # 检查是否为流式响应
                is_streaming = (
                    response.headers.get('Content-Type', '').startswith('text/event-stream') or
                    response.headers.get('Transfer-Encoding') == 'chunked' or
                    'stream' in response.headers.get('Content-Type', '').lower()
                )

                if is_streaming and original_request:
                    # 流式响应：创建 StreamResponse 并逐块转发
                    proxy_response = web.StreamResponse(
                        status=response.status,
                        headers=dict(response.headers)
                    )
                    await proxy_response.prepare(original_request)

                    # 逐块读取并转发
                    async for chunk in response.content.iter_chunked(8192):
                        await proxy_response.write(chunk)

                    await proxy_response.write_eof()

                    # 计算响应时间
                    response_time = (datetime.now() - start_time).total_seconds() * 1000

                    # 更新 endpoint 健康状态
                    endpoint.update_health_status(
                        status='healthy',
                        increment_requests=True,
                        is_failure=False,
                        response_time=response_time
                    )

                    logger.debug(
                        f"[{request_id}] 流式响应完成: {response.status}, "
                        f"耗时: {response_time:.2f}ms"
                    )

                    return proxy_response
                else:
                    # 非流式响应：一次性读取
                    response_body = await response.read()

                    # 计算响应时间
                    response_time = (datetime.now() - start_time).total_seconds() * 1000

                    # 检查状态码，只有 200 才算成功
                    is_success = response.status == 200

                    # 更新 endpoint 健康状态
                    endpoint.update_health_status(
                        status='healthy' if is_success else 'unhealthy',
                        increment_requests=True,
                        is_failure=not is_success,
                        response_time=response_time
                    )

                    if is_success:
                        logger.debug(
                            f"[{request_id}] 响应成功: {response.status}, "
                            f"耗时: {response_time:.2f}ms"
                        )
                    else:
                        logger.warning(
                            f"[{request_id}] 响应失败: {response.status}, "
                            f"耗时: {response_time:.2f}ms"
                        )
                        # 将失败的 endpoint 加入验证队列
                        if self.failure_queue:
                            await self.failure_queue.add_failed_endpoint(
                                endpoint.id,
                                f"HTTP {response.status}"
                            )

                    # 构建代理响应
                    proxy_response = web.Response(
                        status=response.status,
                        body=response_body,
                        headers=dict(response.headers)
                    )

                    return proxy_response

        except asyncio.TimeoutError:
            logger.error(f"[{request_id}] 请求超时")
            endpoint.update_health_status(
                status='unhealthy',
                increment_requests=True,
                is_failure=True
            )
            # 将失败请求加入队列
            if self.failure_queue:
                # 将失败的 endpoint 加入验证队列
                await self.failure_queue.add_failed_endpoint(
                    endpoint.id,
                    f"Timeout after {endpoint.timeout}s"
                )
            return None

        except Exception as e:
            logger.error(f"[{request_id}] 转发请求失败: {e}")
            endpoint.update_health_status(
                status='unhealthy',
                increment_requests=True,
                is_failure=True
            )
            # 将失败请求加入队列
            if self.failure_queue:
                # 将失败的 endpoint 加入验证队列
                await self.failure_queue.add_failed_endpoint(
                    endpoint.id,
                    str(e)
                )
            return None

    async def start(self):
        """启动代理服务器"""
        if self.running:
            logger.warning("代理服务器已经在运行")
            return

        try:
            logger.info(f"正在启动代理服务器 {self.host}:{self.port}...")

            # 保存 PID 到文件
            self._write_pid()

            self.runner = web.AppRunner(self.app)
            await self.runner.setup()

            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()

            self.running = True
            self.stats['start_time'] = datetime.now().isoformat()

            logger.info(f"[OK] 代理服务器已启动: http://{self.host}:{self.port}")
            print(f"[OK] 代理服务器已启动: http://{self.host}:{self.port}")

            # 注释掉主动健康监控器（改为被动检测）
            # if self.health_monitor:
            #     endpoints = self._get_active_endpoints()
            #     if endpoints:
            #         self._health_monitor_task = asyncio.create_task(
            #             self.health_monitor.start(endpoints)
            #         )
            #         logger.info("[OK] 健康监控器已启动")
            #         print("[OK] 健康监控器已启动")

            # 启动故障转移管理器（后台任务）
            if self.failover_manager:
                policy = self.priority_manager.get_policy() if self.priority_manager else {}
                if policy.get('auto_failover'):
                    self._failover_manager_task = asyncio.create_task(
                        self.failover_manager.start()
                    )
                    logger.info("[OK] 故障转移监控已启动")
                    print("[OK] 故障转移监控已启动")

            # 启动失败队列处理器（后台任务）
            if self.failure_queue:
                # 清空历史失败记录（每次启动时重新开始）
                self.failure_queue.clear()
                # 获取所有 endpoints 用于验证
                all_endpoints = self._get_all_endpoints()
                self._failure_queue_task = asyncio.create_task(
                    self.failure_queue.process_queue(all_endpoints)
                )
                logger.info("[OK] 失败队列处理器已启动")
                print("[OK] 失败队列处理器已启动")

            # 保持运行
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                logger.info("收到停止信号")

        except Exception as e:
            logger.error(f"启动代理服务器失败: {e}", exc_info=True)
            self._remove_pid()
            raise
        finally:
            # 确保 PID 文件被清理
            await self.stop()

    async def stop(self):
        """停止代理服务器"""
        if not self.running:
            return

        logger.info("正在停止代理服务器...")
        print("\n正在停止代理服务器...")

        self.running = False

        # 停止失败队列处理器
        if self.failure_queue and self._failure_queue_task:
            await self.failure_queue.stop()
            if not self._failure_queue_task.done():
                self._failure_queue_task.cancel()
                try:
                    await self._failure_queue_task
                except asyncio.CancelledError:
                    pass
            self._failure_queue_task = None
            logger.info("[OK] 失败队列处理器已停止")

        # 停止故障转移管理器
        if self.failover_manager and self._failover_manager_task:
            await self.failover_manager.stop()
            if not self._failover_manager_task.done():
                self._failover_manager_task.cancel()
                try:
                    await self._failover_manager_task
                except asyncio.CancelledError:
                    pass
            self._failover_manager_task = None
            logger.info("[OK] 故障转移管理器已停止")

        # 停止健康监控器
        if self.health_monitor and self._health_monitor_task:
            await self.health_monitor.stop()
            if not self._health_monitor_task.done():
                self._health_monitor_task.cancel()
                try:
                    await self._health_monitor_task
                except asyncio.CancelledError:
                    pass
            self._health_monitor_task = None
            logger.info("[OK] 健康监控器已停止")

        # 关闭客户端会话
        if self.client_session:
            await self.client_session.close()
            self.client_session = None

        # 停止服务器
        if self.site:
            await self.site.stop()
            self.site = None

        if self.runner:
            await self.runner.cleanup()
            self.runner = None

        # 删除 PID 文件
        self._remove_pid()

        logger.info("[OK] 代理服务器已停止")
        print("[OK] 代理服务器已停止")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()

        if stats['start_time']:
            start = datetime.fromisoformat(stats['start_time'])
            stats['uptime'] = (datetime.now() - start).total_seconds()

        return stats

    def _write_pid(self):
        """写入 PID 文件"""
        try:
            self.pid_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.pid_file, 'w') as f:
                data = {
                    'pid': os.getpid(),
                    'host': self.host,
                    'port': self.port,
                    'start_time': datetime.now().isoformat()
                }
                json.dump(data, f)
            logger.debug(f"PID 文件已写入: {self.pid_file}")
        except Exception as e:
            logger.error(f"写入 PID 文件失败: {e}")

    def _remove_pid(self):
        """删除 PID 文件"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
                logger.debug(f"PID 文件已删除: {self.pid_file}")
        except Exception as e:
            logger.error(f"删除 PID 文件失败: {e}")

    @staticmethod
    def get_running_server():
        """获取正在运行的服务器信息

        Returns:
            服务器信息字典，如果没有运行则返回 None
        """
        pid_file = Path.home() / '.qcc' / 'proxy.pid'

        if not pid_file.exists():
            return None

        try:
            with open(pid_file, 'r') as f:
                data = json.load(f)

            pid = data.get('pid')
            if not pid:
                return None

            # 检查进程是否存在
            try:
                os.kill(pid, 0)  # 发送信号 0 只检查进程是否存在
                return data
            except OSError:
                # 进程不存在，清理 PID 文件
                pid_file.unlink()
                return None

        except Exception as e:
            logger.error(f"读取 PID 文件失败: {e}")
            return None

    @staticmethod
    def stop_running_server():
        """停止正在运行的服务器

        Returns:
            是否成功停止
        """
        server_info = ProxyServer.get_running_server()

        if not server_info:
            return False

        pid = server_info['pid']

        try:
            # 发送 SIGTERM 信号
            os.kill(pid, signal.SIGTERM)
            logger.info(f"已向进程 {pid} 发送停止信号")
            return True
        except OSError as e:
            logger.error(f"停止进程失败: {e}")
            return False

    async def __aenter__(self):
        """上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        await self.stop()
