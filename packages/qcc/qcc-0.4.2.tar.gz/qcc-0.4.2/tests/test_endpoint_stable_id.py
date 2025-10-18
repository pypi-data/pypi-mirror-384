"""测试 Endpoint ID 稳定性

验证相同的 base_url + api_key 组合总是生成相同的 ID
"""

import pytest
from fastcc.core.endpoint import Endpoint


def test_stable_id_same_config():
    """测试相同配置生成相同 ID"""
    base_url = "https://api.example.com"
    api_key = "sk-test-12345"

    # 创建两个相同配置的 endpoint
    ep1 = Endpoint(base_url=base_url, api_key=api_key)
    ep2 = Endpoint(base_url=base_url, api_key=api_key)

    # 应该有相同的 ID
    assert ep1.id == ep2.id, "相同配置应该生成相同的 ID"


def test_stable_id_different_configs():
    """测试不同配置生成不同 ID"""
    ep1 = Endpoint(
        base_url="https://api1.example.com",
        api_key="sk-test-12345"
    )
    ep2 = Endpoint(
        base_url="https://api2.example.com",
        api_key="sk-test-12345"
    )
    ep3 = Endpoint(
        base_url="https://api1.example.com",
        api_key="sk-test-67890"
    )

    # 不同配置应该有不同 ID
    assert ep1.id != ep2.id, "不同 base_url 应该生成不同 ID"
    assert ep1.id != ep3.id, "不同 api_key 应该生成不同 ID"
    assert ep2.id != ep3.id, "完全不同的配置应该生成不同 ID"


def test_stable_id_with_different_metadata():
    """测试相同核心配置但不同元数据仍生成相同 ID"""
    base_url = "https://api.example.com"
    api_key = "sk-test-12345"

    ep1 = Endpoint(
        base_url=base_url,
        api_key=api_key,
        weight=100,
        priority=1,
        metadata={"env": "dev"}
    )
    ep2 = Endpoint(
        base_url=base_url,
        api_key=api_key,
        weight=50,
        priority=2,
        metadata={"env": "prod"}
    )

    # 核心配置相同，ID 应该相同（即使 weight、priority、metadata 不同）
    assert ep1.id == ep2.id, "核心配置相同时应该生成相同的 ID"


def test_id_format():
    """测试 ID 格式"""
    ep = Endpoint(
        base_url="https://api.example.com",
        api_key="sk-test-12345"
    )

    # ID 应该是 8 字符的十六进制字符串
    assert len(ep.id) == 8, "ID 长度应该是 8 个字符"
    assert all(c in '0123456789abcdef' for c in ep.id), "ID 应该是十六进制字符串"


def test_failure_queue_deduplication():
    """测试失败队列去重场景（真实使用场景）"""
    base_url = "https://api.example.com"
    api_key = "sk-test-12345"

    # 创建多个相同配置的 endpoint 实例
    ep1 = Endpoint(base_url=base_url, api_key=api_key)
    ep2 = Endpoint(base_url=base_url, api_key=api_key)
    ep3 = Endpoint(base_url=base_url, api_key=api_key)

    # 所有实例应该有相同的 ID
    assert ep1.id == ep2.id == ep3.id

    # 模拟失败队列去重逻辑
    failed_endpoints = set()
    failed_endpoints.add(ep1.id)
    failed_endpoints.add(ep2.id)  # 应该被去重
    failed_endpoints.add(ep3.id)  # 应该被去重

    # 集合中应该只有一个 endpoint ID
    assert len(failed_endpoints) == 1
    assert ep1.id in failed_endpoints


def test_from_dict_preserves_id():
    """测试从字典恢复时保持 ID 稳定性"""
    original = Endpoint(
        base_url="https://api.example.com",
        api_key="sk-test-12345"
    )

    # 序列化再反序列化
    data = original.to_dict()
    restored = Endpoint.from_dict(data)

    # ID 应该保持一致
    assert restored.id == original.id
    assert restored.base_url == original.base_url
    assert restored.api_key == original.api_key


def test_equality_and_hash_consistency():
    """测试相等性和哈希一致性"""
    ep1 = Endpoint(
        base_url="https://api.example.com",
        api_key="sk-test-12345",
        weight=100
    )
    ep2 = Endpoint(
        base_url="https://api.example.com",
        api_key="sk-test-12345",
        weight=50  # 不同的 weight
    )

    # 相等性基于 base_url + api_key
    assert ep1 == ep2, "核心配置相同应该相等"
    assert hash(ep1) == hash(ep2), "相等的对象应该有相同的哈希值"

    # ID 也应该相同
    assert ep1.id == ep2.id, "相等的对象应该有相同的 ID"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
