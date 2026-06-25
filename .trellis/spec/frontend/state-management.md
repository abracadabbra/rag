# State Management

> How state is managed in this project.

---

## Overview

The current frontend uses Vue local component state. There is no global store.

---

## State Categories

- Local UI state: `ref` / `computed` in Vue components.
- Server state: loaded through `frontend/src/services/api.js`.
- Route state: Vue Router in `frontend/src/main.js`.
- Session state: backend session id stored in the active QA component.

---

## Scene QA State

`QAView.vue` owns the active scene conversation state:

- `sessionId`
- `messages`
- `loading`
- `error`
- clarification state
- sidebar open/close state

Scene views should pass configuration props into `QAView` instead of owning chat state.

---

## Business Tool State

Tool data is display state, not a separate frontend source of truth.

- Backend sends `tool_calls` and `tool_intent`.
- `QAView.vue` stores those fields on assistant messages.
- Missing-field clarification keeps temporary input state only until the user submits it.
- Restored session history must read `tool_calls` and `tool_intent` from each
  assistant message's own `metadata`; do not infer historical tool cards from
  session-level metadata.

---

## Common Mistakes

- Do not create a global store for one scene unless multiple unrelated components need the same state.
- Do not infer tool execution client-side; render backend `tool_intent` and `tool_calls`.
- Clear pending clarification state when sending a new query, resetting the session, or switching sessions.
