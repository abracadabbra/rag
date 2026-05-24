"""
Reranker 服务单元测试
使用 mock 避免加载真实模型
"""

import pytest
from unittest.mock import patch, MagicMock

from api.services.rerank_service import BGEReranker, reset_reranker


@pytest.fixture
def mock_cross_encoder():
    """Mock CrossEncoder 模型"""
    mock_model = MagicMock()
    with patch("sentence_transformers.CrossEncoder", return_value=mock_model):
        yield mock_model


@pytest.fixture
def reranker(mock_cross_encoder):
    """创建使用 mock 模型的 reranker"""
    return BGEReranker(model_name="test-model", device="cpu", top_k=3)


class TestBGEReranker:
    """BGE Reranker 测试"""

    def test_rerank_empty_documents(self, reranker):
        result = reranker.rerank("query", [])
        assert result == []

    def test_rerank_returns_top_k(self, reranker, mock_cross_encoder):
        docs = [
            {"content": "doc1", "metadata": {}},
            {"content": "doc2", "metadata": {}},
            {"content": "doc3", "metadata": {}},
            {"content": "doc4", "metadata": {}},
        ]
        mock_cross_encoder.predict.return_value = [0.1, 0.9, 0.5, 0.3]

        results = reranker.rerank("query", docs, top_k=2)
        assert len(results) == 2

    def test_rerank_sorted_by_score(self, reranker, mock_cross_encoder):
        docs = [
            {"content": "low", "metadata": {}},
            {"content": "high", "metadata": {}},
            {"content": "mid", "metadata": {}},
        ]
        mock_cross_encoder.predict.return_value = [0.1, 0.9, 0.5]

        results = reranker.rerank("query", docs)
        assert results[0]["content"] == "high"
        assert results[1]["content"] == "mid"
        assert results[2]["content"] == "low"

    def test_rerank_score_added(self, reranker, mock_cross_encoder):
        docs = [{"content": "doc1", "metadata": {"id": "1"}}]
        mock_cross_encoder.predict.return_value = [0.85]

        results = reranker.rerank("query", docs)
        assert results[0]["rerank_score"] == pytest.approx(0.85)
        assert results[0]["metadata"] == {"id": "1"}

    def test_rerank_uses_default_top_k(self, reranker, mock_cross_encoder):
        docs = [{"content": f"doc{i}", "metadata": {}} for i in range(5)]
        mock_cross_encoder.predict.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]

        results = reranker.rerank("query", docs)
        assert len(results) == 3  # default top_k

    def test_rerank_predict_failure_fallback(self, reranker, mock_cross_encoder):
        docs = [
            {"content": "doc1", "metadata": {}},
            {"content": "doc2", "metadata": {}},
        ]
        mock_cross_encoder.predict.side_effect = RuntimeError("model error")

        results = reranker.rerank("query", docs, top_k=1)
        assert len(results) == 1
        assert results[0]["content"] == "doc1"

    def test_rerank_with_numpy_scores(self, reranker, mock_cross_encoder):
        """测试 numpy 数组类型的 scores"""
        import numpy as np

        docs = [{"content": "doc1", "metadata": {}}, {"content": "doc2", "metadata": {}}]
        mock_cross_encoder.predict.return_value = np.array([0.3, 0.8])

        results = reranker.rerank("query", docs)
        assert results[0]["content"] == "doc2"
        assert results[0]["rerank_score"] == pytest.approx(0.8)


class TestRerankerSingleton:
    """Reranker 单例管理测试"""

    def teardown_method(self):
        reset_reranker()

    @patch("sentence_transformers.CrossEncoder")
    @patch("api.services.rerank_service.settings")
    @patch("api.services.rerank_service.torch")
    def test_get_reranker_singleton(self, mock_torch, mock_settings, mock_ce):
        from api.services.rerank_service import get_reranker

        mock_torch.cuda.is_available.return_value = False
        mock_settings.rerank_model = "test-model"
        mock_settings.rerank_top_k = 3

        r1 = get_reranker()
        r2 = get_reranker()
        assert r1 is r2

    def test_reset_reranker(self):
        reset_reranker()
        import api.services.rerank_service as mod
        assert mod._reranker is None
