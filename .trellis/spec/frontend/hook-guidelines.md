# Hook Guidelines

> How hooks are used in this project.

---

## Overview

**注意**：本项目目前没有前端代码，以下是规划的 Hook 规范。

---

## Custom Hook Patterns

自定义 Hook 命名以 `use` 开头：

```tsx
// src/hooks/useChat.ts
export const useChat = (sceneType: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  
  const sendMessage = async (query: string) => {
    setLoading(true);
    try {
      const response = await queryRiskRules(query);
      setMessages([...messages, { query, answer: response.answer }]);
    } finally {
      setLoading(false);
    }
  };
  
  return { messages, loading, sendMessage };
};
```

---

## Data Fetching

计划使用 **React Query** 或 **SWR** 处理数据获取。

---

## Naming Conventions

- 自定义 Hook：`use<Name>`（例如：`useChat`, `useSession`）
- 返回值：使用对象而不是数组（便于命名）

---

## Common Mistakes

（待前端开发后补充）
