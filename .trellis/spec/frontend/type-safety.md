# Type Safety

> Data-shape safety patterns in this project.

---

## Overview

The current frontend is JavaScript, not TypeScript. Runtime data contracts are
primarily enforced by backend Pydantic schemas and service-level validation.

Frontend code should still read optional response fields defensively.

---

## API Contract Handling

- Keep API response parsing in `frontend/src/services/api.js`.
- Components should handle missing arrays with `|| []`.
- Components should handle missing objects with `|| null`.
- Numeric formatting helpers should return the original value when the value is not a number.

Example:

```js
messages.value[msgIndex].tool_calls = data.tool_calls || []
messages.value[msgIndex].tool_intent = data.tool_intent || null
```

---

## Business Tool Fields

For business tools, the backend contract is documented in
`docs/BUSINESS_TOOLS.md`.

Frontend display should treat these fields as optional:

- `tool_calls`
- `tool_intent`
- `retrieval_metadata`
- `result.chain`

---

## Common Mistakes

- Do not assume SSE events arrive with every optional field populated.
- Do not call `.map` or `.length` on fields before confirming they are arrays.
- Do not duplicate backend validation in the frontend; show safe fallbacks instead.
