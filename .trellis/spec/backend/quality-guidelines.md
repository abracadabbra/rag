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
