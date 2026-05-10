# Type Safety

> Type safety patterns in this project.

---

## Overview

**注意**：本项目目前没有前端代码，以下是规划的类型安全规范。

使用 **TypeScript** 进行类型检查。

---

## Type Organization

```
src/types/
├── api.ts        # API 请求/响应类型
└── models.ts     # 数据模型类型
```

---

## Validation

计划使用 **Zod** 进行运行时验证。

---

## Common Patterns

- 使用接口定义对象类型
- 使用类型别名定义联合类型
- 避免使用 `any`

---

## Forbidden Patterns

- ❌ 使用 `any`
- ❌ 使用 `as` 类型断言（除非必要）
- ❌ 忽略 TypeScript 错误（`@ts-ignore`）
