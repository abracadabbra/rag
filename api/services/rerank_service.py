"""
BGE Reranker 精排模块
对候选文档进行更精确的相关性重排序
"""

import logging
from typing import List, Dict, Any, Optional
import torch

from api.config import settings

logger = logging.getLogger(__name__)


class BGEReranker:
    """BGE Reranker 精排模型"""

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        device: str = None,
        top_k: int = 3
    ):
        """
        初始化 BGE Reranker

        Args:
            model_name: 模型名称
            device: 设备（cpu/cuda），None 则自动检测
            top_k: 返回的重排序结果数量
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = device
        self.top_k = top_k

        logger.info(f"🔧 加载 BGE Reranker 模型: {model_name}")
        logger.info(f"   设备: {device}")

        try:
            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(
                model_name,
                device=device,
                max_length=512
            )
            logger.info("✅ BGE Reranker 模型加载完成")
        except ImportError:
            logger.error("sentence-transformers 未安装，请运行: pip install sentence-transformers")
            raise ImportError("需要安装 sentence-transformers: pip install sentence-transformers")

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        对候选文档进行重排序

        Args:
            query: 查询文本
            documents: 候选文档列表，每项包含 content, metadata 等
            top_k: 返回数量，None 则使用默认 self.top_k

        Returns:
            重排序后的文档列表，按相关性分数从高到低
        """
        if not documents:
            return []

        top_k = top_k or self.top_k

        # 提取文档内容
        doc_contents = [doc.get("content", "") for doc in documents]

        # 构建 query-document pair
        pairs = [[query, content] for content in doc_contents]

        # 计算相关性分数
        try:
            scores = self.model.predict(pairs, show_progress_bar=False)
        except Exception as e:
            logger.error(f"Reranker 预测失败: {e}")
            # 失败时返回原始顺序
            return documents[:top_k]

        # 转换为 numpy 数组
        if hasattr(scores, 'tolist'):
            scores = scores.tolist()
        elif not isinstance(scores, list):
            scores = list(scores)

        # 打包结果
        doc_scores = list(zip(documents, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)

        # 构建返回结果
        results = []
        for doc, score in doc_scores[:top_k]:
            result = {
                **doc,
                "rerank_score": float(score)
            }
            results.append(result)

        logger.debug(f"Rerank 完成，输入: {len(documents)}, 输出: {len(results)}")

        return results


# 全局单例
_reranker: Optional[BGEReranker] = None


def get_reranker(
    model_name: str = None,
    device: str = None,
    top_k: int = None
) -> BGEReranker:
    """
    获取 BGE Reranker 单例

    Args:
        model_name: 模型名称，None 则使用配置
        device: 设备，None 则自动检测
        top_k: 返回数量，None 则使用配置

    Returns:
        BGEReranker 实例
    """
    global _reranker

    if _reranker is None:
        model_name = model_name or settings.rerank_model
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        top_k = top_k or settings.rerank_top_k

        _reranker = BGEReranker(
            model_name=model_name,
            device=device,
            top_k=top_k
        )

    return _reranker


def reset_reranker() -> None:
    """重置 reranker 单例（用于测试或重新加载模型）"""
    global _reranker
    _reranker = None


if __name__ == "__main__":
    # 测试
    print("测试 BGE Reranker...")

    # 模拟文档
    docs = [
        {"content": "信用卡单笔交易限额是5万元", "metadata": {"rule_id": "R001"}},
        {"content": "白金卡的日累计限额是20万元", "metadata": {"rule_id": "R002"}},
        {"content": "金卡单日限额10万元", "metadata": {"rule_id": "R003"}},
    ]

    try:
        reranker = get_reranker(top_k=2)
        results = reranker.rerank("信用卡限额是多少？", docs)

        print(f"重排序结果:")
        for r in results:
            print(f"  score: {r['rerank_score']:.4f}, content: {r['content'][:30]}...")
    except Exception as e:
        print(f"测试失败（可能是模型未下载）: {e}")
        print("首次使用会自动下载模型")
