# 数据摄入使用指南

## 概述

数据摄入 Pipeline 负责将文档加载、分块、生成 Embedding 并存入 Milvus 向量数据库。

## 支持的文件格式

- **Markdown** (`.md`) - 推荐，支持 frontmatter 元数据
- **PDF** (`.pdf`) - 自动提取文本
- **Word** (`.docx`) - 自动提取段落
- **纯文本** (`.txt`) - 直接读取

## 快速开始

### 1. 准备数据

将文档放入对应目录：

```bash
data/
├── risk_rules/           # 风控规则文档
│   ├── R001_信用卡交易限额.md
│   └── R002_信用卡取现限额.md
├── model_cards/          # 模型卡片（待添加）
└── test_cases/           # 测试用例
```

### 2. 试运行（推荐）

先使用 `--dry-run` 模式验证数据：

```bash
# 激活虚拟环境
source venv/bin/activate

# 试运行
python ingestion/ingest.py \
  --source data/risk_rules \
  --scene risk_rule \
  --dry-run
```

输出示例：
```
==========================================
  RAG 系统数据摄入工具
==========================================

🔗 连接 Milvus: localhost:19530
✅ 连接成功，Collection: unified_docs

📂 找到 2 个文件

📖 加载文档...
✅ 加载成功: data/risk_rules/R001_信用卡交易限额.md
✅ 加载成功: data/risk_rules/R002_信用卡取现限额.md
✅ 成功加载 2 个文档

✂️  文本分块...
✅ 生成 8 个文本块

🔍 试运行模式，不插入数据

📋 样本数据（前3个块）:

--- 块 1 ---
内容长度: 456 字符
元数据: {'rule_id': 'R001', 'scene_type': 'risk_rule', ...}
内容预览: # 信用卡单笔交易限额规则...
```

### 3. 正式导入

确认无误后，去掉 `--dry-run` 参数：

```bash
python ingestion/ingest.py \
  --source data/risk_rules \
  --scene risk_rule
```

输出示例：
```
🧮 生成 Embedding...
✅ 生成 8 个 Embedding

💾 插入 Milvus...
✅ 成功插入 8 条数据

✅ 摄入完成，耗时: 12.34秒
   成功: 8
   失败: 0
   跳过: 0
```

## 命令行参数

### 必填参数

- `--source, -s`: 源目录路径
- `--scene, -t`: 场景类型
  - `risk_rule` - 风控规则
  - `model_card` - 模型卡片
  - `simulation` - 仿真结果
  - `profit` - 毛利数据

### 可选参数

- `--pattern, -p`: 文件匹配模式（默认: `*`）
- `--collection, -c`: Collection 名称（默认: 从配置读取）
- `--dry-run`: 试运行模式，不实际插入数据

## 使用示例

### 示例 1：导入所有风控规则

```bash
python ingestion/ingest.py -s data/risk_rules -t risk_rule
```

### 示例 2：只导入特定文件

```bash
python ingestion/ingest.py \
  -s data/risk_rules \
  -t risk_rule \
  --pattern "R001*"
```

### 示例 3：导入到自定义 Collection

```bash
python ingestion/ingest.py \
  -s data/risk_rules \
  -t risk_rule \
  --collection my_custom_collection
```

### 示例 4：批量导入多个场景

```bash
# 风控规则
python ingestion/ingest.py -s data/risk_rules -t risk_rule

# 模型卡片
python ingestion/ingest.py -s data/model_cards -t model_card

# 仿真结果
python ingestion/ingest.py -s data/simulation -t simulation
```

## 工作流程

数据摄入 Pipeline 的完整流程：

```
1. 文档加载 (loaders.py)
   ├── 读取文件
   ├── 提取 frontmatter 元数据
   └── 返回 {content, metadata}

2. 文本分块 (splitters.py)
   ├── 使用 RecursiveCharacterTextSplitter
   ├── chunk_size=500, overlap=50
   └── 返回文本块列表

3. Embedding 生成 (embeddings.py)
   ├── BGE-M3 本地模型（推荐）
   ├── 或 OpenAI Embedding API
   └── 返回向量列表

4. 插入 Milvus (ingest.py)
   ├── 生成唯一 ID
   ├── 批量插入数据
   └── 刷新 Collection
```

## 数据结构

### Milvus Collection Schema

```python
{
    "id": "abc123...",                    # MD5 哈希
    "vector": [0.1, 0.2, ...],           # 1024 维向量
    "scene_type": "risk_rule",           # 场景类型
    "content": "文本内容...",             # 原始文本
    "metadata": {                         # 元数据
        "rule_id": "R001",
        "rule_name": "信用卡交易限额规则",
        "category": "交易限额",
        "version": "v2.3",
        "source": "data/risk_rules/R001.md",
        "chunk_index": 0,
        "total_chunks": 3
    },
    "created_at": 1715097600000          # 时间戳（毫秒）
}
```

## 性能优化

### 1. 批量处理

数据摄入工具自动批量处理：
- Embedding 生成：batch_size=32
- Milvus 插入：批量插入所有数据

### 2. 增量更新

目前不支持增量更新，重复导入会生成新的 ID。

**计划支持：**
- 检测文档变化（基于文件哈希）
- 只更新变化的文档
- 删除已移除的文档

### 3. 并行处理

对于大量文档，可以手动并行处理：

```bash
# 终端 1
python ingestion/ingest.py -s data/risk_rules -t risk_rule

# 终端 2
python ingestion/ingest.py -s data/model_cards -t model_card
```

## 故障排查

### 问题 1：连接 Milvus 失败

**错误信息：**
```
❌ 摄入失败: Connection refused
```

**解决方案：**
1. 检查 Milvus 是否启动：`docker ps | grep milvus`
2. 检查端口：`lsof -i :19530`
3. 重启 Milvus：`cd infrastructure && docker-compose restart milvus`

### 问题 2：Embedding 生成失败

**错误信息：**
```
❌ 加载 BGE-M3 模型失败
```

**解决方案：**
1. 检查模型是否下载：`ls ~/.cache/huggingface/hub/`
2. 手动下载模型：
   ```bash
   from FlagEmbedding import BGEM3FlagModel
   model = BGEM3FlagModel("BAAI/bge-m3")
   ```
3. 或使用 OpenAI Embedding：
   ```bash
   # 编辑 .env
   USE_OPENAI_EMBEDDING=true
   OPENAI_API_KEY=your_key_here
   ```

### 问题 3：文件加载失败

**错误信息：**
```
❌ 加载失败: data/risk_rules/R001.pdf, 错误: ...
```

**解决方案：**
1. 检查文件格式是否支持
2. 检查文件是否损坏
3. 对于 PDF，确保不是扫描件（需要 OCR）
4. 查看详细错误信息

### 问题 4：内存不足

**错误信息：**
```
MemoryError: Unable to allocate array
```

**解决方案：**
1. 减少 batch_size：
   ```bash
   # 编辑 .env
   EMBEDDING_BATCH_SIZE=16
   ```
2. 分批导入文档
3. 增加系统内存

## 验证数据

导入完成后，验证数据：

```bash
# 查看 Collection 信息
python infrastructure/milvus_schema.py --action info
```

输出示例：
```
📊 Collection 信息: unified_docs
   - 文档数量: 8
   - Schema: ...
   - 索引: ...
```

## 下一步

数据导入完成后：
1. 启动 API 服务：`make dev`
2. 测试查询：`curl http://localhost:8000/api/v1/risk-rules/query`
3. 查看 API 文档：http://localhost:8000/docs

---

**文档版本**: v1.0  
**最后更新**: 2026-05-07
