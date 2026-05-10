"""
缓存服务单元测试
"""

from api.services.cache_service import CacheService
from tests.fakes import FakeRedis


def test_cache_key_contains_scene_type_prefix():
    cache = CacheService(redis_client=FakeRedis(), ttl=60)

    cache_key = cache._generate_cache_key(
        query="白金卡限额",
        scene_type="risk_rule",
        top_k=5,
        score_threshold=0.7,
    )

    assert cache_key.startswith("rag:query:risk_rule:")


def test_cache_set_and_get_round_trip():
    redis_client = FakeRedis()
    cache = CacheService(redis_client=redis_client, ttl=120)
    result = {"answer": "50,000 元", "retrieved_count": 1}

    saved = cache.set(
        query="白金卡的单笔交易限额是多少？",
        scene_type="risk_rule",
        top_k=5,
        score_threshold=0.7,
        result=result,
    )

    assert saved is True
    assert len(redis_client.store) == 1

    cached = cache.get(
        query="白金卡的单笔交易限额是多少？",
        scene_type="risk_rule",
        top_k=5,
        score_threshold=0.7,
    )

    assert cached == result


def test_invalidate_by_scene_type_only_removes_matching_entries():
    redis_client = FakeRedis()
    cache = CacheService(redis_client=redis_client, ttl=120)

    cache.set("问题1", "risk_rule", 5, 0.7, {"answer": "A"})
    cache.set("问题2", "model_card", 5, 0.7, {"answer": "B"})

    deleted = cache.invalidate(scene_type="risk_rule")

    assert deleted == 1
    assert len(redis_client.store) == 1
    remaining_key = next(iter(redis_client.store))
    assert remaining_key.startswith("rag:query:model_card:")


def test_cache_stats_report_key_count_and_ttl():
    redis_client = FakeRedis()
    cache = CacheService(redis_client=redis_client, ttl=300)

    cache.set("问题1", "risk_rule", 5, 0.7, {"answer": "A"})
    cache.set("问题2", "risk_rule", 3, 0.5, {"answer": "B"})

    stats = cache.get_stats()

    assert stats["enabled"] is True
    assert stats["total_keys"] == 2
    assert stats["ttl"] == 300
