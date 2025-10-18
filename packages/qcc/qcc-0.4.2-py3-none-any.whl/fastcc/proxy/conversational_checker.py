"""对话式健康检查器

通过真实的 AI 对话测试来评估 endpoint 的健康状态和性能。
相比传统的 ping 测试，这种方式能更准确地反映真实使用情况。
"""

import asyncio
import aiohttp
import random
import time
import logging
from typing import List, Optional, Dict
from .health_check_models import ConversationalHealthCheck, HealthCheckResult

logger = logging.getLogger(__name__)


class ConversationalHealthChecker:
    """对话式健康检查器

    发送真实的 AI 对话请求来测试 endpoint 的健康状态，
    而不是简单的网络 ping。
    """

    def __init__(self):
        """初始化健康检查器"""
        self.timeout = 30  # 30 秒超时
        self.max_tokens = 20  # 确保有足够空间返回验证码
        # 使用最快最便宜的 Claude 模型（根据 AnyRouter 测试，haiku 系列可用）
        self.model = "claude-3-5-haiku-20241022"

    async def check_endpoint(self, endpoint) -> ConversationalHealthCheck:
        """检查单个 endpoint

        Args:
            endpoint: Endpoint 实例

        Returns:
            ConversationalHealthCheck 记录
        """
        check = ConversationalHealthCheck(endpoint.id)

        # 生成随机验证码（6位字母数字组合）
        verification_code = ''.join(
            random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6)
        )
        check.test_message = f"收到消息请仅回复这个验证码：{verification_code}"
        check.verification_code = verification_code  # 保存用于验证

        try:
            start_time = time.time()

            # 发送测试请求
            response = await self._send_test_message(
                endpoint,
                check.test_message
            )

            end_time = time.time()
            check.response_time_ms = (end_time - start_time) * 1000

            # 解析响应
            if response:
                check.result = HealthCheckResult.SUCCESS
                check.response_content = response.get('content', '')
                check.tokens_used = response.get('usage', {}).get('total_tokens', 0)
                check.model_used = response.get('model', '')

                # 验证响应质量（检查是否包含验证码）
                check.response_valid = self._validate_response(
                    check.verification_code,
                    check.response_content
                )
                check.response_score = self._calculate_response_score(
                    check.response_time_ms,
                    check.response_valid,
                    check.response_content
                )

                logger.debug(
                    f"Endpoint {endpoint.id} 健康检查成功 "
                    f"({check.response_time_ms:.0f}ms, 评分: {check.response_score:.0f})"
                )
            else:
                check.result = HealthCheckResult.FAILURE
                logger.warning(f"Endpoint {endpoint.id} 健康检查失败：无响应")

        except asyncio.TimeoutError:
            check.result = HealthCheckResult.TIMEOUT
            check.error_message = "请求超时"
            logger.error(f"Endpoint {endpoint.id} 健康检查超时")

        except aiohttp.ClientError as e:
            error_str = str(e).lower()

            if 'rate limit' in error_str or '429' in error_str:
                check.result = HealthCheckResult.RATE_LIMITED
                check.error_message = "API 限流"
                logger.warning(f"Endpoint {endpoint.id} 被限流")
            elif 'unauthorized' in error_str or '401' in error_str:
                check.result = HealthCheckResult.INVALID_KEY
                check.error_message = "API Key 无效"
                logger.error(f"Endpoint {endpoint.id} API Key 无效")
            else:
                check.result = HealthCheckResult.FAILURE
                check.error_message = str(e)
                logger.error(f"Endpoint {endpoint.id} 健康检查失败: {e}")

        except Exception as e:
            check.result = HealthCheckResult.FAILURE
            check.error_message = f"未知错误: {str(e)}"
            logger.error(f"Endpoint {endpoint.id} 健康检查异常: {e}", exc_info=True)

        return check

    async def _send_test_message(
        self,
        endpoint,
        message: str
    ) -> Optional[Dict]:
        """发送测试消息到 endpoint

        Args:
            endpoint: Endpoint 实例
            message: 测试消息

        Returns:
            响应数据或 None
        """
        # 构建 API 请求
        url = f"{endpoint.base_url}/v1/messages"

        # 同时支持两种认证方式以确保最大兼容性
        headers = {
            'Content-Type': 'application/json',
            # Anthropic 原生格式
            'x-api-key': endpoint.api_key,
            # OpenAI 兼容格式
            'Authorization': f'Bearer {endpoint.api_key}',
            'anthropic-version': '2023-06-01',
            # Claude Code CLI 识别（从官方 CLI 源码提取）
            'User-Agent': 'claude-code/2.0.21',
            'x-app': 'cli'
        }

        payload = {
            'model': self.model,
            'max_tokens': self.max_tokens,
            'messages': [
                {
                    'role': 'user',
                    'content': message
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    # 提取响应内容
                    # 支持标准 Anthropic 格式和其他可能的格式
                    content = ''
                    if 'content' in data and data['content']:
                        # 标准 Anthropic 格式
                        content = data['content'][0].get('text', '')
                    elif 'message' in data:
                        # 某些代理可能使用 message 字段
                        content = data['message']
                    elif 'text' in data:
                        # 简化格式
                        content = data['text']

                    return {
                        'content': content,
                        'usage': data.get('usage', {}),
                        'model': data.get('model', '')
                    }
                elif response.status == 429:
                    raise aiohttp.ClientError("Rate limit exceeded")
                elif response.status == 401:
                    raise aiohttp.ClientError("Unauthorized")
                else:
                    error_text = await response.text()
                    raise aiohttp.ClientError(
                        f"HTTP {response.status}: {error_text}"
                    )

    def _validate_response(self, verification_code: str, response: str) -> bool:
        """验证响应是否包含验证码

        Args:
            verification_code: 发送给 AI 的验证码
            response: AI 响应内容

        Returns:
            True 如果响应包含验证码，False 否则
        """
        if not response or not verification_code:
            return False

        # 检查响应中是否包含验证码（不区分大小写）
        return verification_code.upper() in response.upper()

    def _calculate_response_score(
        self,
        response_time: float,
        is_valid: bool,
        content: str
    ) -> float:
        """计算响应质量评分 (0-100)

        Args:
            response_time: 响应时间（毫秒）
            is_valid: 响应是否有效
            content: 响应内容

        Returns:
            质量评分
        """
        score = 0.0

        # 1. 响应有效性 (50 分)
        if is_valid:
            score += 50

        # 2. 响应时间 (30 分)
        # 优秀: < 500ms = 30 分
        # 良好: < 1000ms = 20 分
        # 一般: < 2000ms = 10 分
        # 较差: >= 2000ms = 0 分
        if response_time < 500:
            score += 30
        elif response_time < 1000:
            score += 20
        elif response_time < 2000:
            score += 10

        # 3. 响应内容 (20 分)
        if content:
            # 简洁的回答更好
            if len(content) < 50:
                score += 20
            elif len(content) < 100:
                score += 15
            else:
                score += 10

        return score

    async def check_all_endpoints(
        self,
        endpoints: List
    ) -> List[ConversationalHealthCheck]:
        """并发检查所有 endpoint

        Args:
            endpoints: Endpoint 列表

        Returns:
            健康检查记录列表
        """
        # 只检查启用的 endpoint
        enabled_endpoints = [ep for ep in endpoints if ep.enabled]

        if not enabled_endpoints:
            logger.warning("没有启用的 endpoint 需要检查")
            return []

        logger.info(f"开始并发检查 {len(enabled_endpoints)} 个 endpoint")

        # 并发执行所有检查
        tasks = [
            self.check_endpoint(endpoint)
            for endpoint in enabled_endpoints
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤掉异常
        valid_results = [
            r for r in results
            if isinstance(r, ConversationalHealthCheck)
        ]

        logger.info(f"健康检查完成，成功 {len(valid_results)}/{len(results)} 个")

        return valid_results

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"ConversationalHealthChecker("
            f"model={self.model}, "
            f"timeout={self.timeout}s)"
        )
