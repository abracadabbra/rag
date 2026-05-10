# Quality Guidelines

> Code quality standards for frontend development.

---

## Overview

**注意**：本项目目前没有前端代码，以下是规划的质量标准。

计划使用：
- **ESLint** - 代码检查
- **Prettier** - 代码格式化
- **Vitest** - 单元测试
- **React Testing Library** - 组件测试

---

## Forbidden Patterns

- ❌ 使用 `any` 类型
- ❌ 直接修改 state（使用 `setState`）
- ❌ 在循环中使用 Hooks

---

## Required Patterns

- ✅ 使用 TypeScript
- ✅ 使用函数组件 + Hooks
- ✅ Props 使用接口定义

---

## Testing Requirements

- 关键组件需要单元测试
- API 调用需要 Mock

---

## Code Review Checklist

- [ ] 通过 ESLint 检查
- [ ] 通过 TypeScript 类型检查
- [ ] 组件有 Props 类型定义
- [ ] 测试通过
