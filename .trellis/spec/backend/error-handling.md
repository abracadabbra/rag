# Error Handling

> How errors are handled in this project.

---

## Overview

本项目使用 **分层错误处理**：
- **服务层**：抛出特定的 Python 异常（`ConnectionError`, `TimeoutError`, `ValueError`）
- **路由层**：捕获异常并转换为 HTTP 状态码
- **响应格式**：统一的 JSON 错误响应

---

## Error Types

### Python 异常类型

默认使用 Python 内置异常，不定义自定义异常类：

| 异常类型 | 使用场景 | HTTP 状态码 |
|---------|---------|-----------|
| `ConnectionError` | 数据库连接失败、LLM 调用失败 | 503 Service Unavailable |
| `TimeoutError` | 请求超时 | 504 Gateway Timeout |
| `ValueError` | 参数验证失败 | 400 Bad Request |
| `Exception` | 未预期的错误 | 500 Internal Server Error |

### Business Contract Exception

业务系统 HTTP 返回合同校验允许一个窄例外：`BusinessContractError`。

- 必须继承 `ValueError`，保持路由层和调用方的参数/合同错误语义。
- 只能用于业务接口响应形状校验，例如缺少必填字段、字段类型异常、非对象 JSON、风控命中规则或毛利链路格式异常。
- 可携带 `diagnostic_code`、`missing_fields`、`invalid_fields` 等结构化诊断字段。
- 诊断字段只能包含字段名、合同类型标签和稳定错误码，不能包含真实 payload 值、密钥、URL、账号、手机号、证件号或堆栈细节。
- 非合同错误（网络、鉴权、运行时异常）不得通过该异常向前端暴露原始异常内容。

**示例**：

```python
# 参考：api/services/rag_service.py:38-39
except Exception as e:
    logger.error(f"Milvus 连接失败: {e}", exc_info=True)
    raise ConnectionError(f"无法连接到 Milvus: {e}")
```

---

## Error Handling Patterns

### 服务层错误处理

服务层抛出异常，不返回错误对象：

```python
# 参考：api/services/rag_service.py:120-122
try:
    results = self.collection.search(...)
except Exception as e:
    logger.error(f"Milvus 检索失败: {e}", exc_info=True)
    raise ConnectionError(f"向量检索失败: {e}")
```

**规范**：
- 捕获具体的异常类型，不要使用裸 `except`
- 记录完整的异常堆栈（`exc_info=True`）
- 抛出语义化的异常（`ConnectionError` 表示服务不可用）
- 异常消息包含足够的上下文信息

### 路由层错误处理

路由层捕获异常并转换为 HTTP 响应：

```python
# 参考：api/routers/risk_rules.py:99-122
try:
    result = agent.process(...)
    return QueryResponse(...)
except ConnectionError as e:
    logger.error(f"[{request_id}] 连接失败 - {str(e)}", exc_info=True)
    raise HTTPException(status_code=503, detail=f"服务暂时不可用: {str(e)}")
except TimeoutError as e:
    logger.error(f"[{request_id}] 请求超时 - {str(e)}", exc_info=True)
    raise HTTPException(status_code=504, detail=f"请求超时: {str(e)}")
except ValueError as e:
    logger.error(f"[{request_id}] 参数错误 - {str(e)}")
    raise HTTPException(status_code=400, detail=f"请求参数错误: {str(e)}")
except Exception as e:
    logger.error(f"[{request_id}] 查询失败 - {str(e)}", exc_info=True)
    raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
```

**规范**：
- 按照异常类型分别处理，从具体到通用
- 每个异常都记录日志（包含 request_id）
- 使用 `HTTPException` 返回标准的 HTTP 错误响应
- 错误消息对用户友好，不暴露内部实现细节

---

## API Error Responses

### 响应格式

使用 FastAPI 的 `HTTPException`，自动生成标准格式：

```json
{
  "detail": "服务暂时不可用，请稍后重试: 无法连接到 Milvus"
}
```

### 状态码映射

| 状态码 | 含义 | 使用场景 |
|-------|------|---------|
| 400 | Bad Request | 参数验证失败 |
| 500 | Internal Server Error | 未预期的错误 |
| 503 | Service Unavailable | 依赖服务不可用（Milvus/Redis/OpenAI） |
| 504 | Gateway Timeout | LLM 调用超时 |

### 错误响应模型

定义 Pydantic 模型用于 API 文档：

```python
# 参考：api/models/response.py
class ErrorResponse(BaseModel):
    detail: str
    request_id: Optional[str] = None
```

在路由中声明：

```python
@router.post(
    "/query",
    response_model=QueryResponse,
    responses={
        500: {"model": ErrorResponse, "description": "服务器错误"}
    }
)
```

---

## Logging Best Practices

### 错误日志格式

```python
# 包含 request_id、错误类型、错误消息
logger.error(f"[{request_id}] 连接失败 - {str(e)}", exc_info=True)
```

**规范**：
- 使用 `logger.error()` 记录错误
- 包含 `request_id` 用于追踪
- 使用 `exc_info=True` 记录完整堆栈
- 错误消息简洁明了

### 不同错误级别的日志

```python
# 参数错误：不需要堆栈（用户输入问题）
logger.error(f"[{request_id}] 参数错误 - {str(e)}")

# 系统错误：需要堆栈（代码或依赖问题）
logger.error(f"[{request_id}] 连接失败 - {str(e)}", exc_info=True)
```

---

## Common Mistakes

### ❌ 吞掉异常

```python
# 错误：捕获异常但不处理
try:
    result = service.query(...)
except Exception:
    pass  # 静默失败，难以调试
```

```python
# 正确：记录日志并重新抛出
try:
    result = service.query(...)
except Exception as e:
    logger.error(f"查询失败: {e}", exc_info=True)
    raise
```

### ❌ 使用裸 except

```python
# 错误：捕获所有异常（包括 KeyboardInterrupt）
try:
    result = service.query(...)
except:
    logger.error("查询失败")
```

```python
# 正确：明确捕获的异常类型
try:
    result = service.query(...)
except (ConnectionError, TimeoutError) as e:
    logger.error(f"查询失败: {e}", exc_info=True)
```

### ❌ 错误消息暴露内部细节

```python
# 错误：暴露数据库连接字符串
raise HTTPException(
    status_code=503,
    detail=f"连接失败: postgresql://user:pass@host:5432/db"
)
```

```python
# 正确：用户友好的错误消息
raise HTTPException(
    status_code=503,
    detail="服务暂时不可用，请稍后重试"
)
```

### ❌ 不记录异常堆栈

```python
# 错误：只记录错误消息
except Exception as e:
    logger.error(f"查询失败: {str(e)}")
```

```python
# 正确：记录完整堆栈
except Exception as e:
    logger.error(f"查询失败: {str(e)}", exc_info=True)
```
