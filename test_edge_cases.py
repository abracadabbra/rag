"""
边界条件测试
测试各种异常输入和边界情况
"""

import requests
import json


def test_empty_query():
    """测试空查询"""
    print("\n" + "=" * 60)
    print("测试 1：空查询")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1/risk-rules/query"

    test_cases = [
        ("空字符串", ""),
        ("只有空格", "   "),
        ("只有换行", "\n\n"),
    ]

    for name, query in test_cases:
        print(f"\n【{name}】query: '{query}'")
        try:
            response = requests.post(
                base_url,
                json={"query": query},
                timeout=10
            )

            if response.status_code == 422:
                print(f"✅ 正确拒绝（422 Validation Error）")
            elif response.status_code == 400:
                print(f"✅ 正确拒绝（400 Bad Request）")
            elif response.status_code == 200:
                result = response.json()
                print(f"⚠️  接受了空查询")
                print(f"   答案: {result.get('answer', '')[:100]}")
            else:
                print(f"❌ 意外状态码: {response.status_code}")

        except Exception as e:
            print(f"❌ 请求失败: {e}")

    print("\n" + "=" * 60)


def test_very_long_query():
    """测试超长查询"""
    print("\n" + "=" * 60)
    print("测试 2：超长查询")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1/risk-rules/query"

    test_cases = [
        ("正常长度", "白金卡的单笔交易限额是多少？", True),
        ("较长查询", "我想了解一下关于白金卡、金卡和普卡的单笔交易限额、日累计限额以及月累计限额的详细规则，特别是在境外交易和网络交易场景下的限制。" * 5, True),
        ("超长查询", "白金卡" * 500, False),  # 1000+ 字符
    ]

    for name, query, should_succeed in test_cases:
        print(f"\n【{name}】长度: {len(query)} 字符")
        try:
            response = requests.post(
                base_url,
                json={"query": query},
                timeout=30
            )

            if response.status_code == 200:
                if should_succeed:
                    print(f"✅ 查询成功")
                else:
                    print(f"⚠️  超长查询被接受（可能需要限制）")
            elif response.status_code == 422:
                if not should_succeed:
                    print(f"✅ 正确拒绝（超过长度限制）")
                else:
                    print(f"❌ 正常查询被拒绝")
            else:
                print(f"状态码: {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"⚠️  请求超时（可能需要优化）")
        except Exception as e:
            print(f"❌ 请求失败: {e}")

    print("\n" + "=" * 60)


def test_special_characters():
    """测试特殊字符"""
    print("\n" + "=" * 60)
    print("测试 3：特殊字符")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1/risk-rules/query"

    test_cases = [
        ("SQL 注入", "'; DROP TABLE users; --"),
        ("HTML 标签", "<script>alert('xss')</script>"),
        ("特殊符号", "!@#$%^&*()_+-=[]{}|;':\",./<>?"),
        ("Emoji", "白金卡的限额是多少？😊💳"),
        ("换行符", "白金卡\n的限额\n是多少？"),
        ("制表符", "白金卡\t的限额\t是多少？"),
    ]

    for name, query in test_cases:
        print(f"\n【{name}】query: {query[:50]}...")
        try:
            response = requests.post(
                base_url,
                json={"query": query},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ 查询成功（已处理特殊字符）")
                print(f"   答案: {result.get('answer', '')[:80]}...")
            elif response.status_code == 400:
                print(f"⚠️  被拒绝（可能过于严格）")
            else:
                print(f"状态码: {response.status_code}")

        except Exception as e:
            print(f"❌ 请求失败: {e}")

    print("\n" + "=" * 60)


def test_invalid_parameters():
    """测试无效参数"""
    print("\n" + "=" * 60)
    print("测试 4：无效参数")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1/risk-rules/query"

    test_cases = [
        ("负数 top_k", {"query": "白金卡限额", "top_k": -1}),
        ("超大 top_k", {"query": "白金卡限额", "top_k": 1000}),
        ("负数阈值", {"query": "白金卡限额", "score_threshold": -0.5}),
        ("超大阈值", {"query": "白金卡限额", "score_threshold": 2.0}),
        ("错误类型 top_k", {"query": "白金卡限额", "top_k": "abc"}),
        ("错误类型阈值", {"query": "白金卡限额", "score_threshold": "high"}),
        ("无效 session_id", {"query": "白金卡限额", "session_id": "invalid-uuid"}),
    ]

    for name, params in test_cases:
        print(f"\n【{name}】params: {params}")
        try:
            response = requests.post(
                base_url,
                json=params,
                timeout=10
            )

            if response.status_code == 422:
                print(f"✅ 正确拒绝（422 Validation Error）")
                error = response.json()
                if 'detail' in error:
                    print(f"   错误信息: {error['detail'][0]['msg']}")
            elif response.status_code == 400:
                print(f"✅ 正确拒绝（400 Bad Request）")
            elif response.status_code == 200:
                print(f"⚠️  接受了无效参数（可能需要更严格验证）")
            else:
                print(f"状态码: {response.status_code}")

        except Exception as e:
            print(f"❌ 请求失败: {e}")

    print("\n" + "=" * 60)


def test_concurrent_requests():
    """测试并发请求"""
    print("\n" + "=" * 60)
    print("测试 5：并发请求")
    print("=" * 60)

    import concurrent.futures
    import time

    base_url = "http://localhost:8000/api/v1/risk-rules/query"

    def make_request(i):
        """发送单个请求"""
        try:
            start = time.time()
            response = requests.post(
                base_url,
                json={"query": f"白金卡的限额是多少？{i}"},
                timeout=30
            )
            elapsed = time.time() - start
            return {
                "index": i,
                "status": response.status_code,
                "time": elapsed,
                "success": response.status_code == 200
            }
        except Exception as e:
            return {
                "index": i,
                "status": 0,
                "time": 0,
                "success": False,
                "error": str(e)
            }

    # 并发 10 个请求
    print("\n发送 10 个并发请求...")
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, i) for i in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    total_time = time.time() - start_time

    # 统计结果
    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count
    avg_time = sum(r["time"] for r in results if r["success"]) / max(success_count, 1)

    print(f"\n📊 并发测试结果:")
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   成功: {success_count}/10")
    print(f"   失败: {failed_count}/10")
    print(f"   平均响应时间: {avg_time:.2f}秒")

    if success_count == 10:
        print(f"   ✅ 所有请求成功")
    elif success_count >= 8:
        print(f"   ⚠️  部分请求失败")
    else:
        print(f"   ❌ 大量请求失败")

    print("\n" + "=" * 60)


def test_missing_dependencies():
    """测试依赖服务不可用"""
    print("\n" + "=" * 60)
    print("测试 6：依赖服务检查")
    print("=" * 60)

    health_url = "http://localhost:8000/health"

    print("\n检查服务健康状态...")
    try:
        response = requests.get(health_url, timeout=10)

        if response.status_code == 200:
            health = response.json()
            print(f"✅ 服务健康")
            print(f"\n各组件状态:")
            for component, status in health.items():
                if component == "status":
                    continue
                if isinstance(status, dict):
                    comp_status = status.get("status", "unknown")
                    icon = "✅" if comp_status == "healthy" else "❌"
                    print(f"   {icon} {component}: {comp_status}")
                    if "error" in status:
                        print(f"      错误: {status['error']}")
        else:
            print(f"⚠️  服务状态异常: {response.status_code}")

    except Exception as e:
        print(f"❌ 健康检查失败: {e}")

    print("\n" + "=" * 60)


def test_session_edge_cases():
    """测试会话边界情况"""
    print("\n" + "=" * 60)
    print("测试 7：会话边界情况")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1/risk-rules/query"

    # 测试 1：使用不存在的 session_id
    print("\n【测试 1】使用不存在的 session_id")
    response = requests.post(
        base_url,
        json={
            "query": "白金卡限额",
            "session_id": "non-existent-session-12345"
        },
        timeout=10
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 自动创建新会话")
        print(f"   返回 session_id: {result.get('session_id', '')[:20]}...")
    else:
        print(f"❌ 请求失败: {response.status_code}")

    # 测试 2：快速连续请求同一会话
    print("\n【测试 2】快速连续请求同一会话")
    session_id = None

    for i in range(3):
        response = requests.post(
            base_url,
            json={
                "query": f"问题 {i+1}",
                "session_id": session_id
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            session_id = result.get("session_id")
            print(f"   请求 {i+1}: ✅ 成功")
        else:
            print(f"   请求 {i+1}: ❌ 失败")

    print("\n" + "=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("边界条件测试")
    print("=" * 60)
    print("\n请确保:")
    print("1. API 服务已启动 (python -m api.main)")
    print("2. Redis 已启动")
    print("3. Milvus 已启动")
    print("4. 已导入测试数据")

    input("\n按 Enter 键开始测试...")

    try:
        # 测试 1：空查询
        test_empty_query()
        input("\n按 Enter 键继续...")

        # 测试 2：超长查询
        test_very_long_query()
        input("\n按 Enter 键继续...")

        # 测试 3：特殊字符
        test_special_characters()
        input("\n按 Enter 键继续...")

        # 测试 4：无效参数
        test_invalid_parameters()
        input("\n按 Enter 键继续...")

        # 测试 5：并发请求
        test_concurrent_requests()
        input("\n按 Enter 键继续...")

        # 测试 6：依赖服务
        test_missing_dependencies()
        input("\n按 Enter 键继续...")

        # 测试 7：会话边界
        test_session_edge_cases()

        print("\n" + "=" * 60)
        print("🎉 所有边界条件测试完成！")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败，请确保 API 服务已启动")
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
