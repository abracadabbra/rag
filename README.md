# RAG 统一技术架构系统

基于 LangChain + LangGraph 的多场景 RAG 系统，支持风控规则问答、模型卡片检索、仿真结果解读、毛利抽成查询四个业务场景。

## 项目状态

**当前阶段：** 多场景 RAG + 风控/毛利业务工具接入验证

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
- [x] 风控/毛利订单级业务工具、合同探测、审计和前端证据展示
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

参考 [数据准备指南](./数据准备指南.md)，整理风控规则文档并放入 `data/risk_rules/` 目录；毛利、抽成、司机收入和订单钱流口径文档放入 `data/profit/` 目录。

### 5. 导入数据

```bash
# 安装依赖并使用默认虚拟环境
make install

# 导入风控规则语料
./.venv/bin/python -m ingestion.ingest --source data/risk_rules --scene risk_rule

# 导入毛利链路语料
./.venv/bin/python -m ingestion.ingest --source data/profit --scene profit
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
│   ├── profit/                   # 毛利链路文档
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
| 阶段 1 | MVP 单场景（风控规则） | 2-3周 | ✅ 已完成 |
| 阶段 2 | 多轮对话 + 会话管理 | 2周 | ✅ 已完成基础能力 |
| 阶段 3 | 自动钻取 + 并行执行 + 多场景 | 2-3周 | 🚧 进行中（已支持多场景与业务工具接入验证） |
| 阶段 4 | 人工介入 + 全场景上线 | 2周 | ⏳ 待开始 |
| 阶段 5 | 持续优化 | 持续 | ⏳ 待开始 |

**总计：** 约 3 个月完整上线

### 已完成能力摘要

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
- 风控/毛利订单级业务工具，支持 mock/HTTP 模式、合同探测、响应样例校验、访问控制和脱敏审计
- 问答页展示业务工具调用证据、风控命中规则、毛利钱流链路、毛利拆解和安全降级提示

📋 **待完成：**
- 第一批数据导入和测试

## 文档索引

- [技术方案.md](./技术方案.md) - 完整的技术架构设计
- [数据准备指南.md](./数据准备指南.md) - 数据格式规范和准备流程
- [docs/BUSINESS_TOOL_QUICKSTART.md](./docs/BUSINESS_TOOL_QUICKSTART.md) - 业务工具接真实系统的最短接入清单
- [docs/BUSINESS_TOOLS.md](./docs/BUSINESS_TOOLS.md) - 风控/毛利业务工具合同、配置、探测、审计和前端展示说明
- [docs/BUSINESS_TOOL_ACCEPTANCE.md](./docs/BUSINESS_TOOL_ACCEPTANCE.md) - 业务工具验收状态、上线清单和交接说明
- [docs/API_FIX.md](./docs/API_FIX.md) - API 修复说明（日志、错误处理、健康检查）
- [infrastructure/README.md](./infrastructure/README.md) - 基础设施部署指南
- [.trellis/tasks/05-07-phase0-infrastructure/prd.md](.trellis/tasks/05-07-phase0-infrastructure/prd.md) - 阶段0详细需求

## 业务工具接入

项目已内置风控和毛利订单级业务工具。用户在风控或毛利场景里提出订单级问题时，系统会先用规则识别是否需要查询业务系统；开启 LLM 意图兜底后，模糊问题会走结构化意图判断，但低置信度或缺订单号时只提示澄清，不直接调用接口。

如果你现在要接真实风控/毛利系统，先看 [docs/BUSINESS_TOOL_QUICKSTART.md](./docs/BUSINESS_TOOL_QUICKSTART.md)；如果要看完整合同、Schema、审计和前端展示约束，再看 [docs/BUSINESS_TOOLS.md](./docs/BUSINESS_TOOLS.md)。

核心配置在 `.env`：

```env
ENABLE_BUSINESS_TOOLS=true
ENABLE_BUSINESS_TOOL_LLM_INTENT=false
ENABLE_BUSINESS_TOOL_ACCESS_CONTROL=false
ENABLE_BUSINESS_TOOL_AUDIT_FILE=false

RISK_API_BASE_URL=
RISK_API_KEY=
PROFIT_API_BASE_URL=
PROFIT_API_KEY=
```

- `MINIMAX_API_BASE` 默认使用 `https://topapi.link/v1`。
- `ENABLE_BUSINESS_TOOLS=false` 会关闭风控/毛利业务工具执行。
- `RISK_API_BASE_URL` 或 `PROFIT_API_BASE_URL` 留空时使用 mock 数据；填入真实 base URL 后切换为 HTTP 模式。
- 业务工具运行态里 `data_source=http` 只表示当前走 HTTP client；进一步通过 `integration_mode`
  区分 `fake_http`（进程内 fake transport 验证链路）和 `external_http`（真实外部系统）。
- 真实风控接口至少返回 `order_id`、`decision`、`risk_score`、`hit_rules`、`recommended_action`。
- 真实毛利接口至少返回 `order_id`、`gross_amount`、`platform_commission`、`driver_income`、`subsidy`、`coupon`、`platform_net_profit`。
- `ENABLE_BUSINESS_TOOL_ACCESS_CONTROL=true` 后，订单级查询、探测和审计读取需要请求头 `X-Business-Tool-Token`。
- `ENABLE_BUSINESS_TOOL_AUDIT_FILE=true` 会把脱敏审计摘要写入 `BUSINESS_TOOL_AUDIT_FILE`。

接入真实系统前先跑一键 smoke/readiness 检查：

```bash
# 先导出机器可读合同给真实系统联调方
make business-contracts
make business-contracts BUSINESS_CONTRACT_OUTPUT_FILE=/tmp/business_tool_contracts.json

# 导出合同 + readiness + 下一步动作的联调验收包
make business-acceptance-pack
make business-acceptance-pack ORDER_ID=ORD88888 \
  BUSINESS_ACCEPTANCE_PACK_OUTPUT_FILE=/tmp/business_tool_acceptance_pack.json
make business-acceptance-pack ORDER_ID=ORD88888 \
  BUSINESS_SMOKE_FAKE_HTTP=1 \
  BUSINESS_ACCEPTANCE_PACK_OUTPUT_FILE=/tmp/business_tool_acceptance_pack_fake_http.json

make business-smoke

# 生产接入/CI 门禁：要求 readiness_check.overall_status 必须为 ready
make business-smoke-strict

# 可覆盖订单号、审计文件和真实系统响应样例
make business-smoke-strict ORDER_ID=ORD88888 \
  BUSINESS_SMOKE_AUDIT_FILE=/tmp/business_tool_audit.jsonl \
  RISK_RESPONSE_FILE=/tmp/risk_response.json \
  PROFIT_RESPONSE_FILE=/tmp/profit_response.json

# 离线校验联调方填写的真实系统响应样例，不调用风控/毛利接口
make business-validate-samples
make business-validate-samples \
  RISK_RESPONSE_FILE=/tmp/risk_response.json \
  PROFIT_RESPONSE_FILE=/tmp/profit_response.json \
  BUSINESS_SAMPLE_VALIDATION_OUTPUT_FILE=/tmp/business_sample_validation.json

# CI 日志只打印精简摘要，同时保存完整安全报告
make business-smoke-strict ORDER_ID=ORD88888 \
  BUSINESS_SMOKE_AUDIT_FILE=/tmp/business_tool_audit.jsonl \
  BUSINESS_SMOKE_OUTPUT_FILE=/tmp/business_smoke_report.json \
  BUSINESS_SMOKE_SUMMARY_ONLY=1

# fake HTTP 集成演练：risk/profit 都走真实 HTTP client，但不依赖外部系统或本地端口
make business-smoke-strict ORDER_ID=ORD88888 \
  BUSINESS_SMOKE_AUDIT_FILE=/tmp/business_tool_audit.jsonl \
  BUSINESS_SMOKE_FAKE_HTTP=1
```

输出里的 `readiness_check.overall_status` 用来判断接入状态：
`ready` 表示可进入真实流量验证，`ready_with_warnings` 表示主链路通过但仍有配置提醒，
`blocked` 表示存在必须先处理的门禁失败。
其中自然语言毛利 smoke 会先生成 `tool_intent`，再复用该 intent 执行业务工具；
报告中的 `query_smoke.execution_path=inspected_intent` 可用来确认没有发生二次路由。
报告还会通过 `intent_precheck` readiness gate 校验风控/毛利标准问题能在不执行真实接口的情况下选中目标 Function calling 工具，证据只保留 scene/tool/source/confidence 等安全字段。
`make business-smoke` 默认向脚本传入 `--fail-on-blocked`，因此只有 `blocked`
会让命令返回非 0；warnings 会保留在报告中但不阻断本地检查。
`make business-smoke-strict` 使用 `--require-ready`，适合作为 CI 或真实系统上线前门禁：
`blocked` 或 `ready_with_warnings` 都会让 Make 以非 0 失败。需要区分精确退出码时，
直接调用 `scripts/business_tool_smoke.py --require-ready`：`blocked` 返回 2，
`ready_with_warnings` 返回 3。
启用 `BUSINESS_SMOKE_FAKE_HTTP=1` 时，脚本会使用进程内 fake HTTP transport
拦截 risk/profit client 请求，把两条工具链路都切到 `http` 模式，适合在接真实业务系统前先验证合同、探测、审计、readiness 与降级链路不会乱。
`make business-acceptance-pack` 生成的
`/tmp/business_tool_acceptance_pack.json` 会把合同、readiness 项、safe smoke 证据和
`integration_handoff.recommended_next_actions` 放到同一个交付物里，方便真实系统联调方按
warning/blocker 逐项处理。验收包也会带上 `sample_handoff`：样例模板路径、
`make business-validate-samples`、自定义样例文件命令和报告脱敏保证；同时带上
`prompt_contract`，用于查看风控/毛利回答口径、输出结构和 Prompt 安全规则。
仓库同时提供可复制填写的响应样例模板：
`examples/business_tool_samples/risk_response.sample.json` 和
`examples/business_tool_samples/profit_response.sample.json`。填入真实系统返回后可用
`make business-validate-samples` 离线校验；输出只包含通过/失败、诊断码、缺失字段、
异常字段、可展示字段和未展示字段名，不回显完整 payload、订单号或金额值。
在这种模式下，`runtime_status.tools[*].integration_mode` 会显示为 `fake_http`，
`real_http_configured` 也会进入 `passed`，表示“HTTP client 调用链路已经验通，但还不是外部生产系统”。
`external_http_configured` 会保持 warning，用来提醒上线前必须切到真实外部系统。
该模式不监听 `127.0.0.1` 端口，因此可以在禁止本地端口绑定的环境里运行；真正上线前仍需用
`integration_mode=external_http` 的真实系统配置补跑严格门禁。
需要保留完整证据但避免 CI 日志过长时，传入 `--output-file` 保存完整 JSON 报告，
并配合 `--summary-only` 让 stdout 只输出 `readiness` 计数、warning/blocker ID
和审计事件数量。

LLM 工具意图兜底需要单独做 live 验收，因为它会真实调用当前配置的 LLM Provider：

```bash
make business-llm-acceptance ORDER_ID=ORD88888 \
  BUSINESS_LLM_ACCEPTANCE_OUTPUT_FILE=/tmp/business_llm_acceptance.json
```

这条验收会临时开启 `ENABLE_BUSINESS_TOOL_LLM_INTENT=true`，检查模糊毛利问题能走
`selection_source=llm` 生成结构化 `tool_intent`，并验证低置信度和不安全订单号不会执行
业务接口。没有有效模型凭证时命令会非 0 失败，这是预期的未验收状态。

真实环境上线前，建议以 `make business-smoke-strict` 为最终门禁，并要求
`readiness_check.overall_status=ready`。这意味着 warning 也要清零；当前最常见
的 warning 包括：

- `access_control_enabled`：订单级真实数据必须启用访问控制 token。
- `real_http_configured`：风控和毛利都必须切到 HTTP client 路径；上线验收需确认是
  `integration_mode=external_http` 的真实外部系统，而不是 mock 或 fake-http 演练。
- `external_http_configured`：上线前必须使用外部真实风控/毛利系统补跑严格门禁；
  fake-http 演练通过时该项仍会保持 warning。
- `persistent_audit_enabled`：必须开启 JSONL 或等价持久审计，并能回读。
- `audit_traceability`：至少完成一次自然语言订单查询，确认 `audit_id`、
  `selection_reason`、`confidence` 可追因。
- `llm_intent_fallback`：如果生产环境要依赖模糊问题自动识别，就必须配置可用
  的 LLM 凭证并完成验收。这个 gate 只有在真实 fallback 调用至少成功过一次、
  产生过结构化意图后才应视为 `passed`；如果明确不启用这项能力，应在上线说明
  里固定为 `ENABLE_BUSINESS_TOOL_LLM_INTENT=false`。

需要定点排查时再使用 API：

```bash
# 查看机器可读合同，不调用业务系统
curl http://localhost:8000/api/v1/business-tools/contracts

# 查看当前 mock/http、访问控制、审计和合同可用性
curl http://localhost:8000/api/v1/business-tools/runtime-status

# 查看只读接入门禁，不调用业务系统
curl http://localhost:8000/api/v1/business-tools/readiness?limit=20

# 预检自然语言是否会选择业务工具，不调用真实订单接口
curl -X POST http://localhost:8000/api/v1/business-tools/intent \
  -H "Content-Type: application/json" \
  -d '{"scene_type":"profit","query":"查询订单 ORD88888 的抽成和司机收入"}'

# 探测毛利接口，会调用当前 mock 或 HTTP client
curl -X POST http://localhost:8000/api/v1/business-tools/probe \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"get_profit_chain_detail","order_id":"ORD88888"}'

# 离线校验真实系统响应样例，不调用业务 API
curl -X POST http://localhost:8000/api/v1/business-tools/validate-response \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"get_profit_chain_detail","payload":{"order_id":"ORD88888","gross_amount":128.6,"platform_commission":19.29,"driver_income":92.35,"subsidy":8.0,"coupon":6.0,"platform_net_profit":2.33}}'

# 批量校验多条真实系统响应样例，只返回聚合诊断和逐条 index
curl -X POST http://localhost:8000/api/v1/business-tools/validate-responses \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"get_profit_chain_detail","payloads":[{"order_id":"ORD88888","gross_amount":128.6,"platform_commission":19.29,"driver_income":92.35,"subsidy":8.0,"coupon":6.0,"platform_net_profit":2.33}]}'

# 查看最近脱敏工具调用摘要
curl http://localhost:8000/api/v1/business-tools/audit-events?limit=20
```

前端 `API 设置` 页面可以查看业务接口合同、运行态、只读接入门禁、安全检查、接口探测、响应样例校验和最近审计事件。风控和毛利问答页支持选择回答口径（自动、财务/运营/排查或策略），显式选择会回显在答案卡上；页面也会在答案下方展示 `tool_calls`：调用了哪个工具、数据源、接口路径、审计 ID、耗时、选择依据、置信度，以及风控命中证据或毛利钱流链路。失败调用会显示 `接口降级提示`，只展示安全的 `error_type`，不展示原始异常、堆栈、密钥或完整订单 payload。

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
# 创建默认虚拟环境（.venv）并安装依赖
make install

# 如果需要沿用旧的 venv 目录
VENV_DIR=venv make install

# 运行测试
make test

# 代码格式化
make format

# 类型检查
make lint
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
**当前阶段**: 多场景 RAG + 风控/毛利业务工具接入验证
