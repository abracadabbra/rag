"""
数据摄入模块初始化
"""

from ingestion.loaders import load_document, load_documents
from ingestion.splitters import split_text, split_documents
from ingestion.embeddings import embed_documents, embed_query

__all__ = [
    "load_document",
    "load_documents",
    "split_text",
    "split_documents",
    "embed_documents",
    "embed_query"
]
