#!/usr/bin/env python3
"""
数据摄入 CLI 工具
用途：将文档导入 Milvus 向量数据库
"""

import click
import time
from pathlib import Path
from typing import List
from pymilvus import connections, Collection
import hashlib
from datetime import datetime

from ingestion.loaders import load_documents
from ingestion.splitters import split_documents
from ingestion.embeddings import embed_documents
from api.config import settings

# BM25 索引构建
try:
    from api.services.bm25_service import get_bm25_indexer
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    print("⚠️  BM25 模块不可用，跳过索引构建")


class DataIngestion:
    """数据摄入管理器"""

    def __init__(self, collection_name: str = None):
        """
        初始化数据摄入管理器

        Args:
            collection_name: Collection 名称
        """
        self.collection_name = collection_name or settings.milvus_collection

        # 连接 Milvus
        print(f"🔗 连接 Milvus: {settings.milvus_host}:{settings.milvus_port}")
        connections.connect(
            alias="default",
            host=settings.milvus_host,
            port=settings.milvus_port
        )

        self.collection = Collection(self.collection_name)
        print(f"✅ 连接成功，Collection: {self.collection_name}")

    def ingest_directory(
        self,
        source_dir: str,
        scene_type: str,
        file_pattern: str = "*",
        dry_run: bool = False
    ) -> dict:
        """
        摄入目录下的所有文档

        Args:
            source_dir: 源目录
            scene_type: 场景类型（risk_rule, model_card, simulation, profit）
            file_pattern: 文件匹配模式
            dry_run: 是否为试运行（不实际插入数据）

        Returns:
            摄入统计信息
        """
        start_time = time.time()

        # 查找文件
        source_path = Path(source_dir)
        if not source_path.exists():
            raise ValueError(f"目录不存在: {source_dir}")

        # 支持的文件扩展名
        extensions = [".md", ".pdf", ".docx", ".txt"]
        file_paths = []

        for ext in extensions:
            file_paths.extend(source_path.glob(f"**/{file_pattern}{ext}"))

        if not file_paths:
            print(f"⚠️  未找到任何文档")
            return {"success": 0, "failed": 0, "skipped": 0}

        print(f"\n📂 找到 {len(file_paths)} 个文件")

        # 加载文档
        print(f"\n📖 加载文档...")
        documents = load_documents([str(p) for p in file_paths])
        print(f"✅ 成功加载 {len(documents)} 个文档")

        # 添加场景类型
        for doc in documents:
            doc["metadata"]["scene_type"] = scene_type

        # 文本分块
        print(f"\n✂️  文本分块...")
        chunks = split_documents(documents)
        print(f"✅ 生成 {len(chunks)} 个文本块")

        if dry_run:
            print(f"\n🔍 试运行模式，不插入数据")
            self._print_sample(chunks)
            return {"success": len(chunks), "failed": 0, "skipped": 0}

        # 生成 Embedding
        print(f"\n🧮 生成 Embedding...")
        texts = [chunk["content"] for chunk in chunks]
        embeddings = embed_documents(texts)
        print(f"✅ 生成 {len(embeddings)} 个 Embedding")

        # 插入 Milvus
        print(f"\n💾 插入 Milvus...")
        stats = self._insert_to_milvus(chunks, embeddings, scene_type)

        # 构建 BM25 索引
        if BM25_AVAILABLE and getattr(settings, 'enable_bm25', False):
            self._build_bm25_index(chunks, scene_type)

        elapsed = time.time() - start_time
        print(f"\n✅ 摄入完成，耗时: {elapsed:.2f}秒")
        print(f"   成功: {stats['success']}")
        print(f"   失败: {stats['failed']}")
        print(f"   跳过: {stats['skipped']}")

        return stats

    def _insert_to_milvus(
        self,
        chunks: List[dict],
        embeddings: List[List[float]],
        scene_type: str
    ) -> dict:
        """插入数据到 Milvus"""
        success = 0
        failed = 0
        skipped = 0

        # 准备数据
        ids = []
        vectors = []
        scene_types = []
        contents = []
        metadatas = []
        created_ats = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            try:
                # 生成唯一 ID
                doc_id = self._generate_id(chunk, scene_type, i)

                # 检查是否已存在（可选）
                # existing = self.collection.query(expr=f"id == '{doc_id}'", limit=1)
                # if existing:
                #     skipped += 1
                #     continue

                ids.append(doc_id)
                vectors.append(embedding)
                scene_types.append(scene_type)
                contents.append(chunk["content"][:65535])  # 限制长度
                metadatas.append(chunk["metadata"])
                created_ats.append(int(datetime.now().timestamp() * 1000))

                success += 1

            except Exception as e:
                print(f"❌ 处理失败: {e}")
                failed += 1

        # 批量插入
        if ids:
            try:
                self.collection.insert([
                    ids,
                    vectors,
                    scene_types,
                    contents,
                    metadatas,
                    created_ats
                ])

                # 刷新
                self.collection.flush()
                print(f"✅ 成功插入 {len(ids)} 条数据")

            except Exception as e:
                print(f"❌ 插入失败: {e}")
                failed += len(ids)
                success = 0

        return {"success": success, "failed": failed, "skipped": skipped}

    def _generate_id(self, chunk: dict, scene_type: str, index: int) -> str:
        """生成唯一 ID"""
        metadata = chunk["metadata"]
        source = metadata.get("source", "unknown")
        chunk_index = metadata.get("chunk_index", index)

        # 使用文件路径 + 块索引生成 ID
        id_str = f"{scene_type}_{source}_{chunk_index}"
        return hashlib.md5(id_str.encode()).hexdigest()

    def _print_sample(self, chunks: List[dict]):
        """打印样本数据"""
        print(f"\n📋 样本数据（前3个块）:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n--- 块 {i+1} ---")
            print(f"内容长度: {len(chunk['content'])} 字符")
            print(f"元数据: {chunk['metadata']}")
            print(f"内容预览: {chunk['content'][:200]}...")

    def _build_bm25_index(self, chunks: List[dict], scene_type: str):
        """构建 BM25 索引"""
        print(f"\n📚 构建 BM25 索引...")

        try:
            indexer = get_bm25_indexer()

            # 准备文档数据
            documents = []
            for i, chunk in enumerate(chunks):
                doc_id = self._generate_id(chunk, scene_type, i)
                documents.append({
                    "id": doc_id,
                    "content": chunk["content"],
                    "scene_type": scene_type,
                    "metadata": chunk["metadata"]
                })

            # 构建索引
            indexer.build_index(documents)
            indexer.save_index()

            print(f"✅ BM25 索引构建完成，文档数: {len(documents)}")

        except Exception as e:
            print(f"⚠️  BM25 索引构建失败: {e}")


@click.command()
@click.option(
    "--source",
    "-s",
    required=True,
    help="源目录路径"
)
@click.option(
    "--scene",
    "-t",
    required=True,
    type=click.Choice(["risk_rule", "model_card", "simulation", "profit"]),
    help="场景类型"
)
@click.option(
    "--pattern",
    "-p",
    default="*",
    help="文件匹配模式（默认: *）"
)
@click.option(
    "--collection",
    "-c",
    default=None,
    help="Collection 名称（默认: 从配置读取）"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="试运行模式，不实际插入数据"
)
def main(source: str, scene: str, pattern: str, collection: str, dry_run: bool):
    """
    数据摄入 CLI 工具

    示例:
        python ingest.py --source data/risk_rules --scene risk_rule
        python ingest.py -s data/risk_rules -t risk_rule --dry-run
    """
    print("=" * 60)
    print("  RAG 系统数据摄入工具")
    print("=" * 60)

    try:
        ingestion = DataIngestion(collection_name=collection)
        stats = ingestion.ingest_directory(
            source_dir=source,
            scene_type=scene,
            file_pattern=pattern,
            dry_run=dry_run
        )

        if stats["failed"] > 0:
            exit(1)

    except Exception as e:
        print(f"\n❌ 摄入失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
