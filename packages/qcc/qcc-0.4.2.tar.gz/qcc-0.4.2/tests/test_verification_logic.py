"""测试验证码验证逻辑（独立测试，不依赖 aiohttp）"""

import pytest


def validate_response(verification_code: str, response: str) -> bool:
    """验证响应是否包含验证码（从 conversational_checker.py 复制）

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


def test_validate_response_basic():
    """测试基本验证码验证"""
    # 完全匹配
    assert validate_response("ABC123", "ABC123") is True
    # 包含验证码
    assert validate_response("ABC123", "这是验证码：ABC123") is True
    # 不匹配
    assert validate_response("ABC123", "XYZ789") is False
    # 空响应
    assert validate_response("ABC123", "") is False


def test_validate_response_case_insensitive():
    """测试不区分大小写"""
    assert validate_response("ABC123", "abc123") is True
    assert validate_response("abc123", "ABC123") is True
    assert validate_response("AbC123", "aBc123") is True
    assert validate_response("XYZ789", "xyz789") is True


def test_validate_response_embedded():
    """测试嵌入在文本中的验证码"""
    assert validate_response("ABC123", "前面文字 abc123 后面文字") is True
    assert validate_response("XYZ789", "The code is: xyz789!") is True
    assert validate_response("TEST99", "请确认：TEST99") is True


def test_validate_response_invalid():
    """测试无效情况"""
    # 部分匹配（不算）
    assert validate_response("ABC123", "ABC") is False
    assert validate_response("ABC123", "123") is False
    assert validate_response("ABC123", "BC12") is False

    # 有空格（不算完整匹配）
    # 注意：这个会通过，因为我们用 'in' 检查
    # 如果要严格匹配，需要修改逻辑
    assert validate_response("ABC123", "ABC 123") is False


def test_validate_response_edge_cases():
    """测试边界情况"""
    # 空验证码
    assert validate_response("", "ABC123") is False
    # None 验证码
    assert validate_response(None, "ABC123") is False
    # None 响应
    assert validate_response("ABC123", None) is False
    # 都是 None
    assert validate_response(None, None) is False


def test_verification_code_format():
    """测试验证码格式生成"""
    import re
    import random

    code_pattern = re.compile(r'^[A-Z0-9]{6}$')

    # 生成 100 个验证码
    codes = []
    for _ in range(100):
        code = ''.join(
            random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6)
        )
        codes.append(code)

        # 验证格式
        assert code_pattern.match(code), f"验证码格式错误: {code}"
        assert len(code) == 6, f"验证码长度错误: {len(code)}"

    # 检查唯一性（100 个中应该大部分不重复）
    unique_codes = set(codes)
    # 36^6 = 2,176,782,336 种可能，100 个重复概率极低
    assert len(unique_codes) > 90, f"验证码重复率过高: {len(unique_codes)}/100"


def test_real_world_scenarios():
    """测试真实场景"""
    # 场景 1：正常响应（AI 回复了验证码）
    assert validate_response("A1B2C3", "A1B2C3") is True

    # 场景 2：AI 可能加一些礼貌用语
    assert validate_response("X9Y8Z7", "好的，验证码是：X9Y8Z7") is True

    # 场景 3：被禁用的 key 返回空响应
    assert validate_response("TEST99", "") is False

    # 场景 4：错误响应（不包含验证码）
    assert validate_response("CODE88", "API key is disabled") is False

    # 场景 5：服务器返回错误 JSON（没有验证码）
    assert validate_response("VALID1", '{"error": {"message": "Bad Request"}}') is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
