"""
多轮对话测试脚本
测试会话管理和上下文记忆功能
"""

import requests
import json
import time


def test_multi_turn_conversation():
    """测试多轮对话"""
    print("\n" + "=" * 60)
    print("测试多轮对话")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1/risk-rules/query"
    session_id = None

    # 第一轮：询问白金卡限额
    print("\n【第 1 轮】用户: 白金卡的单笔交易限额是多少？")
    response = requests.post(
        base_url,
        json={
            "query": "白金卡的单笔交易限额是多少？",
            "session_id": session_id,
            "top_k": 5,
            "score_threshold": 0.7
        },
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        session_id = result["session_id"]
        print(f"系统: {result['answer']}")
        print(f"[session_id: {session_id}]")
        print(f"[检索到 {result['retrieved_count']} 个文档]")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return

    time.sleep(1)

    # 第二轮：追问日累计限额（使用代词"它"）
    print("\n【第 2 轮】用户: 日累计限额呢？")
    response = requests.post(
        base_url,
        json={
            "query": "日累计限额呢？",
            "session_id": session_id,
            "top_k": 5,
            "score_threshold": 0.7
        },
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        print(f"系统: {result['answer']}")
        print(f"[session_id: {result['session_id']}]")
        print(f"[检索到 {result['retrieved_count']} 个文档]")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return

    time.sleep(1)

    # 第三轮：对比金卡
    print("\n【第 3 轮】用户: 金卡的限额呢？")
    response = requests.post(
        base_url,
        json={
            "query": "金卡的限额呢？",
            "session_id": session_id,
            "top_k": 5,
            "score_threshold": 0.7
        },
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        print(f"系统: {result['answer']}")
        print(f"[session_id: {result['session_id']}]")
        print(f"[检索到 {result['retrieved_count']} 个文档]")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return

    print("\n" + "=" * 60)
    print("✅ 多轮对话测试完成")
    print("=" * 60)


def test_session_persistence():
    """测试会话持久化"""
    print("\n" + "=" * 60)
    print("测试会话持久化")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1/risk-rules/query"

    # 第一次对话
    print("\n【第 1 次对话】")
    response = requests.post(
        base_url,
        json={
            "query": "白金卡的单笔限额是多少？",
            "top_k": 5,
            "score_threshold": 0.7
        },
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        session_id = result["session_id"]
        print(f"用户: 白金卡的单笔限额是多少？")
        print(f"系统: {result['answer'][:100]}...")
        print(f"[session_id: {session_id}]")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return

    # 等待 5 秒
    print("\n⏳ 等待 5 秒...")
    time.sleep(5)

    # 第二次对话（使用相同 session_id）
    print("\n【第 2 次对话 - 5 秒后】")
    response = requests.post(
        base_url,
        json={
            "query": "日累计呢？",
            "session_id": session_id,
            "top_k": 5,
            "score_threshold": 0.7
        },
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        print(f"用户: 日累计呢？")
        print(f"系统: {result['answer'][:100]}...")
        print(f"[session_id: {result['session_id']}]")
        print("\n✅ 会话成功恢复，系统理解了上下文")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return

    print("\n" + "=" * 60)
    print("✅ 会话持久化测试完成")
    print("=" * 60)


def test_concurrent_sessions():
    """测试并发会话"""
    print("\n" + "=" * 60)
    print("测试并发会话")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1/risk-rules/query"

    # 创建两个独立会话
    sessions = []

    # 会话 1：询问白金卡
    print("\n【会话 1】用户 A: 白金卡的单笔限额是多少？")
    response = requests.post(
        base_url,
        json={"query": "白金卡的单笔限额是多少？"},
        timeout=30
    )
    if response.status_code == 200:
        result = response.json()
        sessions.append({
            "id": result["session_id"],
            "user": "A",
            "context": "白金卡"
        })
        print(f"系统: {result['answer'][:80]}...")
        print(f"[session_id: {result['session_id']}]")

    # 会话 2：询问金卡
    print("\n【会话 2】用户 B: 金卡的单笔限额是多少？")
    response = requests.post(
        base_url,
        json={"query": "金卡的单笔限额是多少？"},
        timeout=30
    )
    if response.status_code == 200:
        result = response.json()
        sessions.append({
            "id": result["session_id"],
            "user": "B",
            "context": "金卡"
        })
        print(f"系统: {result['answer'][:80]}...")
        print(f"[session_id: {result['session_id']}]")

    # 验证会话独立性
    print("\n【验证会话独立性】")

    # 会话 1 追问
    print(f"\n会话 1 (用户 A): 日累计呢？")
    response = requests.post(
        base_url,
        json={
            "query": "日累计呢？",
            "session_id": sessions[0]["id"]
        },
        timeout=30
    )
    if response.status_code == 200:
        result = response.json()
        print(f"系统: {result['answer'][:80]}...")
        if "白金" in result['answer'] or "50000" in result['answer'] or "200000" in result['answer']:
            print("✅ 会话 1 正确记忆了白金卡上下文")
        else:
            print("⚠️ 会话 1 可能丢失了上下文")

    # 会话 2 追问
    print(f"\n会话 2 (用户 B): 日累计呢？")
    response = requests.post(
        base_url,
        json={
            "query": "日累计呢？",
            "session_id": sessions[1]["id"]
        },
        timeout=30
    )
    if response.status_code == 200:
        result = response.json()
        print(f"系统: {result['answer'][:80]}...")
        if "金" in result['answer'] or "20000" in result['answer'] or "80000" in result['answer']:
            print("✅ 会话 2 正确记忆了金卡上下文")
        else:
            print("⚠️ 会话 2 可能丢失了上下文")

    print("\n" + "=" * 60)
    print("✅ 并发会话测试完成")
    print("=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("多轮对话功能测试")
    print("=" * 60)
    print("\n请确保:")
    print("1. API 服务已启动 (python -m api.main)")
    print("2. Redis 已启动 (docker-compose up -d)")
    print("3. 已导入测试数据")

    input("\n按 Enter 键开始测试...")

    try:
        # 测试 1：基础多轮对话
        test_multi_turn_conversation()

        input("\n按 Enter 键继续下一个测试...")

        # 测试 2：会话持久化
        test_session_persistence()

        input("\n按 Enter 键继续下一个测试...")

        # 测试 3：并发会话
        test_concurrent_sessions()

        print("\n" + "=" * 60)
        print("🎉 所有测试完成！")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败，请确保 API 服务已启动")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    main()
