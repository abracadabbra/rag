"""
文本分块模块
"""

from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from api.config import settings


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

        print(f"✅ 文本分块器初始化完成")
        print(f"   块大小: {self.chunk_size}")
        print(f"   重叠: {self.chunk_overlap}")

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
    # 测试
    print("测试文本分块...")

    text = """
# 信用卡交易限额规则

## 白金卡
- 单笔限额：50,000 元
- 日累计限额：200,000 元

## 金卡
- 单笔限额：20,000 元
- 日累计限额：80,000 元

## 普卡
- 单笔限额：5,000 元
- 日累计限额：20,000 元
    """ * 10  # 重复10次，制造长文本

    chunks = split_text(text)
    print(f"✅ 文本分块完成")
    print(f"   原始长度: {len(text)} 字符")
    print(f"   块数量: {len(chunks)}")
    print(f"   第一块长度: {len(chunks[0])} 字符")
