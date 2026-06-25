# Frontend Directory Structure

> How frontend code is organized in this project.

---

## Overview

The frontend is a Vue 3 single-page application built with Vite.

- Framework: Vue 3 with `<script setup>`
- Router: Vue Router 4
- API client: native `fetch` in `frontend/src/services/api.js`
- Styling: Vue single-file components with scoped CSS plus global CSS variables in `App.vue`
- Build check: `cd frontend && npm run build`

---

## Directory Layout

```text
frontend/
├── src/
│   ├── main.js               # App bootstrap and router setup
│   ├── App.vue               # Root shell, global theme variables
│   ├── components/           # Reusable Vue components
│   ├── services/
│   │   └── api.js            # REST/SSE API client
│   └── views/                # Route-level views
├── index.html
├── package.json
└── vite.config.js
```

---

## Module Organization

### Components

Reusable UI belongs in `frontend/src/components/`.

- Use one `.vue` single-file component per component.
- Use PascalCase file names such as `QAView.vue`.
- Prefer local component state with Vue refs/computed values.
- Keep repeated scene behavior in shared components such as `QAView.vue`.

### Views

Route-level pages belong in `frontend/src/views/`.

- Scene views should stay thin and pass scene-specific props into `QAView`.
- Avoid duplicating full chat logic across scene views.

### Services

API calls belong in `frontend/src/services/api.js`.

- Keep route mapping and SSE parsing centralized.
- Do not duplicate `fetch` logic in components.
- When backend response fields change, update the service parser and affected components together.

---

## Naming Conventions

- Components: `PascalCase.vue`
- Views: `PascalCase.vue`
- Services/helpers: `camelCase.js`
- Template event handlers: `handle<Event>` in `<script setup>`

---

## Current API Flow

For scene chat:

```text
QAView.vue -> querySceneStream(sceneType, params, callbacks) -> /api/v1/<scene>/query-stream
```

SSE events currently handled by the frontend:

- `sources`: sources, retrieval metadata, `tool_calls`, `tool_intent`
- `chunk`: streamed answer text
- `clarification`: missing information prompt, options, optional `tool_intent`
- `done`: final session id
- `error`: user-facing error message
