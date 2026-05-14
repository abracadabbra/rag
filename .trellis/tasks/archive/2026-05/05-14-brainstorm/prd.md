# brainstorm: 前端会话管理组件

## Goal

实现前端会话管理组件，支持多轮对话历史、跨会话检索、会话列表展示。

## What I already know

* 后端已有 `session_manager.py` 和 Redis 会话存储
* 前端已有 `session_id` 支持，但仅用于多轮对话
* 前端 API (`api.js`) 暂无会话管理接口
* 已有 `cache.py` 缓存管理 API
* 会话存储在后端 Redis，前端无持久化

## Open Questions

* ~~会话列表是后端提供还是前端本地管理？~~ → **后端 Redis 维护索引**

## Requirements (evolving)

* [ ] 后端：会话列表 API（获取所有会话、删除会话）
* [ ] 前端：会话列表组件（侧边栏）
* [ ] 前端：会话选择/切换
* [ ] 前端：新建/删除会话
* [ ] 前端：当前会话的问答历史展示

## Decision (ADR-lite)

**Context**: 需要在多场景间共享会话列表
**Decision**: Redis 维护 `sessions:index` 索引，后端提供 API
**Consequences**: 需要扩展 session_manager.py，增加会话列表功能

## Technical Notes

* 前端: Vue 3 + localStorage
* 后端: session_manager.py + Redis
* API 路由前缀: `/api/v1/cache`
