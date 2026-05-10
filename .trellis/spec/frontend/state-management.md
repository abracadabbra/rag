# State Management

> How state is managed in this project.

---

## Overview

**注意**：本项目目前没有前端代码，以下是规划的状态管理方案。

计划使用 **React Context + Hooks** 管理全局状态，**React Query** 管理服务端状态。

---

## State Categories

- **Local State** - 组件内部状态（`useState`）
- **Global State** - 跨组件共享状态（React Context）
- **Server State** - 服务端数据（React Query）
- **URL State** - 路由参数（React Router）

---

## When to Use Global State

- 用户认证信息
- 当前会话 ID
- 主题设置

---

## Server State

使用 React Query 管理：
- 自动缓存
- 自动重新获取
- 乐观更新

---

## Common Mistakes

（待前端开发后补充）
