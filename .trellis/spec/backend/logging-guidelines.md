# Logging Guidelines

> How logging is done in this project.

---

## Overview

本项目使用 Python 标准库 `logging` 模块，配置在 `api/logging_config.py`。

**日志特点**：
- JSON 格式日志（便于解析和分析）
- 包含 Request ID（用于追踪请求）
- 记录性能指标（耗时、Token 消耗）
- 分级日志（DEBUG/INFO/WARNING/ERROR）

---

## Log Levels

### 使用场景

| 级别 | 使用场景 | 示例 |
|-----|---------|------|
| `DEBUG` | 调试信息、详细的执行流程 | Embedding 生成耗时、向量检索参数 |
| `INFO` | 正常的业务流程、关键操作 | 服务启动、查询成功、缓存命中 |
| `WARNING` | 潜在问题、降级处理 | 检索结果为空、缓存失效 |
| `ERROR` | 错误、异常 | 连接失败、查询失败 |

### 示例

```python
# 参考：api/services/rag_service.py

# DEBUG - 性能指标
logger.debug(f"Embedding 生成耗时: {embed_time_ms}ms")
logger.debug(f"向量检索耗时: {retrieval_time_ms}ms, 返回结果数: {len(results[0])}")

# INFO - 业务流程
logger.info(f"Milvus 连接成功 - Collection: {settings.milvus_collection}")
logger.info(f"缓存命中 - query: {query[:50]}...")
logger.info(f"LLM Token 消耗 - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}")

# WARNING - 潜在问题
logger.warning(f"检索结果为空 - query: {query}")

# ERROR - 错误
logger.error(f"Milvus 连接失败: {e}", exc_info=True)
logger.error(f"LLM 调用失败: {e}", exc_info=True)
```

---

## Structured Logging

### 日志格式

使用 JSON 格式，便于日志分析工具解析：

```json
{
  "timestamp": "2026-05-09T14:32:15.123Z",
  "level": "INFO",
  "logger": "api.services.rag_service",
  "message": "查询成功",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "elapsed_ms": 1234
}
```

### 必需字段

每条日志应包含：
- `timestamp` - 时间戳
- `level` - 日志级别
- `logger` - 日志来源（模块名）
- `message` - 日志消息

### 可选字段

根据场景添加：
- `request_id` - 请求 ID（用于追踪）
- `elapsed_ms` - 耗时（毫秒）
- `user_id` - 用户 ID
- `session_id` - 会话 ID

---

## What to Log

### 必须记录的事件

1. **服务启动/关闭**
   ```python
   # 参考：api/main.py:25-33
   print(f"🚀 {settings.app_name} v{settings.app_version} 启动中...")
   print(f"   环境: {settings.environment}")
   ```

2. **外部服务连接**
   ```python
   # 参考：api/services/rag_service.py:34-36
   logger.info(f"Milvus 连接成功 - Collection: {settings.milvus_collection}")
   logger.info(f"LLM 客户端初始化成功 - Model: {settings.openai_model}")
   ```

3. **API 请求**
   ```python
   # 参考：api/routers/risk_rules.py:60-63
   logger.info(
       f"[{request_id}] 收到查询请求 - Query: {request.query[:50]}..., "
       f"Session: {request.session_id}, TopK: {request.top_k}"
   )
   ```

4. **业务操作结果**
   ```python
   # 参考：api/routers/risk_rules.py:84-87
   logger.info(
       f"[{request_id}] 查询成功 - Retrieved: {result['retrieved_count']}, "
       f"Session: {result['session_id']}, Time: {elapsed_ms}ms"
   )
   ```

5. **性能指标**
   ```python
   # 参考：api/services/rag_service.py:102, 125, 159
   logger.debug(f"Embedding 生成耗时: {embed_time_ms}ms")
   logger.debug(f"向量检索耗时: {retrieval_time_ms}ms")
   logger.info(f"LLM 生成耗时: {llm_time_ms}ms")
   ```

6. **LLM Token 消耗**
   ```python
   # 参考：api/services/rag_service.py:247-251
   logger.info(
       f"LLM Token 消耗 - Prompt: {usage.prompt_tokens}, "
       f"Completion: {usage.completion_tokens}, "
       f"Total: {usage.total_tokens}"
   )
   ```

7. **错误和异常**
   ```python
   # 参考：api/services/rag_service.py:38-39
   logger.error(f"Milvus 连接失败: {e}", exc_info=True)
   ```

---

## What NOT to Log

### 禁止记录的内容

1. **敏感信息**
   - ❌ API Key、密码、Token
   - ❌ 用户的完整查询内容（可以截断）
   - ❌ 个人身份信息（PII）

2. **大量数据**
   - ❌ 完整的文档内容
   - ❌ 完整的向量数据
   - ❌ 大型 JSON 对象

3. **高频日志**
   - ❌ 循环内的 DEBUG 日志
   - ❌ 每次缓存查询的日志

### 正确的做法

```python
# ❌ 错误：记录完整查询
logger.info(f"查询: {query}")

# ✅ 正确：截断长文本
logger.info(f"查询: {query[:50]}...")

# ❌ 错误：记录 API Key
logger.info(f"使用 API Key: {settings.openai_api_key}")

# ✅ 正确：不记录敏感信息
logger.info(f"LLM 客户端初始化成功 - Model: {settings.openai_model}")
```

---

## Logger Configuration

### 获取 Logger

在每个模块顶部获取 logger：

```python
import logging

logger = logging.getLogger(__name__)
```

**规范**：
- 使用 `__name__` 作为 logger 名称（自动使用模块路径）
- 不要使用 `logging.getLogger()` 无参数形式

### 日志配置

日志配置在 `api/logging_config.py`：

```python
# 参考：api/logging_config.py
def setup_logging(log_level: str, log_file: str):
    # 配置日志格式、输出目标、日志级别
    pass
```

在应用启动时调用：

```python
# 参考：api/main.py:14-18
from api.logging_config import setup_logging

setup_logging(
    log_level=settings.log_level,
    log_file=settings.log_file
)
```

---

## Best Practices

### 1. 使用 f-string 格式化

```python
# ✅ 推荐
logger.info(f"查询成功 - Retrieved: {count}, Time: {elapsed_ms}ms")

# ❌ 不推荐
logger.info("查询成功 - Retrieved: %d, Time: %dms" % (count, elapsed_ms))
```

### 2. 包含上下文信息

```python
# ✅ 推荐：包含 request_id
logger.info(f"[{request_id}] 查询成功 - Time: {elapsed_ms}ms")

# ❌ 不推荐：缺少上下文
logger.info(f"查询成功")
```

### 3. 错误日志包含堆栈

```python
# ✅ 推荐：记录完整堆栈
except Exception as e:
    logger.error(f"查询失败: {e}", exc_info=True)

# ❌ 不推荐：只记录错误消息
except Exception as e:
    logger.error(f"查询失败: {e}")
```

### 4. 避免字符串拼接

```python
# ✅ 推荐：使用 f-string
logger.info(f"查询: {query[:50]}...")

# ❌ 不推荐：字符串拼接
logger.info("查询: " + query[:50] + "...")
```

---

## Examples

### 完整的日志示例

参考：`api/routers/risk_rules.py:24-122`
- 请求开始：记录 request_id、查询参数
- 请求成功：记录结果统计、耗时
- 请求失败：记录错误类型、错误消息、堆栈

参考：`api/services/rag_service.py:65-177`
- 缓存命中：记录查询内容（截断）
- 性能指标：记录各阶段耗时
- Token 消耗：记录 LLM Token 使用情况
