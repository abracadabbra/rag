# API 修复说明

## 修复内容

### 1. API 路由前缀修复 ✅

**问题：** 路由未加 `/api/v1` 前缀，与技术方案不一致

**修复：** `api/main.py`
```python
app.include_router(risk_rules.router, prefix="/api/v1/risk-rules", tags=["风控规则"])
```

**影响：** 
- 旧路径：`POST /query`
- 新路径：`POST /api/v1/risk-rules/query`

### 2. 日志系统完善 ✅

**新增文件：** `api/logging_config.py`
- 统一日志格式
- 支持文件和控制台输出
- 配置第三方库日志级别

**修改文件：**

1. `api/main.py` - 初始化日志系统
2. `api/routers/risk_rules.py` - 添加请求日志
   - 记录 request_id（UUID）
   - 记录查询内容、参数
   - 记录总耗时
   - 记录检索结果数量

3. `api/services/rag_service.py` - 添加性能日志
   - Embedding 生成耗时
   - 向量检索耗时
   - LLM 生成耗时
   - Token 消耗统计

### 3. 错误处理分类 ✅

**修改文件：** `api/routers/risk_rules.py`

**错误类型分类：**
- `400 Bad Request` - 参数错误（ValueError）
- `503 Service Unavailable` - 连接失败（ConnectionError）
- `504 Gateway Timeout` - 请求超时（TimeoutError）
- `500 Internal Server Error` - 其他错误

**修改文件：** `api/services/rag_service.py`

**异常处理增强：**
- 初始化时捕获 Milvus 和 LLM 连接错误
- 检索时捕获 Milvus 查询错误
- LLM 调用时区分超时和认证错误
- 所有异常都记录详细日志（exc_info=True）

### 4. 健康检查增强 ✅

**修改文件：** `api/routers/health.py`

**新增功能：**

1. **综合健康检查** (`GET /health`)
   - 检查所有依赖服务（Milvus、Redis、OpenAI）
   - 返回整体状态：`healthy` 或 `degraded`
   - 包含各服务详细状态

2. **独立健康检查**
   - `GET /health/milvus` - Milvus 连接和 Collection 状态
   - `GET /health/redis` - Redis 连接状态
   - `GET /health/openai` - OpenAI API 可用性

**响应示例：**
```json
{
  "status": "healthy",
  "timestamp": "2026-05-08T10:30:00.000Z",
  "version": "0.1.0",
  "environment": "development",
  "checks": {
    "api": {"status": "healthy"},
    "milvus": {
      "status": "healthy",
      "host": "localhost",
      "port": 19530,
      "collection_exists": true
    },
    "redis": {
      "status": "healthy",
      "host": "localhost",
      "port": 6379
    },
    "openai": {
      "status": "healthy",
      "model": "gpt-4-turbo-preview",
      "base_url": "https://api.openai.com/v1"
    }
  }
}
```

### 5. 日志级别

- **INFO**: 请求摘要、检索结果、Token 消耗、服务初始化
- **DEBUG**: 详细耗时（Embedding、检索）
- **ERROR**: 异常堆栈（带 exc_info=True）

## 测试方法

### 1. 启动服务

```bash
# 确保基础设施运行
cd infrastructure
docker-compose up -d

# 启动 API 服务
cd ..
python -m api.main
```

### 2. 运行测试脚本

```bash
python test_api.py
```

测试脚本包含：
- 综合健康检查
- 独立健康检查（Milvus、Redis、OpenAI）
- 根路径测试
- 风控规则查询测试
- 错误处理测试（空查询、无效参数）

### 3. 查看日志

**控制台输出示例：**
```
2026-05-08 10:30:15 - api.services.rag_service - INFO - Milvus 连接成功 - Collection: unified_docs
2026-05-08 10:30:15 - api.services.rag_service - INFO - LLM 客户端初始化成功 - Model: gpt-4-turbo-preview
2026-05-08 10:30:15 - api.services.rag_service - INFO - RAG 服务初始化完成 - Collection: unified_docs, Model: gpt-4-turbo-preview
2026-05-08 10:30:20 - api.routers.risk_rules - INFO - [a1b2c3d4-...] 收到查询请求 - Query: 白金卡的单笔交易限额是多少？..., Session: None, TopK: 5
2026-05-08 10:30:20 - api.services.rag_service - DEBUG - Embedding 生成耗时: 120ms
2026-05-08 10:30:20 - api.services.rag_service - DEBUG - 向量检索耗时: 45ms, 返回结果数: 3
2026-05-08 10:30:20 - api.services.rag_service - INFO - 检索完成 - 原始结果: 3, 过滤后: 3 (阈值: 0.7)
2026-05-08 10:30:22 - api.services.rag_service - INFO - LLM 生成耗时: 1850ms
2026-05-08 10:30:22 - api.services.rag_service - INFO - LLM Token 消耗 - Prompt: 450, Completion: 120, Total: 570
2026-05-08 10:30:22 - api.routers.risk_rules - INFO - [a1b2c3d4-...] 查询成功 - Retrieved: 3, Time: 2015ms
```

**日志文件：** `logs/rag_system.log`

## 错误处理示例

### 1. Milvus 连接失败
```json
{
  "detail": "服务暂时不可用，请稍后重试: 无法连接到 Milvus: ..."
}
```
状态码：503

### 2. LLM 超时
```json
{
  "detail": "请求超时，请稍后重试: LLM 响应超时，请稍后重试"
}
```
状态码：504

### 3. 参数错误
```json
{
  "detail": "请求参数错误: ..."
}
```
状态码：400

### 4. OpenAI API Key 错误
```json
{
  "detail": "查询失败: OpenAI API 认证失败，请检查 API Key"
}
```
状态码：500

## 后续优化建议

### 阶段 1 完成项 ✅
- [x] API 路由前缀统一
- [x] 完整日志系统（request_id、耗时、Token）
- [x] 错误处理分类（400/503/504/500）
- [x] 健康检查增强（依赖服务状态）

### 阶段 2 准备
- [ ] Redis 会话管理
- [ ] session_id 实际使用
- [ ] 多轮对话上下文存储

### 阶段 3+
- [ ] Reranker 集成
- [ ] 增量数据更新
- [ ] Prometheus 指标导出
- [ ] LangSmith 追踪集成
- [ ] 降级策略（LLM 不可用时返回检索结果）

## 配置说明

在 `.env` 文件中可配置：

```bash
# 日志配置
LOG_LEVEL=INFO          # DEBUG | INFO | WARNING | ERROR
LOG_FILE=logs/rag_system.log

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# OpenAI 配置
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_API_BASE=https://api.openai.com/v1

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=unified_docs

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
```

## 修复总结

本次修复完成了阶段 1 的所有基础功能：

1. ✅ **API 路由规范化** - 符合 RESTful 设计
2. ✅ **完整日志系统** - 可追踪、可分析、可监控
3. ✅ **错误处理分类** - 明确错误类型，便于调试
4. ✅ **健康检查增强** - 实时监控依赖服务状态

系统现在具备：
- 生产级日志记录
- 详细的性能指标
- 完善的错误处理
- 全面的健康检查

可以进入阶段 2（多轮对话）或继续优化当前功能。

