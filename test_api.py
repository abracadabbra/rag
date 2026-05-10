"""
API 测试脚本
用于验证 API 路由和日志功能
"""

import requests
import json


def test_health():
    """测试综合健康检查"""
    print("\n=== 测试综合健康检查 ===")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"整体状态: {result['status']}")
        print(f"版本: {result['version']}")
        print(f"环境: {result['environment']}")
        print("\n依赖服务状态:")
        for service, check in result.get('checks', {}).items():
            status_icon = "✅" if check['status'] == 'healthy' else "❌"
            print(f"  {status_icon} {service}: {check['status']}")
            if check['status'] != 'healthy' and 'error' in check:
                print(f"     错误: {check['error']}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")


def test_health_individual():
    """测试各个服务的独立健康检查"""
    print("\n=== 测试独立健康检查 ===")

    services = ["milvus", "redis", "openai"]

    for service in services:
        try:
            response = requests.get(f"http://localhost:8000/health/{service}")
            result = response.json()
            status_icon = "✅" if result['status'] == 'healthy' else "❌"
            print(f"{status_icon} {service}: {result['status']}")
            if result['status'] != 'healthy' and 'error' in result:
                print(f"   错误: {result['error']}")
        except Exception as e:
            print(f"❌ {service}: 请求失败 - {e}")


def test_root():
    """测试根路径"""
    print("\n=== 测试根路径 ===")
    try:
        response = requests.get("http://localhost:8000/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")


def test_risk_rules_query():
    """测试风控规则查询"""
    print("\n=== 测试风控规则查询 ===")

    # 测试数据
    payload = {
        "query": "白金卡的单笔交易限额是多少？",
        "session_id": None,
        "top_k": 5,
        "score_threshold": 0.7
    }

    print(f"请求路径: POST http://localhost:8000/api/v1/risk-rules/query")
    print(f"请求数据: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/risk-rules/query",
            json=payload,
            timeout=30
        )
        print(f"\n状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"答案: {result['answer']}")
            print(f"检索到的文档数: {result['retrieved_count']}")
            print(f"来源数量: {len(result['sources'])}")

            if result['sources']:
                print("\n来源详情:")
                for i, source in enumerate(result['sources'], 1):
                    print(f"  [{i}] 分数: {source['score']}")
                    if 'rule_id' in source:
                        print(f"      规则ID: {source['rule_id']}")
                    if 'rule_name' in source:
                        print(f"      规则名称: {source['rule_name']}")
                    print(f"      内容预览: {source['content_preview'][:100]}...")
        else:
            print(f"错误响应: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保 API 服务已启动")
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 请求失败: {e}")


def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")

    # 测试空查询
    print("\n1. 测试空查询:")
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/risk-rules/query",
            json={"query": ""},
            timeout=5
        )
        print(f"   状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"   错误信息: {response.json()}")
    except Exception as e:
        print(f"   ❌ {e}")

    # 测试无效参数
    print("\n2. 测试无效参数:")
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/risk-rules/query",
            json={"query": "测试", "top_k": -1},
            timeout=5
        )
        print(f"   状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"   错误信息: {response.json()}")
    except Exception as e:
        print(f"   ❌ {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("RAG API 测试")
    print("=" * 60)

    # 测试健康检查
    test_health()
    test_health_individual()

    # 测试基础端点
    test_root()

    # 测试风控规则查询
    test_risk_rules_query()

    # 测试错误处理
    test_error_handling()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
