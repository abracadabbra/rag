# Database Guidelines

> Database access patterns, ORM usage, and query conventions.

---

## Overview

本项目使用 **Milvus** 作为向量数据库，**Redis** 作为缓存和会话存储。不使用传统的关系型数据库和 ORM。

---

## Milvus（向量数据库）

### Connection Management

使用 `pymilvus` 连接 Milvus，连接在服务初始化时建立：

```python
# 参考：api/services/rag_service.py:24-40
from pymilvus import connections, Collection

connections.connect(
    alias="default",
    host=settings.milvus_host,
    port=settings.milvus_port
)
collection = Collection(settings.milvus_collection)
collection.load()
```

**规范**：
- 使用 `alias="default"` 作为默认连接
- 连接参数从 `settings` 读取，不硬编码
- Collection 加载后才能查询（`collection.load()`）

### Schema Definition

Collection Schema 定义在 `infrastructure/milvus_schema.py`：

```python
# 参考：infrastructure/milvus_schema.py
# - 使用 FieldSchema 定义字段
# - 向量字段：dim=1024（BGE-M3）
# - 标量字段：scene_type, content, metadata
# - 索引类型：IVF_FLAT（metric_type="IP"）
```

**规范**：
- 向量维度必须与 Embedding 模型匹配（BGE-M3 = 1024）
- 使用 `scene_type` 字段区分不同业务场景
- `metadata` 字段存储 JSON 格式的元数据

### Query Patterns

向量检索使用 `collection.search()`：

```python
# 参考：api/services/rag_service.py:111-119
results = collection.search(
    data=[query_vector],
    anns_field="vector",
    param=search_params,
    limit=top_k,
    expr=f'scene_type == "{scene_type}"',  # 过滤条件
    output_fields=["content", "metadata", "scene_type"]
)
```

**规范**：
- 使用 `expr` 参数过滤场景类型
- `output_fields` 明确指定需要返回的字段
- 检索后过滤低分结果（`score >= score_threshold`）

---

## Redis（缓存和会话存储）

### Connection Management

使用 `redis-py` 连接 Redis：

```python
# 参考：api/services/cache_service.py
import redis

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password,
    db=settings.redis_db,
    decode_responses=True
)
```

**规范**：
- 使用 `decode_responses=True` 自动解码为字符串
- 连接参数从 `settings` 读取
- 使用单例模式（`get_cache_service()`）

### Key Naming Conventions

Redis Key 命名规范：

```
<namespace>:<entity>:<id>
```

**示例**：
- 查询缓存：`cache:query:<hash>`
- 会话数据：`session:<session_id>`
- 会话历史：`session:<session_id>:history`

**规范**：
- 使用冒号 `:` 分隔命名空间
- 缓存 Key 使用查询参数的 hash 值
- 设置合理的 TTL（缓存 1 小时，会话 30 分钟）

---

## Query Patterns

### Milvus 向量检索

完整的检索流程：

```python
# 参考：api/services/rag_service.py:65-177
# 1. 生成查询向量
query_vector = embed_query(query)

# 2. 执行向量检索
results = collection.search(
    data=[query_vector],
    anns_field="vector",
    param=search_params,
    limit=top_k,
    expr=f'scene_type == "{scene_type}"',
    output_fields=["content", "metadata", "scene_type"]
)

# 3. 过滤低分结果
retrieved_docs = [
    hit for hit in results[0] 
    if hit.score >= score_threshold
]
```

### Redis 缓存模式

查询结果缓存：

```python
# 参考：api/services/cache_service.py
# 1. 生成缓存 Key（基于查询参数的 hash）
# 2. 尝试从 Redis 读取
# 3. 如果命中，直接返回
# 4. 如果未命中，执行查询后写入缓存
```

---

## Migrations

本项目不使用传统的数据库迁移工具。Schema 变更流程：

### Milvus Schema 变更

```bash
# 1. 修改 infrastructure/milvus_schema.py
# 2. 删除旧 Collection 并创建新的
python infrastructure/milvus_schema.py --action create --drop-old

# 3. 重新导入数据
python ingestion/ingest.py --source data/risk_rules --scene risk_rule
```

### Redis Key 变更

- 更新 Key 命名规范
- 旧 Key 自动过期（TTL）
- 无需手动迁移

---

## Naming Conventions

### Milvus Collection

- Collection 名称：`unified_docs`（统一文档集合）
- 字段命名：`snake_case`（例如：`scene_type`, `chunk_index`）

### Redis Keys

- 命名格式：`<namespace>:<entity>:<id>`
- 使用冒号 `:` 分隔
- 全部小写

---

## Common Mistakes

### ❌ 忘记加载 Collection

```python
# 错误：直接查询未加载的 Collection
collection = Collection("unified_docs")
results = collection.search(...)  # 报错！
```

```python
# 正确：先加载再查询
collection = Collection("unified_docs")
collection.load()  # 必须先加载
results = collection.search(...)
```

### ❌ Redis Key 没有设置 TTL

```python
# 错误：永久缓存会导致内存泄漏
redis_client.set(key, value)
```

```python
# 正确：设置 TTL
redis_client.setex(key, ttl, value)
```

### ❌ 硬编码连接参数

```python
# 错误：硬编码
connections.connect(host="localhost", port=19530)
```

```python
# 正确：从配置读取
connections.connect(
    host=settings.milvus_host,
    port=settings.milvus_port
)
```
