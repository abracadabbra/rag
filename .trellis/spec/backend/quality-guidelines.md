# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

本项目使用以下工具保证代码质量：
- **Black** - 代码格式化（line-length=100）
- **isort** - import 排序
- **mypy** - 类型检查
- **pytest** - 单元测试

配置文件：`pyproject.toml`

---

## Code Formatting

### Black

使用 Black 自动格式化代码：

```bash
black .
```

**配置**（`pyproject.toml`）：
```toml
[tool.black]
line-length = 100
target-version = ['py310']
include = '\.pyi?$'
```

**规范**：
- 行长度：100 字符
- 目标版本：Python 3.10+
- 提交前必须运行 Black

### isort

使用 isort 排序 import：

```bash
isort .
```

**配置**（`pyproject.toml`）：
```toml
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
```

**规范**：
- 使用 Black 兼容模式
- import 顺序：标准库 → 第三方库 → 本地模块
- 每组之间空一行

---

## Type Checking

### mypy

使用 mypy 进行类型检查：

```bash
mypy .
```

**配置**（`pyproject.toml`）：
```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
ignore_missing_imports = true
```

**规范**：
- 函数参数和返回值添加类型注解
- 使用 `typing` 模块的类型（`List`, `Dict`, `Optional`）
- 允许第三方库缺少类型定义

**示例**：

```python
# 参考：api/services/rag_service.py:65-71
def query(
    self,
    query: str,
    scene_type: str,
    top_k: int = None,
    score_threshold: float = None
) -> Dict[str, Any]:
    """执行 RAG 查询"""
    pass
```

---

## Testing Requirements

### pytest

使用 pytest 编写和运行测试：

```bash
pytest tests/
```

**配置**（`pyproject.toml`）：
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=api --cov=ingestion --cov-report=html --cov-report=term"
```

### 测试覆盖率

目标：> 80% 覆盖率

```bash
pytest --cov=api --cov=ingestion --cov-report=html
```

### 测试文件组织

```
tests/
├── test_api.py           # API 集成测试
├── test_session.py       # 会话管理测试
└── conftest.py           # pytest fixtures
```

**规范**：
- 测试文件命名：`test_*.py`
- 测试函数命名：`test_*`
- 使用 fixtures 共享测试数据

---

## Forbidden Patterns

### ❌ 硬编码配置

```python
# 错误：硬编码
MILVUS_HOST = "localhost"
MILVUS_PORT = 19530
```

```python
# 正确：从配置读取
from api.config import settings

host = settings.milvus_host
port = settings.milvus_port
```

### ❌ 全局可变状态

```python
# 错误：全局变量
cache = {}

def get_cache(key):
    return cache.get(key)
```

```python
# 正确：使用单例模式
class CacheService:
    def __init__(self):
        self.cache = {}
    
    def get(self, key):
        return self.cache.get(key)

_cache_service = None

def get_cache_service():
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
```

### ❌ 裸 except

```python
# 错误：捕获所有异常
try:
    result = query()
except:
    pass
```

```python
# 正确：明确异常类型
try:
    result = query()
except (ConnectionError, TimeoutError) as e:
    logger.error(f"查询失败: {e}", exc_info=True)
    raise
```

### ❌ 字符串拼接构建 SQL/查询

```python
# 错误：SQL 注入风险
query = f"SELECT * FROM users WHERE name = '{user_input}'"
```

```python
# 正确：使用参数化查询
query = "SELECT * FROM users WHERE name = ?"
cursor.execute(query, (user_input,))
```

---

## Required Patterns

### ✅ 使用 Pydantic 进行配置管理

```python
# 参考：api/config.py:11-115
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "RAG System"
    milvus_host: str = "localhost"
    
    class Config:
        env_file = ".env"
```

## Scenario: Runtime Settings Env Writes

### 1. Scope / Trigger

- Trigger: Backend settings APIs write runtime configuration into `.env`.
- Applies to: `api/services/settings_service.py`, `api/routers/settings.py`, and settings tests.

### 2. Signatures

- Service read: `get_llm_settings() -> dict`
- Service write: `update_llm_settings(updates: dict) -> dict`
- API write: `PATCH /api/v1/settings/`

### 3. Contracts

- Only keys in `LLM_CONFIG_KEYS` may be written.
- API keys returned by `get_llm_settings()` must be masked.
- Values written to `.env` must be strings.
- Boolean values must be persisted as lowercase `true` / `false`, not Python `True` / `False`.
- Empty API key fields from the frontend should not overwrite existing secrets.

### 4. Validation & Error Matrix

- Unknown key -> ignored by `update_llm_settings()`.
- `None` value -> skipped.
- Invalid `llm_provider` -> router returns 422.
- Invalid numeric bounds such as confidence outside `0..1` -> router returns 422.

### 5. Good/Base/Bad Cases

- Good: `{"enable_business_tool_llm_intent": True}` writes `enable_business_tool_llm_intent=true`.
- Base: `{"business_tool_llm_intent_min_confidence": 0.82}` writes `0.82`.
- Bad: writing raw booleans and producing `enable_business_tool_llm_intent=True`.

### 6. Tests Required

- Settings service test should assert business tool intent fields are exposed.
- Settings service test should assert boolean updates round-trip as lowercase strings.
- Settings API test should assert confidence validation accepts `0..1` and rejects values outside that range.

### 7. Wrong vs Correct

#### Wrong

```python
env_vars[key] = value
```

#### Correct

```python
env_vars[key] = _format_env_value(value)
```

## Scenario: Business Tool Result Exposure

### 1. Scope / Trigger

- Trigger: Business tools call real systems and pass data to prompts and frontend UI.
- Applies to: `api/services/tool_service.py`, `api/services/business_clients.py`, scene APIs, and `QAView.vue`.

### 2. Signatures

- Tool execution: `BusinessToolService.maybe_execute(query: str, scene_type: str) -> list[dict]`
- Prompt injection: `BusinessToolService.format_tool_context(tool_calls: list[dict]) -> str`
- Frontend payload: `QueryResponse.tool_calls` and SSE `sources.tool_calls`

### 3. Contracts

- Business clients may validate and return full response payloads from real systems.
- `BusinessToolService` must filter tool results through a per-tool allowlist before returning `tool_calls.result`.
- Prompt context must be formatted from the filtered `tool_calls.result`, not the raw client payload.
- Audit logs may include top-level result keys, but must not log full payload values.
- Profit `result.chain` should end with `平台净毛利` when chain data is available.
- Tool calls should include safe interface metadata: `data_source` (`mock` or `http`) and `endpoint_path`.
- Audit logs should record endpoint templates such as `/profit/orders/{order_id}/chain`, not raw order ids embedded in paths.
- When `BusinessToolService.maybe_execute()` adds a new top-level `tool_calls[*]`
  field for frontend or prompt explainability, `api/models/schemas.py::ToolCall`
  must expose the same field. Otherwise non-streaming `QueryResponse` will
  silently drop it during Pydantic serialization even if SSE still includes it.

### 4. Validation & Error Matrix

- Missing required contract field -> business client raises `ValueError`; tool call returns `status="error"` with generic summary.
- Unknown extra field in real response -> accepted by client validation but excluded from `tool_calls.result`.
- Nested unknown field under `hit_rules`, `chain`, or detail objects -> excluded from frontend and prompt context.

### 5. Good/Base/Bad Cases

- Good: profit response includes `payment_account`; audit logs key names only, and `tool_calls.result` omits it.
- Good: `tool_calls` includes `endpoint_path` for frontend explainability, while audit logs use the masked argument plus endpoint template.
- Base: profit response includes allowlisted `chain.node` and `chain.amount`; frontend renders the money-flow strip.
- Bad: passing raw client payload directly into `tool_calls.result` or `format_tool_context()`.

### 6. Tests Required

- Tool service test should include extra sensitive fields and assert they are absent from `tool_calls.result`.
- The same test should assert sensitive values are absent from `format_tool_context()`.
- Business client tests should continue validating required fields and nested chain/rule contracts.
- API regression tests should assert non-streaming `QueryResponse.tool_calls`
  preserves frontend-facing explainability fields such as `audit_id`,
  `endpoint_path`, `data_source`, `error_type`, `selection_reason`, and
  `confidence`.
- Frontend contract tests should assert `QAView.vue` renders every
  frontend-facing field that backend `tool_calls` promises.

### 7. Wrong vs Correct

#### Wrong

```python
result = tool.executor(order_id)
```

```python
# Added in BusinessToolService, but missing from api.models.schemas.ToolCall.
return {"endpoint_path": endpoint_path, "data_source": data_source}
```

#### Correct

```python
raw_result = tool.executor(order_id)
result = self._filter_result_for_display(tool.name, raw_result)
```

```python
class ToolCall(BaseModel):
    endpoint_path: Optional[str] = Field(None, description="业务工具接口路径")
    data_source: Optional[str] = Field(None, description="业务工具数据源: mock/http")
```

## Scenario: Business Tool Path Parameter Safety

### 1. Scope / Trigger

- Trigger: Business tools render external HTTP paths from user or LLM-derived
  order identifiers.
- Applies to: `api/services/business_contracts.py`,
  `api/services/tool_service.py`, `api/services/business_clients.py`, and
  `api/routers/business_tools.py`.

### 2. Signatures

- Contract helper: `normalize_order_id(order_id: Any) -> str`
- Endpoint renderer: `endpoint_path(tool_name: str, *, order_id: str) -> str`
- Probe API: `POST /api/v1/business-tools/probe`

### 3. Contracts

- `order_id` used as an HTTP path parameter must match
  `^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$`.
- Empty values, whitespace, `/`, `.`, `?`, `#`, `&`, `%`, and other URL/path
  control characters must be rejected before any business-system call.
- Endpoint templates may still be rendered with the literal `{order_id}` for
  runtime status, audit templates, and contract docs.
- LLM-supplied `order_id` must be normalized before use. If invalid, ignore it
  and only fall back to a safe order id extracted from the original user query;
  otherwise ask for clarification.

### 4. Validation & Error Matrix

- Empty `order_id` -> `ValueError("order_id is required")`.
- Unsafe `order_id` -> `ValueError("order_id contains unsupported characters")`.
- Probe route catches these `ValueError`s and returns HTTP 400.
- Invalid LLM `order_id` without a safe query fallback -> no tool execution,
  `missing_fields=["order_id"]`.

### 5. Good/Base/Bad Cases

- Good: `ORD88888` renders `/profit/orders/ORD88888/chain`.
- Base: `{order_id}` renders `/profit/orders/{order_id}/chain` for templates.
- Bad: `../admin?token=secret` must not render an endpoint path or call HTTP.

### 6. Tests Required

- Contract/client tests should assert endpoint templates still render correctly.
- Tool service tests should assert invalid LLM `order_id` does not execute.
- Tool service tests should assert invalid LLM `order_id` can fall back to a
  safe order id found in the user query.
- Probe/API tests should assert unsafe `order_id` returns HTTP 400 and does not
  leak the unsafe value or token-like substrings.

### 7. Wrong vs Correct

#### Wrong

```python
return template.format(order_id=order_id)
```

#### Correct

```python
safe_order_id = normalize_order_id(order_id)
return template.format(order_id=safe_order_id)
```

## Scenario: Session Message Metadata

### 1. Scope / Trigger

- Trigger: Assistant messages need to restore tool calls, tool intent, and retrieval metadata from session history.
- Applies to: `api/services/session_manager.py`, `api/routers/sessions.py`, `ConversationAgent`, and `QAView.vue`.

### 2. Signatures

- Persist message: `SessionManager.add_message(session_id, role, content, metadata=None) -> bool`
- Fetch session: `GET /api/v1/sessions/{session_id}`

### 3. Contracts

- Each `Message` must carry its own `metadata: dict`.
- Assistant message metadata is the source of truth for historical UI restoration.
- Session-level metadata may keep latest conversational context, such as missing-field `tool_intent` used to rebuild a clarified query.
- `GET /api/v1/sessions/{session_id}` must return `metadata` on every message object.

### 4. Validation & Error Matrix

- Old messages without metadata -> model defaults to `{}`.
- Multiple assistant messages with different `tool_calls` -> each message returns its own metadata.
- Latest session-level metadata -> must not overwrite older message metadata in history responses.

### 5. Good/Base/Bad Cases

- Good: first assistant message has risk `tool_calls`, second has profit `tool_calls`; history returns both separately.
- Base: user message has empty metadata.
- Bad: frontend reconstructs every assistant message from `state.metadata.tool_calls`.

### 6. Tests Required

- Session manager test should assert message-level metadata survives multiple assistant messages.
- Sessions API test should assert message objects include their own metadata.

### 7. Wrong vs Correct

#### Wrong

```python
state.metadata.update(metadata)
```

#### Correct

```python
message = Message(..., metadata=metadata or {})
state.messages.append(message)
state.metadata.update(metadata)
```

### ✅ 使用单例模式管理服务

```python
# 参考：api/services/rag_service.py:292-300
_rag_service: Optional[RAGService] = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
```

### ✅ 使用 Pydantic 模型验证请求

```python
# 参考：api/models/request.py
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)
```

### ✅ 使用 docstring 文档化函数

```python
# 参考：api/services/rag_service.py:65-83
def query(
    self,
    query: str,
    scene_type: str,
    top_k: int = None,
    score_threshold: float = None
) -> Dict[str, Any]:
    """
    执行 RAG 查询

    Args:
        query: 用户问题
        scene_type: 场景类型
        top_k: 返回文档数量
        score_threshold: 相似度阈值

    Returns:
        查询结果，包含 answer 和 sources
    """
    pass
```

---

## Code Review Checklist

### 功能性

- [ ] 代码实现了需求
- [ ] 边界条件处理正确
- [ ] 错误处理完整

### 代码质量

- [ ] 通过 Black 格式化
- [ ] 通过 isort 排序
- [ ] 通过 mypy 类型检查
- [ ] 函数有类型注解
- [ ] 复杂逻辑有注释

### 测试

- [ ] 有对应的单元测试
- [ ] 测试覆盖主要逻辑
- [ ] 测试通过

### 安全性

- [ ] 没有硬编码的密钥
- [ ] 没有 SQL 注入风险
- [ ] 敏感信息不记录到日志

### 性能

- [ ] 没有 N+1 查询
- [ ] 使用了缓存（如果适用）
- [ ] 批量操作使用批量接口

### 可维护性

- [ ] 函数职责单一
- [ ] 命名清晰
- [ ] 没有重复代码
- [ ] 配置从 settings 读取

---

## Pre-commit Checklist

提交代码前必须执行：

```bash
# 1. 格式化代码
black .
isort .

# 2. 类型检查
mypy .

# 3. 运行测试
pytest tests/

# 4. 检查覆盖率
pytest --cov=api --cov=ingestion --cov-report=term
```

---

## Examples

### 良好的代码示例

**api/services/rag_service.py**
- ✅ 完整的类型注解
- ✅ 详细的 docstring
- ✅ 单例模式
- ✅ 完整的错误处理
- ✅ 详细的日志记录

**api/config.py**
- ✅ 使用 Pydantic Settings
- ✅ 从 .env 读取配置
- ✅ 提供默认值
- ✅ 使用 @lru_cache 缓存配置

**ingestion/loaders.py**
- ✅ 基类 + 多个实现类
- ✅ 工厂函数
- ✅ 便捷函数
- ✅ 错误处理
