# 阶段0：数据准备 + 基础设施搭建

## 目标

搭建 RAG 系统的基础环境，准备第一批风控规则数据，为阶段1（MVP）做好准备。

## 背景

根据《统一 RAG 技术架构方案》，我们采用分阶段实施策略。阶段0是整个项目的基础，需要完成：
1. 核心基础设施部署（Milvus、Redis、FastAPI）
2. 数据摄入 Pipeline 开发
3. 第一批风控规则数据准备和导入
4. 前端会话管理组件开发（并行）

## 需求

### 技术需求

#### 1. 基础设施部署

**Milvus 向量数据库：**
- [ ] 部署 Milvus 2.3+（Docker Compose 或 K8s）
- [ ] 创建 Collection：`unified_docs`
- [ ] Schema 设计：
  - `id`: 文档唯一标识
  - `vector`: 稠密向量（BGE-M3，1024维）
  - `scene_type`: 场景类型（risk_rule/model_card/simulation/profit）
  - `content`: 原始文本内容
  - `metadata`: JSON 字段（存储文档元数据）
- [ ] 配置索引：IVF_FLAT（初期）或 HNSW（生产）

**Redis：**
- [ ] 部署 Redis 7+
- [ ] 配置持久化（AOF + RDB）
- [ ] 用途：会话状态存储（LangGraph Checkpointer）

**FastAPI 服务：**
- [ ] 初始化 FastAPI 项目结构
- [ ] 配置 CORS、日志、异常处理
- [ ] 实现健康检查 endpoint：`GET /health`

#### 2. 数据摄入 Pipeline

**Document Loader：**
- [ ] 支持 Markdown 文件加载
- [ ] 支持 PDF 文件加载（使用 PyPDF2 或 pdfplumber）
- [ ] 支持 Word 文件加载（使用 python-docx）
- [ ] 自动提取 frontmatter 元数据（YAML 格式）

**Text Splitter：**
- [ ] 使用 RecursiveCharacterTextSplitter
- [ ] 配置：chunk_size=500, chunk_overlap=50
- [ ] 中文分隔符：`["\n\n", "\n", "。", "！", "？", "；", " ", ""]`

**Embedding 生成：**
- [ ] 集成 BGE-M3 模型（本地部署或 API）
- [ ] 批量生成 Embedding（batch_size=32）
- [ ] 实现 Embedding 缓存（避免重复计算）

**数据导入脚本：**
- [ ] CLI 工具：`python ingest.py --source data/risk_rules --scene risk_rule`
- [ ] 支持增量更新（检测文档变化）
- [ ] 导入进度显示和错误处理
- [ ] 生成导入报告（成功/失败/跳过数量）

#### 3. 基础 API 实现

**风控规则查询 endpoint：**
- [ ] `POST /api/v1/risk-rules/query`
- [ ] 请求体：`{"query": "string", "session_id": "string|null"}`
- [ ] 响应体：`{"answer": "string", "sources": [...], "session_id": "string"}`
- [ ] 暂时实现简单的单轮问答（不用 LangGraph）

### 数据需求

#### 风控规则文档（业务侧负责）

**数量：** 20-50 条

**格式要求：**
- 优先使用 Markdown 格式
- 包含 frontmatter 元数据（rule_id, rule_name, category, version, update_date）
- 清晰的标题层级
- 如果是 PDF/Word，确保有清晰结构，避免扫描件

**目录结构：**
```
data/
├── risk_rules/
│   ├── R001_信用卡交易限额.md
│   ├── R002_取现限额.md
│   └── ...
└── test_cases/
    └── risk_rules_qa.json  # 10个标注问答对
```

**test_cases/risk_rules_qa.json 格式：**
```json
[
  {
    "question": "白金卡的单笔交易限额是多少？",
    "expected_answer": "50,000 元",
    "source_rule": "R001"
  }
]
```

### 前端需求（并行开发）

**会话管理组件：**
- [ ] 保存和传递 session_id
- [ ] 单次问答界面（输入框 + 答案展示）
- [ ] 展示来源文档（文档名称、章节）
- [ ] 基础样式和交互

## 验收标准

### 技术验收

- [ ] Milvus 和 Redis 正常运行，健康检查通过
- [ ] 数据摄入脚本能成功导入 20+ 条文档
- [ ] 向量库中数据可查询，返回正确的相似文档
- [ ] FastAPI 服务启动正常，`/health` 返回 200
- [ ] `/api/v1/risk-rules/query` 能返回基本答案（即使质量不高）

### 数据验收

- [ ] 至少 20 条风控规则文档已整理完成
- [ ] 文档格式符合规范（有元数据、清晰结构）
- [ ] 10 个测试问答对已标注

### 前端验收

- [ ] 前端界面能发起查询请求
- [ ] 能正确展示答案和来源
- [ ] session_id 正确传递

## 技术方案

### 项目结构

```
rag-system/
├── api/                    # FastAPI 服务
│   ├── main.py            # 入口
│   ├── routers/           # 路由
│   │   └── risk_rules.py
│   ├── services/          # 业务逻辑
│   │   └── rag_service.py
│   └── config.py          # 配置
├── ingestion/             # 数据摄入
│   ├── ingest.py          # CLI 工具
│   ├── loaders.py         # Document Loaders
│   ├── splitters.py       # Text Splitters
│   └── embeddings.py      # Embedding 生成
├── infrastructure/        # 基础设施配置
│   ├── docker-compose.yml # Milvus + Redis
│   └── milvus_schema.py   # Collection 定义
├── data/                  # 数据目录
│   ├── risk_rules/
│   └── test_cases/
├── tests/                 # 测试
├── requirements.txt
└── README.md
```

### 技术栈

- **Python**: 3.10+
- **FastAPI**: 0.104+
- **LangChain**: 0.1+
- **Milvus**: 2.3+
- **Redis**: 7+
- **BGE-M3**: FlagEmbedding 库

### 部署方式

**开发环境：** Docker Compose

```yaml
version: '3.8'
services:
  milvus:
    image: milvusdb/milvus:v2.3.0
    ports:
      - "19530:19530"
    volumes:
      - milvus_data:/var/lib/milvus
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

## 实施计划

### Week 1: 基础设施 + 数据摄入

**Day 1-2: 环境搭建**
- [ ] 部署 Milvus + Redis（Docker Compose）
- [ ] 初始化 FastAPI 项目
- [ ] 配置开发环境（虚拟环境、依赖安装）

**Day 3-4: 数据摄入 Pipeline**
- [ ] 实现 Document Loaders（Markdown、PDF、Word）
- [ ] 实现 Text Splitter
- [ ] 集成 BGE-M3 Embedding

**Day 5: 数据导入**
- [ ] 开发 CLI 工具
- [ ] 测试数据导入流程
- [ ] 导入第一批数据（如果已准备好）

### Week 2: API 开发 + 前端集成

**Day 1-2: 基础 API**
- [ ] 实现 `/api/v1/risk-rules/query`
- [ ] 集成 Milvus 检索
- [ ] 集成 LLM（OpenAI API 或本地模型）

**Day 3-4: 测试与优化**
- [ ] 使用标注问答对测试
- [ ] 调优检索参数（top_k、相似度阈值）
- [ ] 优化 Prompt

**Day 5: 前后端联调**
- [ ] 前后端接口对接
- [ ] 端到端测试
- [ ] 修复 bug

## 风险与依赖

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 数据准备延期 | 阻塞导入测试 | 技术侧先用 mock 数据测试 Pipeline |
| BGE-M3 部署困难 | 无法生成 Embedding | 备选方案：使用 OpenAI Embedding API |
| Milvus 性能问题 | 检索慢 | 先用小数据集验证，后续优化索引 |
| 前端开发延期 | 无法联调 | 先用 Postman 测试后端 API |

## 依赖项

**技术依赖：**
- 服务器资源（至少 8C16G，用于 Milvus + BGE-M3）
- OpenAI API Key（或本地 LLM 部署）

**数据依赖：**
- 业务侧提供 20-50 条风控规则文档
- 业务侧标注 10 个测试问答对

**人员依赖：**
- 后端开发：1-2 人
- 前端开发：1 人（并行）
- 数据准备：业务侧 1 人

## 交付物

- [ ] 可运行的基础设施环境（Milvus + Redis + FastAPI）
- [ ] 数据摄入脚本和使用文档
- [ ] 风控规则向量库（已导入数据）
- [ ] 基础 API 文档（Swagger）
- [ ] 前端会话管理组件
- [ ] 测试报告（包含 10 个问答对的测试结果）

## 后续计划

阶段0完成后，进入阶段1（MVP - 单场景基础问答），重点是：
- 优化检索质量（混合检索、Rerank）
- 优化答案生成（Prompt 工程）
- 提升准确率到 80%+
- 完善监控和日志

---

**创建时间：** 2026-05-07  
**预计完成：** 2026-05-21（2周）  
**负责人：** [待分配]
