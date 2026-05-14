"""
BM25 检索模块
支持预构建索引和动态计算两种模式
"""

import os
import json
import pickle
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# 需要安装: pip install rank-bm25


class BM25Indexer:
    """BM25 索引器"""

    def __init__(self, index_dir: str = "data/bm25_index"):
        """
        初始化 BM25 索引器

        Args:
            index_dir: 索引存储目录
        """
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.index_dir / "bm25_index.pkl"
        self.corpus_file = self.index_dir / "corpus.json"

        self.index = None
        self.corpus = []  # List[{"id": str, "content": str, "scene_type": str, "metadata": dict}]
        self.doc_ids = []

    def build_index(self, documents: List[Dict[str, Any]]) -> None:
        """
        从文档构建 BM25 索引

        Args:
            documents: 文档列表，每项包含 id, content, scene_type, metadata
        """
        from rank_bm25 import BM25Okapi

        logger.info(f"构建 BM25 索引，文档数: {len(documents)}")

        self.corpus = []
        tokenized_corpus = []

        for doc in documents:
            content = doc.get("content", "")
            doc_id = doc.get("id", str(len(self.corpus)))

            self.corpus.append({
                "id": doc_id,
                "content": content,
                "scene_type": doc.get("scene_type", ""),
                "metadata": doc.get("metadata", {})
            })

            # 分词（简单按空格分，可替换为更复杂的分词器）
            tokens = content.lower().split()
            tokenized_corpus.append(tokens)

        self.index = BM25Okapi(tokenized_corpus)
        self.doc_ids = [d["id"] for d in self.corpus]

        logger.info(f"BM25 索引构建完成，文档数: {len(self.corpus)}")

    def save_index(self) -> None:
        """保存索引到磁盘"""
        if self.index is None:
            logger.warning("没有索引可保存")
            return

        logger.info(f"保存 BM25 索引到 {self.index_file}")

        with open(self.index_file, "wb") as f:
            pickle.dump(self.index, f)

        with open(self.corpus_file, "w", encoding="utf-8") as f:
            json.dump(self.corpus, f, ensure_ascii=False)

        logger.info("BM25 索引保存完成")

    def load_index(self) -> bool:
        """从磁盘加载索引"""
        if not self.index_file.exists() or not self.corpus_file.exists():
            logger.info("BM25 索引文件不存在")
            return False

        try:
            logger.info(f"加载 BM25 索引从 {self.index_file}")

            with open(self.index_file, "rb") as f:
                self.index = pickle.load(f)

            with open(self.corpus_file, "r", encoding="utf-8") as f:
                self.corpus = json.load(f)

            self.doc_ids = [d["id"] for d in self.corpus]

            logger.info(f"BM25 索引加载完成，文档数: {len(self.corpus)}")
            return True

        except Exception as e:
            logger.error(f"加载 BM25 索引失败: {e}")
            return False

    def search(
        self,
        query: str,
        scene_type: Optional[str] = None,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索相关文档

        Args:
            query: 查询文本
            scene_type: 场景类型过滤
            top_k: 返回数量

        Returns:
            相关文档列表，每项包含 id, content, score, metadata
        """
        if self.index is None:
            if not self.load_index():
                logger.warning("BM25 索引未加载，返回空结果")
                return []

        # 分词
        query_tokens = query.lower().split()

        # 获取所有文档的 BM25 分数
        scores = self.index.get_scores(query_tokens)

        # 构建结果列表
        results = []
        for i, score in enumerate(scores):
            if i >= len(self.corpus):
                break

            doc = self.corpus[i]

            # 场景过滤
            if scene_type and doc.get("scene_type") != scene_type:
                continue

            results.append({
                "id": doc["id"],
                "content": doc["content"],
                "scene_type": doc.get("scene_type", ""),
                "metadata": doc.get("metadata", {}),
                "bm25_score": float(score)
            })

        # 按分数排序
        results.sort(key=lambda x: x["bm25_score"], reverse=True)

        return results[:top_k]


class BM25Searcher:
    """BM25 搜索器（动态计算模式）"""

    def __init__(self):
        """初始化 BM25 搜索器"""
        self.index = None
        self.tokenized_corpus = []
        self.corpus = []

    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        为文档建立动态索引

        Args:
            documents: 文档列表
        """
        from rank_bm25 import BM25Okapi

        self.corpus = documents
        self.tokenized_corpus = [
            doc.get("content", "").lower().split()
            for doc in documents
        ]

        if self.tokenized_corpus:
            self.index = BM25Okapi(self.tokenized_corpus)
        else:
            self.index = None

    def search(
        self,
        query: str,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索相关文档（动态计算）

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            相关文档列表
        """
        if self.index is None or not self.tokenized_corpus:
            return []

        query_tokens = query.lower().split()
        scores = self.index.get_scores(query_tokens)

        # 打包结果
        doc_scores = list(zip(self.corpus, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for doc, score in doc_scores[:top_k]:
            results.append({
                "id": doc.get("id", ""),
                "content": doc.get("content", ""),
                "scene_type": doc.get("scene_type", ""),
                "metadata": doc.get("metadata", {}),
                "bm25_score": float(score)
            })

        return results


# 全局索引器实例
_bm25_indexer: Optional[BM25Indexer] = None


def get_bm25_indexer(index_dir: str = "data/bm25_index") -> BM25Indexer:
    """获取 BM25 索引器单例"""
    global _bm25_indexer
    if _bm25_indexer is None:
        _bm25_indexer = BM25Indexer(index_dir=index_dir)
        _bm25_indexer.load_index()
    return _bm25_indexer


def compute_bm25_scores_dynamic(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: int = 20
) -> List[Dict[str, Any]]:
    """
    动态计算 BM25 分数（fallback 模式）

    Args:
        query: 查询文本
        documents: 候选文档列表
        top_k: 返回数量

    Returns:
        带 BM25 分数的文档列表
    """
    searcher = BM25Searcher()
    searcher.index_documents(documents)
    return searcher.search(query, top_k=top_k)


if __name__ == "__main__":
    # 测试
    print("测试 BM25 模块...")

    # 模拟文档
    docs = [
        {"id": "1", "content": "信用卡单笔交易限额是5万元", "scene_type": "risk_rule", "metadata": {}},
        {"id": "2", "content": "白金卡的日累计限额是20万元", "scene_type": "risk_rule", "metadata": {}},
        {"id": "3", "content": "金卡单日限额10万元", "scene_type": "risk_rule", "metadata": {}},
    ]

    # 测试预构建模式
    indexer = BM25Indexer()
    indexer.build_index(docs)
    indexer.save_index()

    results = indexer.search("信用卡限额", top_k=2)
    print(f"预构建搜索结果: {results}")

    # 测试动态计算模式
    dynamic_results = compute_bm25_scores_dynamic("信用卡限额", docs, top_k=2)
    print(f"动态计算结果: {dynamic_results}")
