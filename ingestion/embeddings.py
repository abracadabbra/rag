"""
Embedding 生成模块
支持 BGE-M3 本地部署和 OpenAI Embedding API
"""

from typing import List, Optional
import numpy as np
from functools import lru_cache

from api.config import settings


class EmbeddingGenerator:
    """Embedding 生成器基类"""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量生成文档 Embedding"""
        raise NotImplementedError

    def embed_query(self, text: str) -> List[float]:
        """生成查询 Embedding"""
        raise NotImplementedError


class BGEEmbedding(EmbeddingGenerator):
    """BGE-M3 Embedding 生成器"""

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str = "cpu",
        batch_size: int = 32
    ):
        """
        初始化 BGE-M3 模型

        Args:
            model_name: 模型名称
            device: 设备（cpu 或 cuda）
            batch_size: 批处理大小
        """
        from FlagEmbedding import BGEM3FlagModel

        print(f"🔧 加载 BGE-M3 模型: {model_name}")
        print(f"   设备: {device}")

        self.model = BGEM3FlagModel(
            model_name,
            use_fp16=(device == "cuda")
        )
        self.device = device
        self.batch_size = batch_size

        print(f"✅ BGE-M3 模型加载完成")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文档 Embedding

        Args:
            texts: 文本列表

        Returns:
            Embedding 向量列表
        """
        # BGE-M3 返回稠密向量
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            max_length=8192  # BGE-M3 支持长文本
        )

        # 返回稠密向量（dense_vecs）
        return embeddings['dense_vecs'].tolist()

    def embed_query(self, text: str) -> List[float]:
        """
        生成查询 Embedding

        Args:
            text: 查询文本

        Returns:
            Embedding 向量
        """
        embeddings = self.model.encode(
            [text],
            batch_size=1,
            max_length=8192
        )

        return embeddings['dense_vecs'][0].tolist()


class OpenAIEmbedding(EmbeddingGenerator):
    """OpenAI Embedding 生成器"""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None
    ):
        """
        初始化 OpenAI Embedding

        Args:
            model: 模型名称
            api_key: API Key
        """
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key or settings.openai_api_key)
        self.model = model

        print(f"✅ OpenAI Embedding 初始化完成: {model}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文档 Embedding

        Args:
            texts: 文本列表

        Returns:
            Embedding 向量列表
        """
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )

        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> List[float]:
        """
        生成查询 Embedding

        Args:
            text: 查询文本

        Returns:
            Embedding 向量
        """
        response = self.client.embeddings.create(
            input=[text],
            model=self.model
        )

        return response.data[0].embedding


@lru_cache()
def get_embedding_generator() -> EmbeddingGenerator:
    """
    获取 Embedding 生成器单例

    Returns:
        Embedding 生成器实例
    """
    if settings.use_openai_embedding:
        return OpenAIEmbedding(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key
        )
    else:
        return BGEEmbedding(
            model_name=settings.embedding_model,
            device=settings.embedding_device,
            batch_size=settings.embedding_batch_size
        )


# 导出便捷函数
def embed_documents(texts: List[str]) -> List[List[float]]:
    """批量生成文档 Embedding"""
    generator = get_embedding_generator()
    return generator.embed_documents(texts)


def embed_query(text: str) -> List[float]:
    """生成查询 Embedding"""
    generator = get_embedding_generator()
    return generator.embed_query(text)


if __name__ == "__main__":
    # 测试
    print("测试 Embedding 生成...")

    texts = [
        "信用卡单笔交易限额是多少？",
        "白金卡的日累计限额是多少？"
    ]

    embeddings = embed_documents(texts)
    print(f"✅ 生成 {len(embeddings)} 个 Embedding")
    print(f"   维度: {len(embeddings[0])}")

    query_embedding = embed_query("金卡限额")
    print(f"✅ 查询 Embedding 维度: {len(query_embedding)}")
