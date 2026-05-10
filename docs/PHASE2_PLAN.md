---
metadata:
  task_name: "阶段2：多轮对话 + 会话管理"
  created: "2026-05-08"
  status: "planning"
  priority: "P0"
---

# 阶段 2：多轮对话 + 会话管理

## 目标

支持用户追问和上下文记忆，实现真正的对话式交互。

## 核心能力

- ✅ **多轮对话**：记忆上下文，支持追问
- ✅ **会话管理**：Redis 存储，30分钟过期
- ✅ **澄清机制**：检测到歧义时主动询问
- ❌ 暂不支持：自动钻取、并行执行、人工介入

## 技术方案

### 1. 架构调整

**当前架构（阶段 1）：**
```
用户请求 → FastAPI → RAGService → Milvus + LLM → 返回答案
```

**目标架构（阶段 2）：**
```
用户请求 → FastAPI → LangGraph Agent → Redis (会话状态)
                                      ↓
                                   Milvus + LLM
                                      ↓
                                   返回答案
```

### 2. 核心组件

#### 2.1 LangGraph StateGraph

**状态定义：**
```python
class ConversationState(TypedDict):
    session_id: str
    messages: List[BaseMessage]  # 对话历史
    query: str                   # 当前问题
    context: str                 # 检索到的上下文
    answer: str                  # 生成的答案
    sources: List[Dict]          # 来源文档
    needs_clarification: bool    # 是否需要澄清
    clarification_options: List[str]  # 澄清选项
```

**工作流节点：**
1. `analyze_query` - 分析用户问题（是否需要澄清）
2. `retrieve_context` - 检索相关文档
3. `generate_answer` - 生成答案
4. `save_state` - 保存会话状态

#### 2.2 Redis Checkpointer

**会话存储：**
```python
from langgraph.checkpoint.redis import RedisSaver

checkpointer = RedisSaver(
    redis_client=redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port
    )
)

# 配置会话过期时间
checkpointer.ttl = 1800  # 30 分钟
```

**会话 ID 生成：**
- 前端生成 UUID 作为 session_id
- 首次请求时创建会话
- 后续请求携带 session_id

#### 2.3 澄清机制

**触发条件：**
- 问题过于模糊（如"限额是多少？"）
- 检索到多个相关但不同的规则
- 缺少必要的上下文信息

**实现方式：**
```python
def analyze_query(state: ConversationState) -> ConversationState:
    query = state["query"]
    history = state["messages"]
    
    # 使用 LLM 判断是否需要澄清
    prompt = f"""
    基于对话历史和当前问题，判断是否需要澄清：
    
    对话历史：{history}
    当前问题：{query}
    
    如果问题明确，返回 "CLEAR"
    如果需要澄清，返回 "CLARIFY: [选项1, 选项2, ...]"
    """
    
    result = llm.predict(prompt)
    
    if result.startswith("CLARIFY"):
        state["needs_clarification"] = True
        state["clarification_options"] = parse_options(result)
    
    return state
```

### 3. API 调整

#### 3.1 请求模型更新

```python
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None  # 已有字段
    top_k: Optional[int] = None
    score_threshold: Optional[float] = None
    # 新增字段
    clarification_choice: Optional[str] = None  # 用户选择的澄清选项
```

#### 3.2 响应模型更新

```python
class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    retrieved_count: int
    session_id: str  # 必填，返回会话 ID
    # 新增字段
    needs_clarification: bool = False
    clarification_options: List[str] = []
    conversation_turn: int = 1  # 对话轮次
```

### 4. 实现步骤

#### Step 1: Redis 会话存储（1-2天）

**任务：**
- [ ] 安装 LangGraph Redis 依赖
- [ ] 实现 RedisSaver 配置
- [ ] 实现会话创建和恢复
- [ ] 实现会话过期管理
- [ ] 单元测试

**文件：**
- `api/services/session_manager.py` - 会话管理器
- `tests/test_session.py` - 会话测试

#### Step 2: LangGraph Agent 实现（2-3天）

**任务：**
- [ ] 定义 ConversationState
- [ ] 实现 analyze_query 节点
- [ ] 实现 retrieve_context 节点
- [ ] 实现 generate_answer 节点
- [ ] 实现 save_state 节点
- [ ] 构建 StateGraph
- [ ] 集成 RedisSaver

**文件：**
- `api/services/conversation_agent.py` - 对话 Agent
- `api/services/nodes/` - 各个节点实现
- `tests/test_agent.py` - Agent 测试

#### Step 3: 澄清机制（1-2天）

**任务：**
- [ ] 实现问题分析逻辑
- [ ] 实现澄清选项生成
- [ ] 实现用户选择处理
- [ ] 前端交互设计
- [ ] 集成测试

**文件：**
- `api/services/clarification.py` - 澄清逻辑
- `tests/test_clarification.py` - 澄清测试

#### Step 4: API 集成（1天）

**任务：**
- [ ] 更新 QueryRequest/QueryResponse
- [ ] 更新 risk_rules.py 路由
- [ ] 集成 ConversationAgent
- [ ] 更新 API 文档
- [ ] 集成测试

**文件：**
- `api/models/schemas.py` - 更新模型
- `api/routers/risk_rules.py` - 更新路由

#### Step 5: 测试和文档（1-2天）

**任务：**
- [ ] 端到端测试（3 轮以上对话）
- [ ] 澄清机制测试
- [ ] 会话过期测试
- [ ] 性能测试
- [ ] 更新文档

**文件：**
- `test_conversation.py` - 对话测试脚本
- `docs/CONVERSATION_GUIDE.md` - 对话功能文档

## 验收标准

### 功能验收

1. **多轮对话**
   - [ ] 支持 3 轮以上连续对话
   - [ ] 正确记忆上下文（用户提到的卡片类型、金额等）
   - [ ] 能够理解代词引用（"它"、"这个"等）

2. **会话管理**
   - [ ] 会话状态正确保存和恢复
   - [ ] 会话 30 分钟后自动过期
   - [ ] 支持多个并发会话

3. **澄清机制**
   - [ ] 能识别模糊问题
   - [ ] 提供 2-3 个澄清选项
   - [ ] 用户选择后继续对话

### 性能验收

- [ ] 首轮响应时间 < 3s（P95）
- [ ] 后续轮次响应时间 < 2s（P95）
- [ ] 会话恢复时间 < 100ms
- [ ] Redis 内存占用 < 100MB（1000 个会话）

### 质量验收

- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过率 100%
- [ ] 日志完整性 100%
- [ ] 错误处理覆盖所有异常场景

## 测试用例

### 用例 1：基础多轮对话

```
用户: 白金卡的单笔限额是多少？
系统: 白金卡的单笔交易限额是 50,000 元。

用户: 日累计呢？
系统: 白金卡的日累计限额是 200,000 元。

用户: 金卡的限额呢？
系统: 金卡的单笔交易限额是 20,000 元，日累计限额是 80,000 元。
```

### 用例 2：澄清机制

```
用户: 限额是多少？
系统: 请问您想查询哪种卡片的限额？
      1. 白金卡
      2. 金卡
      3. 普卡

用户: 白金卡
系统: 白金卡的单笔交易限额是 50,000 元，日累计限额是 200,000 元。
```

### 用例 3：会话恢复

```
# 第一次对话
用户: 白金卡的单笔限额是多少？
系统: 白金卡的单笔交易限额是 50,000 元。
[session_id: abc123]

# 5 分钟后，携带 session_id 继续对话
用户: 日累计呢？
系统: 白金卡的日累计限额是 200,000 元。
[session_id: abc123]
```

## 技术风险

### 风险 1：LangGraph 学习曲线

**影响：** 开发进度延迟

**缓解措施：**
- 先阅读官方文档和示例
- 从简单的 StateGraph 开始
- 逐步增加复杂度

### 风险 2：Redis 内存占用

**影响：** 大量会话时内存不足

**缓解措施：**
- 设置合理的 TTL（30 分钟）
- 只存储必要的状态信息
- 监控 Redis 内存使用

### 风险 3：澄清机制误判

**影响：** 用户体验下降

**缓解措施：**
- 保守策略：宁可不澄清，也不误判
- 收集用户反馈，持续优化
- 提供"跳过澄清"选项

## 依赖项

### Python 包

```bash
pip install langgraph
pip install redis
pip install langchain-redis
```

### 基础设施

- Redis 7+ （已有）
- Milvus 2.3+ （已有）
- OpenAI API （已有）

## 参考资料

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [LangGraph Checkpointer](https://langchain-ai.github.io/langgraph/how-tos/persistence/)
- [Redis Saver](https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-redis)

## 时间估算

| 任务 | 预计时间 | 依赖 |
|------|----------|------|
| Redis 会话存储 | 1-2 天 | - |
| LangGraph Agent | 2-3 天 | Redis 会话存储 |
| 澄清机制 | 1-2 天 | LangGraph Agent |
| API 集成 | 1 天 | 澄清机制 |
| 测试和文档 | 1-2 天 | API 集成 |

**总计：** 6-10 天（约 2 周）

## 下一步行动

1. 安装 LangGraph 和 Redis 依赖
2. 实现 Redis 会话管理器
3. 实现简单的 LangGraph Agent（无澄清）
4. 测试多轮对话
5. 增加澄清机制
6. 完整测试和文档

---

**创建时间：** 2026-05-08  
**预计完成：** 2026-05-22  
**负责人：** [待分配]
