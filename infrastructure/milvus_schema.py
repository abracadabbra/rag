"""
Milvus Collection Schema 定义
用于创建统一的向量数据库 Collection
"""

from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility
)


def create_unified_collection(
    collection_name: str = "unified_docs",
    dim: int = 384,  # all-MiniLM-L6-v2 向量维度
    drop_old: bool = False
):
    """
    创建统一的文档 Collection

    Args:
        collection_name: Collection 名称
        dim: 向量维度（all-MiniLM-L6-v2 为 384）
        drop_old: 是否删除已存在的 Collection
    """

    # 连接 Milvus
    connections.connect(
        alias="default",
        host="localhost",
        port="19530"
    )

    # 如果 Collection 已存在
    if utility.has_collection(collection_name):
        if drop_old:
            print(f"删除已存在的 Collection: {collection_name}")
            utility.drop_collection(collection_name)
        else:
            print(f"Collection {collection_name} 已存在，跳过创建")
            return Collection(collection_name)

    # 定义字段
    fields = [
        # 主键
        FieldSchema(
            name="id",
            dtype=DataType.VARCHAR,
            is_primary=True,
            max_length=256,
            description="文档唯一标识，格式: {scene_type}_{doc_id}_{chunk_id}"
        ),

        # 向量字段
        FieldSchema(
            name="vector",
            dtype=DataType.FLOAT_VECTOR,
            dim=dim,
            description="BGE-M3 生成的稠密向量"
        ),

        # 场景类型（用于过滤）
        FieldSchema(
            name="scene_type",
            dtype=DataType.VARCHAR,
            max_length=50,
            description="场景类型: risk_rule, model_card, simulation, profit"
        ),

        # 原始内容
        FieldSchema(
            name="content",
            dtype=DataType.VARCHAR,
            max_length=65535,
            description="文本块的原始内容"
        ),

        # 元数据（JSON 字符串）
        FieldSchema(
            name="metadata",
            dtype=DataType.VARCHAR,
            max_length=65535,
            description="文档元数据 JSON 字符串，包含 rule_id, category, version, update_date 等"
        ),

        # 创建时间
        FieldSchema(
            name="created_at",
            dtype=DataType.INT64,
            description="创建时间戳（毫秒）"
        )
    ]

    # 创建 Schema
    schema = CollectionSchema(
        fields=fields,
        description="统一的 RAG 文档库，支持多场景检索",
        enable_dynamic_field=True  # 允许动态字段
    )

    # 创建 Collection
    print(f"创建 Collection: {collection_name}")
    collection = Collection(
        name=collection_name,
        schema=schema,
        using="default"
    )

    # 创建索引
    print("创建向量索引...")
    index_params = {
        "metric_type": "IP",  # 内积（Inner Product）
        "index_type": "IVF_FLAT",  # 初期使用 IVF_FLAT，生产环境可改为 HNSW
        "params": {"nlist": 1024}
    }

    collection.create_index(
        field_name="vector",
        index_params=index_params
    )

    # 创建标量索引（加速过滤）
    print("创建标量索引...")
    collection.create_index(
        field_name="scene_type",
        index_name="scene_type_idx"
    )

    print(f"✅ Collection {collection_name} 创建成功！")
    print(f"   - 向量维度: {dim}")
    print(f"   - 索引类型: IVF_FLAT")
    print(f"   - 支持场景: risk_rule, model_card, simulation, profit")

    return collection


def get_collection_info(collection_name: str = "unified_docs"):
    """
    获取 Collection 信息
    """
    connections.connect(
        alias="default",
        host="localhost",
        port="19530"
    )

    if not utility.has_collection(collection_name):
        print(f"❌ Collection {collection_name} 不存在")
        return

    collection = Collection(collection_name)

    print(f"\n📊 Collection 信息: {collection_name}")
    print(f"   - 文档数量: {collection.num_entities}")
    print(f"   - Schema: {collection.schema}")
    print(f"   - 索引: {collection.indexes}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Milvus Collection 管理")
    parser.add_argument(
        "--action",
        choices=["create", "info", "drop"],
        default="create",
        help="操作类型"
    )
    parser.add_argument(
        "--collection",
        default="unified_docs",
        help="Collection 名称"
    )
    parser.add_argument(
        "--drop-old",
        action="store_true",
        help="删除已存在的 Collection"
    )

    args = parser.parse_args()

    if args.action == "create":
        create_unified_collection(
            collection_name=args.collection,
            drop_old=args.drop_old
        )
    elif args.action == "info":
        get_collection_info(args.collection)
    elif args.action == "drop":
        connections.connect(host="localhost", port="19530")
        if utility.has_collection(args.collection):
            utility.drop_collection(args.collection)
            print(f"✅ Collection {args.collection} 已删除")
        else:
            print(f"❌ Collection {args.collection} 不存在")
