# Directory Structure

> How backend code is organized in this project.

---

## Overview

这是一个基于 **FastAPI + LangChain** 的 RAG 系统，采用分层架构：
- **api/** - FastAPI 应用层（路由、配置、日志）
- **ingestion/** - 数据摄入层（文档加载、分块、向量化）
- **infrastructure/** - 基础设施层（Milvus、Redis、Docker）
- **tests/** - 测试代码

---

## Directory Layout

```
rag/
├── api/                          # FastAPI 应用
│   ├── main.py                   # 应用入口
│   ├── config.py                 # 配置管理（Pydantic Settings）
│   ├── logging_config.py         # 日志配置
│   ├── routers/                  # API 路由
│   │   ├── health.py             # 健康检查
│   │   ├── risk_rules.py         # 风控规则查询
│   │   └── cache.py              # 缓存管理
│   ├── services/                 # 业务逻辑层
│   │   ├── rag_service.py        # RAG 检索服务
│   │   ├── cache_service.py      # 缓存服务
│   │   ├── session_manager.py    # 会话管理
│   │   ├── conversation_agent.py # 对话 Agent
│   │   └── clarification.py      # 澄清机制
│   └── models/                   # Pydantic 数据模型
│       ├── request.py            # 请求模型
│       └── response.py           # 响应模型
│
├── ingestion/                    # 数据摄入
│   ├── ingest.py                 # CLI 工具
│   ├── loaders.py                # 文档加载器（Markdown/PDF/DOCX）
│   ├── splitters.py              # 文本分块器
│   └── embeddings.py             # Embedding 生成
│
├── infrastructure/               # 基础设施
│   ├── docker-compose.yml        # Docker Compose 配置
│   ├── milvus_schema.py          # Milvus Collection 定义
│   └── README.md                 # 部署指南
│
├── tests/                        # 测试
│   ├── test_api.py               # API 测试
│   └── test_session.py           # 会话测试
│
├── data/                         # 数据目录（不提交到 Git）
│   └── risk_rules/               # 风控规则文档
│
├── logs/                         # 日志目录（不提交到 Git）
│
├── .env                          # 环境变量（不提交到 Git）
├── .env.example                  # 环境变量模板
├── requirements.txt              # Python 依赖
├── pyproject.toml                # 项目配置（Black/isort/mypy/pytest）
└── README.md                     # 项目文档
```

---

## Module Organization

### 1. API 层（api/）

**职责**：处理 HTTP 请求、路由、参数验证、响应格式化

- **main.py** - FastAPI 应用入口，注册路由和中间件
- **config.py** - 使用 `pydantic_settings.BaseSettings` 管理配置，支持 `.env` 文件
- **routers/** - 按业务场景拆分路由（每个场景一个文件）
- **services/** - 业务逻辑层，不直接处理 HTTP
- **models/** - Pydantic 模型，用于请求/响应验证

### 2. 数据摄入层（ingestion/）

**职责**：文档加载、文本分块、向量化、写入 Milvus

- **loaders.py** - 文档加载器，支持多种格式（Markdown/PDF/DOCX/TXT）
- **splitters.py** - 文本分块器，基于 LangChain
- **embeddings.py** - Embedding 生成，支持本地模型（BGE-M3）和 OpenAI
- **ingest.py** - CLI 工具，提供命令行接口

### 3. 基础设施层（infrastructure/）

**职责**：数据库、缓存、消息队列等基础设施的配置和管理

- **docker-compose.yml** - 定义 Milvus、Redis、MinIO 等服务
- **milvus_schema.py** - Milvus Collection 的创建、删除、查询

---

## Naming Conventions

### 文件命名
- **Python 文件**：`snake_case.py`（例如：`rag_service.py`）
- **配置文件**：小写 + 下划线（例如：`docker-compose.yml`）
- **文档文件**：大写 + 下划线（例如：`README.md`、`API_FIX.md`）

### 目录命名
- **Python 包**：`snake_case`（例如：`api/`, `ingestion/`）
- **数据目录**：`snake_case`（例如：`data/`, `logs/`）

### 模块命名
- **路由模块**：按业务场景命名（例如：`risk_rules.py`、`model_cards.py`）
- **服务模块**：`<功能>_service.py`（例如：`rag_service.py`、`cache_service.py`）
- **工具模块**：功能名称（例如：`loaders.py`、`splitters.py`）

---

## Examples

### 良好的模块组织示例

**api/routers/risk_rules.py** - 路由层只处理 HTTP 相关逻辑
```python
# 参考：api/routers/risk_rules.py:1-123
# - 使用 APIRouter 定义路由
# - 参数验证使用 Pydantic 模型
# - 业务逻辑委托给 services 层
# - 统一的错误处理（400/500/503/504）
```

**api/services/rag_service.py** - 服务层封装业务逻辑
```python
# 参考：api/services/rag_service.py:1-301
# - 单例模式（get_rag_service()）
# - 完整的日志记录
# - 异常分类处理（ConnectionError/TimeoutError）
```

**ingestion/loaders.py** - 工具模块提供可复用功能
```python
# 参考：ingestion/loaders.py:1-276
# - 基类 + 多个实现类
# - 工厂函数（get_loader）
# - 便捷函数（load_document/load_documents）
```
