# Component Guidelines

> How components are built in this project.

---

## Overview

Frontend components are Vue 3 single-file components using `<script setup>`.

---

## Component Structure

```vue
<template>
  <section class="example-panel">
    <button @click="handleSubmit">提交</button>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['submit'])
const value = ref('')

const handleSubmit = () => {
  if (props.disabled) return
  emit('submit', value.value)
}
</script>

<style scoped>
.example-panel {
  border: 1px solid var(--border-subtle);
}
</style>
```

---

## Props And Events

- Define props with `defineProps`.
- Define events with `defineEmits`.
- Name handlers as `handle<Event>`.
- Keep scene-specific display text in the scene view props when possible.
- Keep shared chat behavior in `QAView.vue`.

---

## Styling

- Use scoped CSS in components.
- Reuse global variables from `App.vue` such as `--bg-card`, `--text-primary`, and `--accent`.
- Keep cards at modest radius unless matching an existing component.
- For scene colors, prefer the existing scene variables instead of hard-coding a new palette.

---

## Accessibility

- Use semantic buttons, forms, and inputs.
- Add `aria-label` when an input has no visible label.
- Preserve keyboard submit behavior for chat and clarification forms.

---

## Common Mistakes

- Do not duplicate the full QA flow in each scene view.
- Do not add component-local API clients; use `frontend/src/services/api.js`.
- Do not assume every clarification is an option list; order-level tool clarification can require typed input.
