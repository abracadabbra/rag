"""
Milvus 连接管理
支持 Milvus Server 和 Milvus Lite（本地文件模式）自动切换
"""

import logging
from typing import Optional
from pymilvus import MilvusClient, CollectionSchema, FieldSchema, DataType
from pymilvus.milvus_client.index import IndexParams

logger = logging.getLogger(__name__)

# Milvus Lite 本地数据库路径
MILVUS_LITE_DB = "milvus_demo.db"

# 全局客户端实例
_client: Optional[MilvusClient] = None


def get_milvus_client(
    host: str = "localhost",
    port: int = 19530,
    collection_name: str = "unified_docs",
    dimension: int = 384,
    timeout: Optional[float] = None,
) -> MilvusClient:
    """
    获取 MilvusClient 实例（单例）

    优先连接 Milvus Server，失败时回退到 Milvus Lite。
    """
    global _client
    if _client is not None:
        return _client

    # 尝试连接 Milvus Server
    try:
        client = MilvusClient(uri=f"http://{host}:{port}", timeout=timeout)
        client.list_collections()
        logger.info(f"Milvus Server 连接成功: {host}:{port}")
        _ensure_collection(client, collection_name, dimension)
        _client = client
        return _client
    except Exception as e:
        logger.warning(f"Milvus Server 连接失败 ({e})，回退到 Milvus Lite")

    # 回退到 Milvus Lite
    client = MilvusClient(uri=MILVUS_LITE_DB, timeout=timeout)
    logger.info(f"Milvus Lite 模式: {MILVUS_LITE_DB}")
    _ensure_collection(client, collection_name, dimension)
    _client = client
    return _client


def _build_schema(dimension: int) -> CollectionSchema:
    """构建 collection schema"""
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dimension),
        FieldSchema(name="scene_type", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="created_at", dtype=DataType.INT64),
    ]
    return CollectionSchema(fields=fields, enable_dynamic_field=False)


def _ensure_collection(client: MilvusClient, name: str, dimension: int):
    """确保 collection 存在且 schema 正确"""
    if client.has_collection(name):
        # 检查 schema 是否匹配（通过检查 id 字段类型）
        desc = client.describe_collection(name)
        id_field = next((f for f in desc.get("fields", []) if f["name"] == "id"), None)
        if id_field and id_field.get("type") == DataType.INT64:
            logger.warning(f"Collection {name} schema 不匹配（id 为 INT64），重建")
            client.drop_collection(name)
        else:
            return  # schema 正确

    schema = _build_schema(dimension)
    client.create_collection(
        collection_name=name,
        schema=schema
    )
    # 创建向量索引
    index_params = IndexParams()
    index_params.add_index(field_name="vector", index_type="AUTOINDEX", metric_type="IP")
    client.create_index(
        collection_name=name,
        index_params=index_params
    )
    client.load_collection(name)
    logger.info(f"创建 Collection: {name} (dim={dimension})")


def reset_client():
    """重置客户端（用于测试）"""
    global _client
    _client = None
