"""
文本分块模块
"""

from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from api.config import settings
import logging

logger = logging.getLogger(__name__)


class TextSplitter:
    """文本分块器"""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        separators: List[str] = None
    ):
        """
        初始化文本分块器

        Args:
            chunk_size: 块大小
            chunk_overlap: 块重叠大小
            separators: 分隔符列表
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        # 中文友好的分隔符
        self.separators = separators or [
            "\n\n",  # 段落
            "\n",    # 行
            "。",    # 句号
            "！",    # 感叹号
            "？",    # 问号
            "；",    # 分号
            "，",    # 逗号
            " ",     # 空格
            ""       # 字符
        ]

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len
        )

        logger.info(f"文本分块器初始化完成 - 块大小: {self.chunk_size}, 重叠: {self.chunk_overlap}")

    def split_text(self, text: str) -> List[str]:
        """
        分割文本

        Args:
            text: 原始文本

        Returns:
            文本块列表
        """
        return self.splitter.split_text(text)

    def split_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        分割文档列表

        Args:
            documents: 文档列表，每个文档包含 content 和 metadata

        Returns:
            分块后的文档列表
        """
        chunks = []

        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})

            # 分割文本
            text_chunks = self.split_text(content)

            # 为每个块创建文档
            for i, chunk in enumerate(text_chunks):
                chunk_doc = {
                    "content": chunk,
                    "metadata": {
                        **metadata,
                        "chunk_index": i,
                        "total_chunks": len(text_chunks)
                    }
                }
                chunks.append(chunk_doc)

        return chunks


def split_text(text: str) -> List[str]:
    """便捷函数：分割文本"""
    splitter = TextSplitter()
    return splitter.split_text(text)


def split_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """便捷函数：分割文档列表"""
    splitter = TextSplitter()
    return splitter.split_documents(documents)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # 命令行测试
        file_path = sys.argv[1]
        from ingestion.loaders import load_document
        doc = load_document(file_path)
        chunks = split_documents([doc])
        logger.info(f"分块完成 - 原始长度: {len(doc['content'])} 字符, 块数量: {len(chunks)}")
