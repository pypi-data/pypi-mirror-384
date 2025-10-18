"""测试失败队列的去重功能"""

import pytest
import asyncio
from pathlib import Path
from fastcc.proxy.failure_queue import FailureQueue
import pytest_asyncio


@pytest_asyncio.fixture
async def failure_queue(tmp_path):
    """创建临时失败队列"""
    storage_path = tmp_path / "test_failure_queue.json"
    queue = FailureQueue(storage_path=storage_path)
    yield queue
    await queue.stop()


@pytest.mark.asyncio
async def test_duplicate_endpoint_not_counted_twice(failure_queue):
    """测试重复添加同一个endpoint不会被计数两次"""
    endpoint_id = "test-endpoint-1"

    # 第一次添加
    await failure_queue.add_failed_endpoint(endpoint_id, "Timeout")
    assert endpoint_id in failure_queue.failed_endpoints
    assert failure_queue.stats['total_failed'] == 1
    assert len(failure_queue.failed_endpoints) == 1

    # 第二次添加（重复）
    await failure_queue.add_failed_endpoint(endpoint_id, "HTTP 500")
    assert endpoint_id in failure_queue.failed_endpoints
    assert failure_queue.stats['total_failed'] == 1  # 不应该增加
    assert len(failure_queue.failed_endpoints) == 1  # 仍然只有1个

    # 第三次添加（重复）
    await failure_queue.add_failed_endpoint(endpoint_id, "Connection error")
    assert failure_queue.stats['total_failed'] == 1  # 仍然是1
    assert len(failure_queue.failed_endpoints) == 1


@pytest.mark.asyncio
async def test_multiple_different_endpoints(failure_queue):
    """测试添加多个不同的endpoint"""
    # 添加3个不同的endpoint
    await failure_queue.add_failed_endpoint("endpoint-1", "Timeout")
    await failure_queue.add_failed_endpoint("endpoint-2", "HTTP 500")
    await failure_queue.add_failed_endpoint("endpoint-3", "Connection error")

    assert len(failure_queue.failed_endpoints) == 3
    assert failure_queue.stats['total_failed'] == 3

    # 重复添加第一个
    await failure_queue.add_failed_endpoint("endpoint-1", "Another timeout")
    assert len(failure_queue.failed_endpoints) == 3  # 仍然是3个
    assert failure_queue.stats['total_failed'] == 3  # 统计数不增加


@pytest.mark.asyncio
async def test_remove_and_readd_endpoint(failure_queue):
    """测试移除后重新添加endpoint"""
    endpoint_id = "test-endpoint"

    # 添加
    await failure_queue.add_failed_endpoint(endpoint_id, "Timeout")
    assert len(failure_queue.failed_endpoints) == 1
    assert failure_queue.stats['total_failed'] == 1

    # 移除
    await failure_queue.remove_endpoint(endpoint_id)
    assert len(failure_queue.failed_endpoints) == 0
    assert endpoint_id not in failure_queue.failed_endpoints

    # 重新添加（应该被计数）
    await failure_queue.add_failed_endpoint(endpoint_id, "HTTP 500")
    assert len(failure_queue.failed_endpoints) == 1
    assert failure_queue.stats['total_failed'] == 2  # 这次应该增加


@pytest.mark.asyncio
async def test_persistence_with_duplicates(failure_queue, tmp_path):
    """测试持久化时的去重"""
    endpoint_id = "test-endpoint"

    # 重复添加3次
    await failure_queue.add_failed_endpoint(endpoint_id, "Error 1")
    await failure_queue.add_failed_endpoint(endpoint_id, "Error 2")
    await failure_queue.add_failed_endpoint(endpoint_id, "Error 3")

    # 创建新队列并加载
    storage_path = tmp_path / "test_failure_queue.json"
    new_queue = FailureQueue(storage_path=storage_path)

    # 验证加载的数据
    assert len(new_queue.failed_endpoints) == 1
    assert endpoint_id in new_queue.failed_endpoints
    assert new_queue.stats['total_failed'] == 1  # 持久化的统计数应该正确

    await new_queue.stop()


@pytest.mark.asyncio
async def test_concurrent_add_same_endpoint(failure_queue):
    """测试并发添加同一个endpoint（线程安全）"""
    endpoint_id = "concurrent-endpoint"

    # 10个协程同时添加同一个 endpoint
    tasks = [
        failure_queue.add_failed_endpoint(endpoint_id, f"Error {i}")
        for i in range(10)
    ]

    await asyncio.gather(*tasks)

    # 验证：只应该计数一次（asyncio.Lock 确保线程安全）
    assert len(failure_queue.failed_endpoints) == 1
    assert endpoint_id in failure_queue.failed_endpoints
    assert failure_queue.stats['total_failed'] == 1  # 不应该是10


@pytest.mark.asyncio
async def test_concurrent_add_different_endpoints(failure_queue):
    """测试并发添加不同的endpoint"""
    # 10个协程同时添加不同的 endpoint
    tasks = [
        failure_queue.add_failed_endpoint(f"endpoint-{i}", f"Error {i}")
        for i in range(10)
    ]

    await asyncio.gather(*tasks)

    # 验证：所有 endpoint 都应该被添加
    assert len(failure_queue.failed_endpoints) == 10
    assert failure_queue.stats['total_failed'] == 10


@pytest.mark.asyncio
async def test_concurrent_add_and_remove(failure_queue):
    """测试并发添加和移除操作"""
    endpoint_id = "test-endpoint"

    # 先添加一个 endpoint
    await failure_queue.add_failed_endpoint(endpoint_id, "Initial error")

    # 并发执行添加和移除操作
    tasks = [
        failure_queue.add_failed_endpoint(endpoint_id, "Error 1"),
        failure_queue.add_failed_endpoint(endpoint_id, "Error 2"),
        failure_queue.remove_endpoint(endpoint_id),
        failure_queue.add_failed_endpoint(endpoint_id, "Error 3"),
    ]

    await asyncio.gather(*tasks)

    # 验证：最终状态应该一致（可能在队列中，也可能不在）
    # 由于移除操作的时机不确定，我们只验证数据一致性
    if endpoint_id in failure_queue.failed_endpoints:
        # 如果在队列中，统计数应该是 2（初始1次 + 重新添加1次）
        assert failure_queue.stats['total_failed'] == 2
    else:
        # 如果不在队列中，说明移除操作最后执行
        assert failure_queue.stats['total_failed'] == 1
