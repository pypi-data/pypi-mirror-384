"""测试验证码验证机制

验证新的验证码机制能够正确识别有效和无效的响应
"""

import pytest
from fastcc.proxy.conversational_checker import ConversationalHealthChecker


def test_validate_response_with_verification_code():
    """测试验证码验证逻辑"""
    checker = ConversationalHealthChecker()

    # 测试用例
    test_cases = [
        # (verification_code, response, expected_valid)
        ("ABC123", "ABC123", True),  # 完全匹配
        ("ABC123", "这是验证码：ABC123", True),  # 包含验证码
        ("ABC123", "abc123", True),  # 不区分大小写
        ("ABC123", "Abc123", True),  # 混合大小写
        ("ABC123", "前面文字 abc123 后面文字", True),  # 中间包含
        ("ABC123", "XYZ789", False),  # 不匹配
        ("ABC123", "", False),  # 空响应
        ("ABC123", "ABC", False),  # 部分匹配（不算）
        ("ABC123", "ABC 123", False),  # 有空格（不算）
        ("", "ABC123", False),  # 空验证码
        (None, "ABC123", False),  # None 验证码
        ("ABC123", None, False),  # None 响应
    ]

    for i, (code, response, expected) in enumerate(test_cases, 1):
        result = checker._validate_response(code, response)
        assert result == expected, (
            f"测试用例 {i} 失败: "
            f"code='{code}', response='{response}', "
            f"expected={expected}, got={result}"
        )


def test_verification_code_generation():
    """测试验证码生成"""
    import re

    # 验证码应该是 6 位字母数字组合
    code_pattern = re.compile(r'^[A-Z0-9]{6}$')

    # 生成多个验证码，确保格式正确且不重复
    codes = set()
    for _ in range(100):
        # 模拟生成验证码的逻辑
        import random
        code = ''.join(
            random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6)
        )

        # 验证格式
        assert code_pattern.match(code), f"验证码格式错误: {code}"

        # 收集用于检查重复
        codes.add(code)

    # 100 次生成应该有很高的唯一性（理论上可能重复，但概率极低）
    # 36^6 = 2,176,782,336 种可能
    assert len(codes) > 90, "验证码重复率过高"


def test_validation_case_insensitive():
    """测试验证码不区分大小写"""
    checker = ConversationalHealthChecker()

    test_cases = [
        ("ABC123", "abc123"),
        ("abc123", "ABC123"),
        ("AbC123", "aBc123"),
        ("XYZ789", "xyz789"),
    ]

    for code, response in test_cases:
        assert checker._validate_response(code, response), (
            f"应该验证通过: code='{code}', response='{response}'"
        )


def test_validation_strict_match():
    """测试验证码需要完整匹配"""
    checker = ConversationalHealthChecker()

    # 这些不应该通过验证
    invalid_cases = [
        ("ABC123", "ABC"),  # 只有前缀
        ("ABC123", "123"),  # 只有后缀
        ("ABC123", "BC12"),  # 中间部分
        ("ABC123", "ABC 123"),  # 有空格
        ("ABC123", "A B C 1 2 3"),  # 分散
        ("ABC123", "ABCD123"),  # 多了字符
    ]

    for code, response in invalid_cases:
        assert not checker._validate_response(code, response), (
            f"不应该验证通过: code='{code}', response='{response}'"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
