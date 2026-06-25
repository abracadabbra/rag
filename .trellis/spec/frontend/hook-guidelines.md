# Hook Guidelines

> How reusable composition logic is used in this project.

---

## Overview

This is a Vue project. React hooks are not used.

The current codebase does not have a `src/composables/` directory. Add one only
when multiple components need to share the same stateful Vue composition logic.

---

## Vue Composable Pattern

If a composable becomes necessary:

```js
// frontend/src/composables/useExample.js
import { ref } from 'vue'

export function useExample() {
  const loading = ref(false)

  const run = async () => {
    loading.value = true
    try {
      // shared async logic
    } finally {
      loading.value = false
    }
  }

  return { loading, run }
}
```

---

## When To Extract

Extract a composable when:

- The same stateful logic appears in two or more components.
- The logic is independent of one component's template.
- The extraction reduces duplicated API/error/loading handling.

Keep logic local when it is used by only one component.

---

## Common Mistakes

- Do not create React-style hooks.
- Do not extract a composable just to move code out of a component.
- Do not duplicate API clients inside composables; call `frontend/src/services/api.js`.
