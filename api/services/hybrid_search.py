"""
混合检索模块
实现向量检索 + BM25 检索的 RRF 融合
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    result_lists: List[List[Dict[str, Any]]],
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    使用 RRF (Reciprocal Rank Fusion) 融合多个检索结果

    RRF 分数 = Σ(1 / (k + rank))

    Args:
        result_lists: 多个检索结果列表，每项是按相关性排序的文档列表
        k: RRF 参数，通常 60
    Returns:
        融合后的文档列表，按 RRF 分数排序
    """
    if not result_lists:
        return []

    # 如果只有一个列表，直接返回
    if len(result_lists) == 1:
        return result_lists[0]

    # 初始化文档得分映射
    doc_scores: Dict[str, float] = {}
    doc_data: Dict[str, Dict[str, Any]] = {}

    # 对每个结果列表计算 RRF 分数
    for result_list in result_lists:
        for rank, doc in enumerate(result_list, start=1):
            # 使用文档 ID 或内容 hash 作为唯一标识
            doc_id = doc.get("id") or doc.get("content", "")[:100]

            # 累加 RRF 分数
            rrf_score = 1.0 / (k + rank)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score

            # 保存文档数据（只保存第一次）
            if doc_id not in doc_data:
                doc_data[doc_id] = doc

    # 按分数排序
    sorted_doc_ids = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

    # 构建结果
    results = []
    for doc_id, score in sorted_doc_ids:
        doc = doc_data[doc_id]
        results.append({
            **doc,
            "rrf_score": score
        })

    return results


def score_normalization(
    scores: List[float],
    method: str = "min_max"
) -> List[float]:
    """
    分数归一化

    Args:
        scores: 原始分数列表
        method: 归一化方法，"min_max" 或 "z_score"

    Returns:
        归一化后的分数列表
    """
    if not scores:
        return []

    if method == "min_max":
        min_s = min(scores)
        max_s = max(scores)
        if max_s == min_s:
            return [1.0] * len(scores)
        return [(s - min_s) / (max_s - min_s) for s in scores]

    elif method == "z_score":
        import statistics
        mean = statistics.mean(scores)
        stdev = statistics.stdev(scores) if len(scores) > 1 else 1.0
        if stdev == 0:
            return [0.0] * len(scores)
        return [(s - mean) / stdev for s in scores]

    return scores


def hybrid_search(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    vector_weight: float = 0.5,
    top_k: int = 20
) -> List[Dict[str, Any]]:
    """
    混合搜索：向量检索 + BM25 检索的加权融合

    Args:
        vector_results: 向量检索结果
        bm25_results: BM25 检索结果
        vector_weight: 向量检索权重 (0-1)，BM25 权重 = 1 - vector_weight
        top_k: 返回数量

    Returns:
        混合检索结果
    """
    if not vector_results and not bm25_results:
        return []

    # 如果只有一种结果，直接返回
    if not vector_results:
        return bm25_results[:top_k]
    if not bm25_results:
        return vector_results[:top_k]

    # 收集所有文档
    all_docs: Dict[str, Dict[str, Any]] = {}

    # 处理向量结果
    vector_scores = [doc.get("score", 0) for doc in vector_results]
    vector_scores_norm = score_normalization(vector_scores)

    for i, doc in enumerate(vector_results):
        doc_id = doc.get("id") or f"vec_{i}"
        all_docs[doc_id] = {
            **doc,
            "id": doc_id,
            "vector_score_norm": vector_scores_norm[i] if i < len(vector_scores_norm) else 0,
            "bm25_score_norm": 0,
            "vector_score": doc.get("score", 0),
            "bm25_score": 0
        }

    # 处理 BM25 结果
    bm25_scores = [doc.get("bm25_score", 0) for doc in bm25_results]
    bm25_scores_norm = score_normalization(bm25_scores)

    for i, doc in enumerate(bm25_results):
        doc_id = doc.get("id") or f"bm25_{i}"
        if doc_id in all_docs:
            all_docs[doc_id]["bm25_score_norm"] = bm25_scores_norm[i] if i < len(bm25_scores_norm) else 0
            all_docs[doc_id]["bm25_score"] = doc.get("bm25_score", 0)
        else:
            all_docs[doc_id] = {
                **doc,
                "id": doc_id,
                "vector_score_norm": 0,
                "bm25_score_norm": bm25_scores_norm[i] if i < len(bm25_scores_norm) else 0,
                "vector_score": 0,
                "bm25_score": doc.get("bm25_score", 0)
            }

    # 计算加权分数
    for doc_id, doc in all_docs.items():
        hybrid_score = (
            vector_weight * doc["vector_score_norm"] +
            (1 - vector_weight) * doc["bm25_score_norm"]
        )
        doc["hybrid_score"] = hybrid_score

    # 按混合分数排序
    sorted_docs = sorted(all_docs.values(), key=lambda x: x["hybrid_score"], reverse=True)

    return sorted_docs[:top_k]


if __name__ == "__main__":
    # 测试
    print("测试混合检索...")

    vector_results = [
        {"id": "1", "content": "信用卡限额", "score": 0.95},
        {"id": "2", "content": "借记卡限额", "score": 0.85},
        {"id": "3", "content": "手机银行", "score": 0.75},
    ]

    bm25_results = [
        {"id": "1", "content": "信用卡限额", "bm25_score": 8.5},
        {"id": "4", "content": "信用卡年费", "bm25_score": 7.2},
        {"id": "2", "content": "借记卡限额", "bm25_score": 6.8},
    ]

    # 测试 RRF 融合
    rrf_results = reciprocal_rank_fusion([vector_results, bm25_results])
    print(f"RRF 融合结果:")
    for r in rrf_results:
        print(f"  id: {r['id']}, rrf_score: {r['rrf_score']:.4f}")

    # 测试加权融合
    hybrid_results = hybrid_search(vector_results, bm25_results, vector_weight=0.6)
    print(f"\n加权融合结果 (vector_weight=0.6):")
    for r in hybrid_results:
        print(f"  id: {r['id']}, hybrid_score: {r['hybrid_score']:.4f}")
