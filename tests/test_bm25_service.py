"""
BM25 服务单元测试
"""

import pytest
import tempfile
import os

from api.services.bm25_service import (
    BM25Indexer,
    BM25Searcher,
    compute_bm25_scores_dynamic,
)
from api.services.hybrid_search import (
    reciprocal_rank_fusion,
    hybrid_search
)


class TestBM25Indexer:
    """BM25 索引器测试"""

    def test_build_and_search(self):
        """测试索引构建和搜索"""
        indexer = BM25Indexer(index_dir=tempfile.mkdtemp())

        docs = [
            {"id": "1", "content": "信用卡单笔交易限额是5万元", "scene_type": "risk_rule", "metadata": {"rule_id": "R001"}},
            {"id": "2", "content": "白金卡的日累计限额是20万元", "scene_type": "risk_rule", "metadata": {"rule_id": "R002"}},
            {"id": "3", "content": "金卡单日限额10万元", "scene_type": "risk_rule", "metadata": {"rule_id": "R003"}},
        ]

        indexer.build_index(docs)
        results = indexer.search("信用卡限额", top_k=2)

        assert len(results) == 2
        assert results[0]["id"] == "1"  # 应该返回 id=1，因为内容更相关
        assert "bm25_score" in results[0]

    def test_scene_filter(self):
        """测试场景过滤"""
        indexer = BM25Indexer(index_dir=tempfile.mkdtemp())

        docs = [
            {"id": "1", "content": "信用卡规则", "scene_type": "risk_rule", "metadata": {}},
            {"id": "2", "content": "信用卡规则", "scene_type": "model_card", "metadata": {}},
        ]

        indexer.build_index(docs)

        # 只搜索 risk_rule 场景
        results = indexer.search("信用卡", scene_type="risk_rule", top_k=10)
        assert all(r["scene_type"] == "risk_rule" for r in results)
        assert len(results) == 1

    def test_save_and_load(self):
        """测试索引保存和加载"""
        temp_dir = tempfile.mkdtemp()
        indexer = BM25Indexer(index_dir=temp_dir)

        docs = [
            {"id": "1", "content": "测试文档", "scene_type": "risk_rule", "metadata": {}},
        ]

        indexer.build_index(docs)
        indexer.save_index()

        # 重新创建索引器并加载
        new_indexer = BM25Indexer(index_dir=temp_dir)
        loaded = new_indexer.load_index()

        assert loaded is True
        results = new_indexer.search("测试", top_k=1)
        assert len(results) == 1
        assert results[0]["id"] == "1"


class TestBM25Searcher:
    """BM25 动态搜索器测试"""

    def test_dynamic_search(self):
        """测试动态搜索"""
        searcher = BM25Searcher()

        docs = [
            {"id": "1", "content": "信用卡单笔限额5万元", "scene_type": "risk_rule"},
            {"id": "2", "content": "白金卡日限额20万元", "scene_type": "risk_rule"},
            {"id": "3", "content": "金卡单日限额10万元", "scene_type": "risk_rule"},
        ]

        searcher.index_documents(docs)
        results = searcher.search("信用卡限额", top_k=2)

        assert len(results) == 2
        assert results[0]["bm25_score"] >= results[1]["bm25_score"]

    def test_empty_corpus(self):
        """测试空语料库"""
        searcher = BM25Searcher()
        results = searcher.search("测试", top_k=5)
        assert results == []


class TestHybridSearch:
    """混合检索测试"""

    def test_reciprocal_rank_fusion(self):
        """测试 RRF 融合"""
        vec_results = [
            {"id": "1", "content": "信用卡", "score": 0.95},
            {"id": "2", "content": "借记卡", "score": 0.85},
            {"id": "3", "content": "手机银行", "score": 0.75},
        ]

        bm25_results = [
            {"id": "1", "content": "信用卡", "bm25_score": 8.5},
            {"id": "4", "content": "信用卡年费", "bm25_score": 7.2},
            {"id": "2", "content": "借记卡", "bm25_score": 6.8},
        ]

        fused = reciprocal_rank_fusion([vec_results, bm25_results])

        # 应该返回 4 个唯一文档
        assert len(fused) == 4

        # 检查排序（id=1 应该在最前，因为两个检索系统都返回了它）
        assert fused[0]["id"] == "1"

        # 检查 rrf_score 存在
        assert "rrf_score" in fused[0]

    def test_reciprocal_rank_fusion_single_list(self):
        """测试单列表 RRF"""
        results = [{"id": "1"}, {"id": "2"}]
        fused = reciprocal_rank_fusion([results])
        assert fused == results

    def test_reciprocal_rank_fusion_empty(self):
        """测试空输入"""
        fused = reciprocal_rank_fusion([])
        assert fused == []

    def test_hybrid_search_weighted(self):
        """测试加权混合搜索"""
        vec_results = [
            {"id": "1", "content": "信用卡", "score": 0.95},
            {"id": "2", "content": "借记卡", "score": 0.85},
        ]

        bm25_results = [
            {"id": "1", "content": "信用卡", "bm25_score": 8.5},
            {"id": "3", "content": "信用卡年费", "bm25_score": 7.2},
        ]

        hybrid = hybrid_search(vec_results, bm25_results, vector_weight=0.6, top_k=3)

        assert len(hybrid) == 3
        assert "hybrid_score" in hybrid[0]

    def test_hybrid_search_single_source(self):
        """测试单一来源"""
        vec_results = [
            {"id": "1", "content": "信用卡", "score": 0.95},
        ]

        hybrid = hybrid_search(vec_results, [], vector_weight=0.6, top_k=2)
        assert len(hybrid) == 1
        assert hybrid[0]["id"] == "1"
