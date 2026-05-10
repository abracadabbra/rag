# Component Guidelines

> How components are built in this project.

---

## Overview

**注意**：本项目目前没有前端代码，以下是规划的组件规范。

计划使用 **React 18+ with TypeScript**，采用函数组件 + Hooks 模式。

---

## Component Structure

```tsx
// 标准组件结构
import React from 'react';

// 1. Props 接口定义
interface ChatWindowProps {
  sessionId: string | null;
  onSendMessage: (message: string) => void;
}

// 2. 组件实现
export const ChatWindow: React.FC<ChatWindowProps> = ({ 
  sessionId, 
  onSendMessage 
}) => {
  // 3. Hooks
  const [message, setMessage] = useState('');
  
  // 4. 事件处理函数
  const handleSubmit = () => {
    onSendMessage(message);
    setMessage('');
  };
  
  // 5. 渲染
  return (
    <div>
      {/* JSX */}
    </div>
  );
};
```

---

## Props Conventions

- 使用 TypeScript 接口定义 Props
- Props 接口命名：`<ComponentName>Props`
- 必需的 props 不使用 `?`
- 可选的 props 使用 `?`
- 回调函数命名：`on<Event>`（例如：`onSendMessage`）

---

## Styling Patterns

待定（计划使用 CSS Modules 或 Tailwind CSS）

---

## Accessibility

- 使用语义化 HTML 标签
- 添加 ARIA 属性
- 支持键盘导航

---

## Common Mistakes

（待前端开发后补充）
