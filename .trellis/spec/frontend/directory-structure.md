# Frontend Directory Structure

> How frontend code is organized in this project.

---

## Overview

**注意**：本项目目前没有前端代码，以下是规划的前端架构。

计划使用：
- **框架**：React 18+ with TypeScript
- **构建工具**：Vite
- **状态管理**：React Context + Hooks
- **UI 库**：待定（Ant Design / Material-UI）
- **HTTP 客户端**：Axios

---

## Directory Layout

```
frontend/
├── src/
│   ├── main.tsx              # 应用入口
│   ├── App.tsx               # 根组件
│   ├── components/           # 可复用组件
│   │   ├── common/           # 通用组件（Button, Input）
│   │   ├── chat/             # 聊天相关组件
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageList.tsx
│   │   │   └── InputBox.tsx
│   │   └── layout/           # 布局组件
│   │       ├── Header.tsx
│   │       └── Sidebar.tsx
│   ├── pages/                # 页面组件
│   │   ├── RiskRulePage.tsx  # 风控规则页面
│   │   ├── ModelCardPage.tsx # 模型卡片页面
│   │   └── HomePage.tsx      # 首页
│   ├── hooks/                # 自定义 Hooks
│   │   ├── useChat.ts        # 聊天逻辑
│   │   ├── useSession.ts     # 会话管理
│   │   └── useQuery.ts       # 查询逻辑
│   ├── services/             # API 服务
│   │   ├── api.ts            # API 客户端配置
│   │   ├── riskRuleService.ts
│   │   └── sessionService.ts
│   ├── types/                # TypeScript 类型定义
│   │   ├── api.ts            # API 类型
│   │   └── models.ts         # 数据模型
│   ├── utils/                # 工具函数
│   │   ├── format.ts         # 格式化函数
│   │   └── validation.ts     # 验证函数
│   ├── contexts/             # React Context
│   │   └── SessionContext.tsx
│   └── styles/               # 样式文件
│       └── global.css
├── public/                   # 静态资源
├── index.html                # HTML 模板
├── vite.config.ts            # Vite 配置
├── tsconfig.json             # TypeScript 配置
└── package.json              # 依赖管理
```

---

## Module Organization

### 1. Components（组件）

**职责**：可复用的 UI 组件

- **common/** - 通用组件（按钮、输入框、卡片）
- **chat/** - 聊天相关组件
- **layout/** - 布局组件（头部、侧边栏）

**规范**：
- 每个组件一个文件夹（如果有样式和测试）
- 组件名使用 PascalCase
- Props 使用 TypeScript 接口定义

### 2. Pages（页面）

**职责**：路由对应的页面组件

- 每个页面对应一个路由
- 页面组件组合多个 components
- 页面组件处理数据获取和状态管理

### 3. Hooks（自定义 Hooks）

**职责**：封装可复用的逻辑

- 命名以 `use` 开头
- 封装 API 调用、状态管理、副作用

### 4. Services（API 服务）

**职责**：封装 API 调用

- 每个业务场景一个 service 文件
- 使用 Axios 发起请求
- 统一的错误处理

---

## Naming Conventions

### 文件命名

- **组件文件**：`PascalCase.tsx`（例如：`ChatWindow.tsx`）
- **Hook 文件**：`camelCase.ts`（例如：`useChat.ts`）
- **Service 文件**：`camelCase.ts`（例如：`riskRuleService.ts`）
- **工具文件**：`camelCase.ts`（例如：`format.ts`）

### 组件命名

- **组件名**：PascalCase（例如：`ChatWindow`）
- **Props 接口**：`<ComponentName>Props`（例如：`ChatWindowProps`）

---

## Examples

### 组件示例（待实现）

```tsx
// src/components/chat/ChatWindow.tsx
interface ChatWindowProps {
  sessionId: string | null;
  onSendMessage: (message: string) => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ 
  sessionId, 
  onSendMessage 
}) => {
  // 组件实现
  return <div>...</div>;
};
```

### Hook 示例（待实现）

```tsx
// src/hooks/useChat.ts
export const useChat = (sceneType: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  
  const sendMessage = async (query: string) => {
    // 发送消息逻辑
  };
  
  return { messages, loading, sendMessage };
};
```

### Service 示例（待实现）

```tsx
// src/services/riskRuleService.ts
import axios from 'axios';

export const queryRiskRules = async (query: string) => {
  const response = await axios.post('/api/v1/risk-rules/query', {
    query,
    top_k: 5,
    score_threshold: 0.7
  });
  return response.data;
};
```
