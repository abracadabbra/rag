# 重构前端 UI — 深色金融风

## Goal

将现有前端界面从泛用 Ant Design 风格重构为深色金融风 + 科技感的设计语言，覆盖全局主题、首页、对话页和核心组件。

## 设计方向

- **色调**: 深色背景 (#0a0e1a 级) + 金色/蓝绿点缀
- **科技感**: 细微发光效果、玻璃拟态元素、动态粒子/网格背景
- **字体**: 展示用字体 + 易读正文
- **质感**: 不刺眼、稳重、专业

## 涉及文件

- `frontend/src/App.vue` — 全局样式/CSS 变量
- `frontend/src/views/Home.vue` — 首页重构
- `frontend/src/views/RiskRulesQA.vue` — 对话页重构（其他 QA 页同理）
- `frontend/src/components/ChatInput.vue` — 暗色适配
- `frontend/src/components/AnswerDisplay.vue` — 暗色适配
- `frontend/src/components/SourceList.vue` — 暗色适配
- `frontend/src/components/SessionSidebar.vue` — 暗色适配
- `frontend/src/components/ClarificationOptions.vue` — 暗色适配
- `frontend/src/views/ApiSettings.vue` — 暗色适配

## Open Questions

1. 你那里有可用的展示字体吗（比如 Noto Serif SC 或类似中文字体）？还是直接用系统字体 + 英文特色字体？
2. 对话页的 4 个场景（风控/模型/仿真/毛利）是否需要各自不同的主题色？还是统一深色风格？
