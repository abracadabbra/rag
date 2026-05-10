"""
缓存功能测试脚本
"""

import requests
import time
import json


def test_cache_performance():
    """测试缓存性能提升"""
    print("\n" + "=" * 60)
    print("测试缓存性能")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1/risk-rules/query"
    query = "白金卡的单笔交易限额是多少？"

    # 第一次查询（无缓存）
    print("\n【第 1 次查询】无缓存")
    start_time = time.time()
    response = requests.post(
        base_url,
        json={
            "query": query,
            "top_k": 5,
            "score_threshold": 0.7
        },
        timeout=30
    )
    first_time = time.time() - start_time

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 查询成功")
        print(f"   耗时: {first_time:.2f}秒")
        print(f"   答案: {result['answer'][:100]}...")
    else:
        print(f"❌ 查询失败: {response.status_code}")
        return

    # 第二次查询（有缓存）
    print("\n【第 2 次查询】有缓存")
    start_time = time.time()
    response = requests.post(
        base_url,
        json={
            "query": query,
            "top_k": 5,
            "score_threshold": 0.7
        },
        timeout=30
    )
    second_time = time.time() - start_time

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 查询成功")
        print(f"   耗时: {second_time:.2f}秒")
        print(f"   答案: {result['answer'][:100]}...")
    else:
        print(f"❌ 查询失败: {response.status_code}")
        return

    # 性能对比
    speedup = first_time / second_time if second_time > 0 else 0
    print(f"\n📊 性能对比:")
    print(f"   第 1 次（无缓存）: {first_time:.2f}秒")
    print(f"   第 2 次（有缓存）: {second_time:.2f}秒")
    print(f"   加速比: {speedup:.2f}x")

    if speedup > 5:
        print(f"   ✅ 缓存效果显著！")
    elif speedup > 2:
        print(f"   ✅ 缓存有效")
    else:
        print(f"   ⚠️  缓存效果不明显")

    print("\n" + "=" * 60)


def test_cache_stats():
    """测试缓存统计"""
    print("\n" + "=" * 60)
    print("测试缓存统计")
    print("=" * 60)

    stats_url = "http://localhost:8000/api/v1/cache/stats"

    print("\n获取缓存统计...")
    response = requests.get(stats_url, timeout=10)

    if response.status_code == 200:
        stats = response.json()
        print(f"✅ 获取成功")
        print(f"\n缓存统计:")
        print(f"   启用状态: {stats['enabled']}")
        print(f"   缓存 Key 数量: {stats['total_keys']}")
        if stats.get('memory_used_human'):
            print(f"   内存使用: {stats['memory_used_human']}")
        if stats.get('ttl'):
            print(f"   过期时间: {stats['ttl']}秒")
    else:
        print(f"❌ 获取失败: {response.status_code}")

    print("\n" + "=" * 60)


def test_cache_invalidation():
    """测试缓存清除"""
    print("\n" + "=" * 60)
    print("测试缓存清除")
    print("=" * 60)

    invalidate_url = "http://localhost:8000/api/v1/cache/invalidate"
    stats_url = "http://localhost:8000/api/v1/cache/stats"

    # 先查看当前缓存数量
    print("\n【清除前】获取缓存统计...")
    response = requests.get(stats_url, timeout=10)
    if response.status_code == 200:
        stats = response.json()
        print(f"   缓存 Key 数量: {stats['total_keys']}")

    # 清除所有查询缓存
    print("\n【清除】清空所有查询缓存...")
    response = requests.post(
        invalidate_url,
        json={},
        timeout=10
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 清除成功")
        print(f"   删除数量: {result['deleted_count']}")
        print(f"   消息: {result['message']}")
    else:
        print(f"❌ 清除失败: {response.status_code}")

    # 再次查看缓存数量
    print("\n【清除后】获取缓存统计...")
    response = requests.get(stats_url, timeout=10)
    if response.status_code == 200:
        stats = response.json()
        print(f"   缓存 Key 数量: {stats['total_keys']}")

    print("\n" + "=" * 60)


def test_cache_with_different_params():
    """测试不同参数的缓存隔离"""
    print("\n" + "=" * 60)
    print("测试缓存参数隔离")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1/risk-rules/query"
    query = "金卡的日累计限额是多少？"

    # 参数组合 1
    print("\n【参数组合 1】top_k=5, score_threshold=0.7")
    response1 = requests.post(
        base_url,
        json={
            "query": query,
            "top_k": 5,
            "score_threshold": 0.7
        },
        timeout=30
    )
    if response1.status_code == 200:
        print(f"✅ 查询成功")

    # 参数组合 2（不同参数，应该不命中缓存）
    print("\n【参数组合 2】top_k=3, score_threshold=0.7")
    response2 = requests.post(
        base_url,
        json={
            "query": query,
            "top_k": 3,
            "score_threshold": 0.7
        },
        timeout=30
    )
    if response2.status_code == 200:
        print(f"✅ 查询成功")

    # 再次使用参数组合 1（应该命中缓存）
    print("\n【参数组合 1 再次】top_k=5, score_threshold=0.7")
    start_time = time.time()
    response3 = requests.post(
        base_url,
        json={
            "query": query,
            "top_k": 5,
            "score_threshold": 0.7
        },
        timeout=30
    )
    elapsed = time.time() - start_time

    if response3.status_code == 200:
        print(f"✅ 查询成功")
        print(f"   耗时: {elapsed:.2f}秒")
        if elapsed < 0.5:
            print(f"   ✅ 命中缓存（响应很快）")
        else:
            print(f"   ⚠️  可能未命中缓存")

    print("\n" + "=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("缓存功能测试")
    print("=" * 60)
    print("\n请确保:")
    print("1. API 服务已启动 (python -m api.main)")
    print("2. Redis 已启动 (docker-compose up -d)")
    print("3. 已导入测试数据")
    print("4. 配置中 cache_enabled=True")

    input("\n按 Enter 键开始测试...")

    try:
        # 测试 1：缓存性能
        test_cache_performance()

        input("\n按 Enter 键继续下一个测试...")

        # 测试 2：缓存统计
        test_cache_stats()

        input("\n按 Enter 键继续下一个测试...")

        # 测试 3：缓存清除
        test_cache_invalidation()

        input("\n按 Enter 键继续下一个测试...")

        # 测试 4：参数隔离
        test_cache_with_different_params()

        print("\n" + "=" * 60)
        print("🎉 所有测试完成！")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败，请确保 API 服务已启动")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
