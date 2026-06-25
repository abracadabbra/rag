# Quality Guidelines

> Code quality standards for frontend development.

---

## Overview

The frontend currently has a Vite build check but no dedicated lint, typecheck,
or unit-test command.

Required verification for frontend changes:

```bash
cd frontend && npm run build
```

---

## Required Patterns

- Keep shared API behavior in `frontend/src/services/api.js`.
- Keep repeated scene QA behavior in `QAView.vue`.
- Use Vue refs/computed values for local state.
- Use scoped CSS for component-specific styles.
- Preserve existing scene theme variables and dark financial UI style.

---

## Forbidden Patterns

- Do not duplicate `querySceneStream` parsing in components.
- Do not add dependencies unless the task requires them and the user approves.
- Do not hard-code a backend host in components; use the existing `/api/v1` service base.
- Do not expose raw backend exception details in the UI.

---

## Testing Requirements

- Backend/API field changes that affect frontend rendering need matching backend tests.
- Frontend-only visual or interaction changes must at least pass `npm run build`.
- For SSE changes, verify `sources`, `chunk`, `clarification`, `done`, and `error` handling stays compatible.

---

## Code Review Checklist

- [ ] `cd frontend && npm run build` passes.
- [ ] No unused imports.
- [ ] Text fits in compact controls on desktop and mobile widths.
- [ ] Pending/loading/error states are handled.
- [ ] Cross-layer response fields match backend schemas and docs.
