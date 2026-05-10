"""
澄清机制测试脚本
"""

import requests
import json


def test_clarification_vague_query():
    """测试模糊问题的澄清"""
    print("\n" + "=" * 60)
    print("测试澄清机制 - 模糊问题")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1/risk-rules/query"

    # 第一轮：提出模糊问题
    print("\n【第 1 轮】用户: 限额是多少？")
    response = requests.post(
        base_url,
        json={
            "query": "限额是多少？",
            "top_k": 5,
            "score_threshold": 0.7
        },
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        session_id = result["session_id"]

        if result.get("needs_clarification"):
            print(f"系统: {result['answer']}")
            print("\n澄清选项:")
            for i, option in enumerate(result["clarification_options"], 1):
                print(f"  {i}. {option}")
            print(f"\n[session_id: {session_id}]")
            print(f"[needs_clarification: True]")

            # 第二轮：用户选择澄清选项
            if result["clarification_options"]:
                choice = result["clarification_options"][0]
                print(f"\n【第 2 轮】用户选择: {choice}")

                response = requests.post(
                    base_url,
                    json={
                        "query": "限额是多少？",
                        "session_id": session_id,
                        "clarification_choice": choice,
                        "top_k": 5,
                        "score_threshold": 0.7
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    print(f"系统: {result['answer'][:200]}...")
                    print(f"\n[检索到 {result['retrieved_count']} 个文档]")
                    print("✅ 澄清后成功获取答案")
                else:
                    print(f"❌ 请求失败: {response.status_code}")
        else:
            print(f"系统: {result['answer']}")
            print("\n⚠️ 未触发澄清机制")
    else:
        print(f"❌ 请求失败: {response.status_code}")

    print("\n" + "=" * 60)


def test_clarification_with_context():
    """测试有上下文的澄清"""
    print("\n" + "=" * 60)
    print("测试澄清机制 - 有上下文")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1/risk-rules/query"

    # 第一轮：明确问题
    print("\n【第 1 轮】用户: 白金卡的单笔限额是多少？")
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
        print(f"系统: {result['answer'][:100]}...")
        print(f"[session_id: {session_id}]")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return

    # 第二轮：模糊追问（有上下文，应该不需要澄清）
    print("\n【第 2 轮】用户: 日累计呢？")
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

        if result.get("needs_clarification"):
            print(f"系统: {result['answer']}")
            print("\n澄清选项:")
            for i, option in enumerate(result["clarification_options"], 1):
                print(f"  {i}. {option}")
            print("\n⚠️ 触发了澄清（可能是因为上下文不够明确）")
        else:
            print(f"系统: {result['answer'][:100]}...")
            print("\n✅ 基于上下文直接回答，未触发澄清")
    else:
        print(f"❌ 请求失败: {response.status_code}")

    print("\n" + "=" * 60)


def test_no_clarification_needed():
    """测试明确问题不需要澄清"""
    print("\n" + "=" * 60)
    print("测试澄清机制 - 明确问题")
    print("=" * 60)

    base_url = "http://localhost:8000/api/v1/risk-rules/query"

    print("\n用户: 白金卡的单笔交易限额是多少？")
    response = requests.post(
        base_url,
        json={
            "query": "白金卡的单笔交易限额是多少？",
            "top_k": 5,
            "score_threshold": 0.7
        },
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()

        if result.get("needs_clarification"):
            print(f"系统: {result['answer']}")
            print("\n澄清选项:")
            for i, option in enumerate(result["clarification_options"], 1):
                print(f"  {i}. {option}")
            print("\n⚠️ 明确问题触发了澄清（不应该）")
        else:
            print(f"系统: {result['answer'][:100]}...")
            print(f"\n[检索到 {result['retrieved_count']} 个文档]")
            print("✅ 明确问题直接回答，未触发澄清")
    else:
        print(f"❌ 请求失败: {response.status_code}")

    print("\n" + "=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("澄清机制测试")
    print("=" * 60)
    print("\n请确保:")
    print("1. API 服务已启动 (python -m api.main)")
    print("2. Redis 已启动 (docker-compose up -d)")
    print("3. 已导入测试数据")

    input("\n按 Enter 键开始测试...")

    try:
        # 测试 1：模糊问题触发澄清
        test_clarification_vague_query()

        input("\n按 Enter 键继续下一个测试...")

        # 测试 2：有上下文的模糊问题
        test_clarification_with_context()

        input("\n按 Enter 键继续下一个测试...")

        # 测试 3：明确问题不需要澄清
        test_no_clarification_needed()

        print("\n" + "=" * 60)
        print("🎉 所有测试完成！")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败，请确保 API 服务已启动")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")


if __name__ == "__main__":
    main()
