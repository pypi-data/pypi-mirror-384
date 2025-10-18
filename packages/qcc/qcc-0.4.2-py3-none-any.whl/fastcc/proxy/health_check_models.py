"""健康检查数据模型"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class HealthCheckResult(Enum):
    """健康检查结果枚举"""
    SUCCESS = "success"              # 成功
    FAILURE = "failure"              # 失败
    TIMEOUT = "timeout"              # 超时
    RATE_LIMITED = "rate_limited"    # 被限流
    INVALID_KEY = "invalid_key"      # API Key 无效
    MODEL_ERROR = "model_error"      # 模型错误


class ConversationalHealthCheck:
    """对话式健康检查记录

    通过真实的 AI 对话测试来评估 endpoint 的健康状态和性能。
    相比传统的 ping 测试，这种方式能更准确地反映真实使用情况。
    """

    def __init__(self, endpoint_id: str):
        """初始化健康检查记录

        Args:
            endpoint_id: 被检查的 endpoint ID
        """
        self.endpoint_id = endpoint_id
        self.check_id = str(uuid.uuid4())[:8]
        self.timestamp = datetime.now().isoformat()

        # 测试消息和验证码
        self.test_message = "收到消息请回复 1"
        self.verification_code: Optional[str] = None  # 随机验证码

        # 检测结果
        self.result: Optional[HealthCheckResult] = None
        self.response_time_ms: Optional[float] = None  # 响应时间（毫秒）
        self.response_content: Optional[str] = None
        self.error_message: Optional[str] = None
        self.error_code: Optional[str] = None

        # 响应质量评估
        self.response_valid: bool = False  # 响应是否符合预期
        self.response_score: float = 0.0   # 响应质量评分 (0-100)

        # 额外信息
        self.tokens_used: Optional[int] = None
        self.model_used: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            包含所有检查信息的字典
        """
        return {
            'endpoint_id': self.endpoint_id,
            'check_id': self.check_id,
            'timestamp': self.timestamp,
            'test_message': self.test_message,
            'result': self.result.value if self.result else None,
            'response_time_ms': self.response_time_ms,
            'response_content': self.response_content,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'response_valid': self.response_valid,
            'response_score': self.response_score,
            'tokens_used': self.tokens_used,
            'model_used': self.model_used
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationalHealthCheck':
        """从字典创建实例

        Args:
            data: 包含检查信息的字典

        Returns:
            ConversationalHealthCheck 实例
        """
        check = cls(data['endpoint_id'])
        check.check_id = data.get('check_id', check.check_id)
        check.timestamp = data.get('timestamp', check.timestamp)
        check.test_message = data.get('test_message', check.test_message)

        result_str = data.get('result')
        if result_str:
            check.result = HealthCheckResult(result_str)

        check.response_time_ms = data.get('response_time_ms')
        check.response_content = data.get('response_content')
        check.error_message = data.get('error_message')
        check.error_code = data.get('error_code')
        check.response_valid = data.get('response_valid', False)
        check.response_score = data.get('response_score', 0.0)
        check.tokens_used = data.get('tokens_used')
        check.model_used = data.get('model_used')

        return check

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"ConversationalHealthCheck("
            f"endpoint={self.endpoint_id}, "
            f"result={self.result.value if self.result else 'None'}, "
            f"response_time={self.response_time_ms}ms)"
        )
