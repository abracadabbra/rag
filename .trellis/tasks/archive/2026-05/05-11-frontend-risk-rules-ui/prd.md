# frontend: 风控规则问答界面

## Decision (ADR-lite)

**Context**: 需要为 RAG 系统开发前端界面
**Decision**: 使用 Vue 3 + Vite，前端目录 `/frontend/`
**Consequences**: 选择轻量级框架，上手快，适合 MVP 阶段

---

## Goal

为 RAG 系统开发前端界面，支持用户进行风控规则问答，包括：问题输入、答案展示、来源文档显示、多轮会话管理。

---

## Requirements

### 功能需求

1. **问答界面**
   - 问题输入框（Textarea，支持回车提交）
   - 发送按钮
   - 加载状态显示

2. **答案展示**
   - AI 回答文本显示
   - 支持 Markdown 基础渲染

3. **来源文档展示**
   - 规则 ID
   - 规则名称
   - 相似度分数
   - 内容预览

4. **会话管理**
   - 自动创建 session_id
   - 多轮对话支持（同一 session 连续问答）
   - 新建会话按钮

5. **澄清机制**
   - 如果 API 返回 `needs_clarification: true`
   - 显示澄清选项供用户选择

6. **错误处理**
   - API 失败时显示错误信息
   - 网络断开提示
   - 空答案提示

---

## Acceptance Criteria

- [ ] 可以输入问题并发送
- [ ] 答案正确显示
- [ ] 来源文档正确显示（规则ID、名称、分数、预览）
- [ ] 多轮对话正常（session_id 保持）
- [ ] 加载状态显示（发送时禁用输入）
- [ ] 错误状态处理（API 失败提示）
- [ ] 澄清选项显示（当 API 需要时）

---

## Definition of Done

- [ ] Vue 3 + Vite 项目创建完成
- [ ] 问答组件实现
- [ ] API 调用集成
- [ ] 样式美观（基础 CSS）
- [ ] 本地可运行（`npm run dev`）

---

## Out of Scope

- 用户认证/权限
- 多场景切换（风控/模型卡片/仿真/毛利）
- 流式输出（打字机效果）
- 复杂样式/动画
- 移动端适配
- 会话历史保存

---

## Technical Notes

### Backend API

- **Base URL**: `http://localhost:8000`
- **Query Endpoint**: `POST /api/v1/risk-rules/query`
- **Health Check**: `GET /health`
- **CORS**: 已配置 localhost:5173 (Vite 默认)

### API Contract

Request:
```json
{
  "query": "问题内容",
  "session_id": "可选",
  "top_k": 5,
  "score_threshold": 0.7,
  "clarification_choice": "可选"
}
```

Response:
```json
{
  "answer": "答案内容",
  "sources": [
    {
      "score": 0.95,
      "content_preview": "...",
      "rule_id": "R001",
      "rule_name": "规则名称"
    }
  ],
  "retrieved_count": 3,
  "session_id": "会话ID",
  "needs_clarification": false,
  "clarification_options": []
}
```

### 项目结构

```
/frontend/               # Vue 3 项目
├── src/
│   ├── components/      # 组件
│   │   ├── ChatInput.vue
│   │   ├── AnswerDisplay.vue
│   │   └── SourceList.vue
│   ├── views/           # 页面
│   │   └── RiskRulesQA.vue
│   ├── services/        # API 调用
│   │   └── api.js
│   ├── App.vue
│   └── main.js
├── index.html
└── vite.config.js
```
