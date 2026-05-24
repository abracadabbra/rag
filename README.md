# RAG 统一技术架构系统

基于 LangChain + LangGraph 的多场景 RAG 系统，支持风控规则问答、模型卡片检索、仿真结果解读、毛利抽成查询四个业务场景。

## 项目状态

**当前阶段：** 阶段 1 - MVP 单场景基础问答

**进度：**
- [x] 技术方案设计
- [x] 基础设施配置（Docker Compose）
- [x] 数据摄入 Pipeline 开发
- [x] FastAPI 服务搭建
- [x] 基础 RAG 功能实现
- [x] 完整日志系统
- [x] 健康检查和错误处理
- [x] API Settings 后端验证和前端 UI
- [x] Milvus schema 修复（维度 384，VARCHAR 元数据）
- [x] Docker 生产部署配置（多阶段构建）
- [x] 前端会话管理侧边栏
- [x] Settings 和 Reranker 测试覆盖
- [x] Milvus 客户端 server/lite 自动切换
- [ ] 第一批数据导入

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd rag
```

### 2. 一键启动基础设施

```bash
./setup.sh
```

这个脚本会自动：
- 检查前置条件（Docker、Python）
- 创建 `.env` 配置文件
- 启动 Milvus + Redis
- 安装 Python 依赖
- 初始化 Milvus Collection

### 3. 配置环境变量

编辑 `.env` 文件，填入必要的配置：

```bash
# 必填项
OPENAI_API_KEY=your_openai_api_key_here

# 可选项（使用默认值即可）
MILVUS_HOST=localhost
REDIS_HOST=localhost
```

### 4. 准备数据

参考 [数据准备指南](./数据准备指南.md)，整理风控规则文档并放入 `data/risk_rules/` 目录。

### 5. 导入数据

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行数据摄入脚本（待开发）
python ingestion/ingest.py --source data/risk_rules --scene risk_rule
```

### 6. 启动 API 服务

```bash
# 启动 FastAPI 服务
python -m api.main
```

访问 http://localhost:8000/docs 查看 API 文档。

### 7. 测试 API

```bash
# 运行测试脚本
python test_api.py

# 或使用 curl 测试
curl -X POST http://localhost:8000/api/v1/risk-rules/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "白金卡的单笔交易限额是多少？",
    "top_k": 5,
    "score_threshold": 0.7
  }'
```

## 项目结构

```
rag-system/
├── api/                          # FastAPI 服务
│   ├── main.py                   # 入口文件
│   ├── routers/                  # 路由
│   │   ├── risk_rules.py         # 风控规则查询
│   │   ├── model_cards.py        # 模型卡片检索
│   │   ├── simulation.py         # 仿真解读
│   │   ├── profit.py             # 毛利查询
│   │   └── settings.py           # API 设置管理
│   ├── services/                 # 业务逻辑
│   │   ├── rag_service.py
│   │   └── settings_service.py   # 设置服务（.env 读写）
│   └── config.py                 # 配置管理
│
├── frontend/                     # Vue 3 前端
│   ├── src/
│   │   ├── views/
│   │   │   └── ApiSettings.vue   # API 设置页面
│   │   ├── components/           # 组件
│   │   └── services/
│   │       └── api.js            # API 客户端
│   ├── Dockerfile                # 前端 Docker 构建
│   ├── nginx.conf                # Nginx 配置
│   └── vite.config.js            # Vite 配置
│
├── ingestion/                    # 数据摄入
│   ├── ingest.py                 # CLI 工具
│   ├── loaders.py                # Document Loaders
│   ├── splitters.py              # Text Splitters
│   └── embeddings.py             # Embedding 生成
│
├── infrastructure/               # 基础设施
│   ├── docker-compose.yml        # Docker Compose 配置
│   ├── milvus_schema.py          # Milvus Collection 定义
│   └── README.md                 # 部署指南
│
├── Dockerfile                    # 后端 Docker 构建
├── data/                         # 数据目录
│   ├── risk_rules/               # 风控规则文档
│   ├── model_cards/              # 模型卡片数据
│   └── test_cases/               # 测试用例
│
├── tests/                        # 测试
│   ├── test_ingestion.py
│   ├── test_api.py
│   └── test_settings.py          # Settings 测试
│
├── .trellis/                     # Trellis 任务管理
│   └── tasks/
│       └── 05-07-phase0-infrastructure/  # 阶段0任务
│
├── .env.example                  # 环境变量模板
├── .env                          # 环境变量（不提交到 Git）
├── setup.sh                      # 快速启动脚本
├── requirements.txt              # Python 依赖
├── 技术方案.md                   # 完整技术方案
├── 数据准备指南.md               # 数据准备说明
└── README.md                     # 本文件
```

## 核心技术栈

- **编程语言**: Python 3.10+
- **Web 框架**: FastAPI
- **AI 框架**: LangChain + LangGraph
- **向量数据库**: Milvus 2.3+
- **缓存**: Redis 7+
- **Embedding 模型**: BGE-M3
- **LLM**: GPT-4 Turbo / GPT-3.5 Turbo

## 架构设计

### 整体架构

```
Java 上游系统
  ↓
FastAPI (直接路由)
  ↓
┌─────────┬─────────┬─────────┬─────────┐
│风控规则 │模型卡片 │仿真解读 │毛利查询 │
│Agent    │Agent    │Agent    │Agent    │
│(LangGraph)│(LangGraph)│(LangGraph)│(LangGraph)│
└─────────┴─────────┴─────────┴─────────┘
  ↓
Redis (会话状态) + Milvus (向量检索) + LLM
```

### 核心能力

每个场景 Agent 具备：
- ✅ **多轮对话**：记忆上下文，支持追问
- ✅ **自动钻取**：发现异常自动深入分析
- ✅ **并行执行**：同时调用多个数据源
- ✅ **人工介入**：高风险操作需用户确认

详见 [技术方案.md](./技术方案.md)

## 分阶段实施计划

| 阶段 | 目标 | 时间 | 状态 |
|------|------|------|------|
| 阶段 0 | 数据准备 + 基础设施 | 1-2周 | ✅ 已完成 |
| 阶段 1 | MVP 单场景（风控规则） | 2-3周 | 🚧 进行中 |
| 阶段 2 | 多轮对话 + 会话管理 | 2周 | ⏳ 待开始 |
| 阶段 3 | 自动钻取 + 并行执行 + 多场景 | 2-3周 | ⏳ 待开始 |
| 阶段 4 | 人工介入 + 全场景上线 | 2周 | ⏳ 待开始 |
| 阶段 5 | 持续优化 | 持续 | ⏳ 待开始 |

**总计：** 约 3 个月完整上线

### 阶段 1 完成情况

✅ **已完成：**
- 基础 RAG 检索（BGE-M3 + Milvus）
- FastAPI 服务框架
- 风控规则查询 API (`POST /api/v1/risk-rules/query`)
- 完整日志系统（Request ID、性能指标、Token 统计）
- 健康检查（综合检查 + 独立检查）
- 错误处理分类（400/503/504/500）
- 数据摄入 Pipeline（支持 Markdown、PDF、DOCX）
- API Settings（后端 .env 配置管理 + 前端设置界面）
- Milvus schema 修复（维度 1024→384，JSON→VARCHAR）
- Docker 生产部署（后端/前端多阶段构建，nginx 反向代理）
- 前端会话管理侧边栏
- Settings 和 Reranker 测试覆盖
- Milvus 客户端 server/lite 自动切换

📋 **待完成：**
- 第一批数据导入和测试

## 文档索引

- [技术方案.md](./技术方案.md) - 完整的技术架构设计
- [数据准备指南.md](./数据准备指南.md) - 数据格式规范和准备流程
- [docs/API_FIX.md](./docs/API_FIX.md) - API 修复说明（日志、错误处理、健康检查）
- [infrastructure/README.md](./infrastructure/README.md) - 基础设施部署指南
- [.trellis/tasks/05-07-phase0-infrastructure/prd.md](.trellis/tasks/05-07-phase0-infrastructure/prd.md) - 阶段0详细需求

## 常用命令

### 基础设施管理

```bash
# 启动所有服务
cd infrastructure && docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f milvus
docker-compose logs -f redis

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart
```

### Milvus 管理

```bash
# 查看 Collection 信息
python infrastructure/milvus_schema.py --action info

# 重新创建 Collection
python infrastructure/milvus_schema.py --action create --drop-old

# 删除 Collection
python infrastructure/milvus_schema.py --action drop
```

### 开发

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/

# 代码格式化
black .
isort .

# 类型检查
mypy .
```

## 监控与调试

### 服务访问地址

| 服务 | 地址 | 用途 |
|------|------|------|
| Milvus | `localhost:19530` | 向量数据库 |
| Redis | `localhost:6379` | 会话存储 |
| MinIO Console | http://localhost:9001 | 对象存储管理 |
| Redis Commander | http://localhost:8081 | Redis 可视化 |
| API Docs | http://localhost:8000/docs | API 文档 |

### 健康检查

```bash
# 综合健康检查（检查所有依赖服务）
curl http://localhost:8000/health

# 独立健康检查
curl http://localhost:8000/health/milvus
curl http://localhost:8000/health/redis
curl http://localhost:8000/health/openai
```

### API 测试

```bash
# 运行完整测试套件
python test_api.py

# 测试风控规则查询
curl -X POST http://localhost:8000/api/v1/risk-rules/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "白金卡的单笔交易限额是多少？",
    "top_k": 5,
    "score_threshold": 0.7
  }'
```

### 日志查看

```bash
# 查看实时日志
tail -f logs/rag_system.log

# 查看错误日志
grep ERROR logs/rag_system.log

# 查看性能指标
grep "耗时" logs/rag_system.log
```

## 贡献指南

### 开发流程

1. 从 `main` 分支创建功能分支
2. 开发并编写测试
3. 提交 Pull Request
4. Code Review 通过后合并

### 代码规范

- 遵循 PEP 8
- 使用 Black 格式化代码
- 使用 isort 排序 import
- 使用 mypy 进行类型检查
- 测试覆盖率 > 80%

## 常见问题

### Q: Milvus 启动失败怎么办？

**A:** 检查日志 `docker-compose logs milvus`，常见原因：
- 端口被占用（19530）
- 内存不足（至少需要 4GB）
- etcd 或 minio 未启动

### Q: 如何切换到本地 LLM？

**A:** 编辑 `.env` 文件：
```bash
LOCAL_LLM_ENABLED=true
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=qwen2.5:72b
```

### Q: 数据导入失败怎么办？

**A:** 检查：
- 文档格式是否符合规范
- Milvus 是否正常运行
- Embedding 模型是否正确加载

更多问题请查看 [技术方案.md](./技术方案.md) 的"故障排查"章节。

## 许可证

[待定]

## 联系方式

- **项目负责人**: [待填写]
- **技术支持**: [待填写]

---

**文档版本**: v1.1  
**最后更新**: 2026-05-08  
**当前阶段**: 阶段 1 - MVP 单场景基础问答
