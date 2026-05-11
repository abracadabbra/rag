<template>
  <div class="answer-display">
    <div class="answer-header">
      <span class="answer-label">AI 回答</span>
    </div>
    <div class="answer-content" v-html="renderedAnswer"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  answer: {
    type: String,
    required: true
  }
})

const renderedAnswer = computed(() => {
  return marked.parse(props.answer)
})
</script>

<style scoped>
.answer-display {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.answer-header {
  margin-bottom: 12px;
}

.answer-label {
  font-weight: 600;
  color: #333;
}

.answer-content {
  line-height: 1.6;
  color: #444;
}

.answer-content :deep(p) {
  margin: 0 0 12px 0;
}

.answer-content :deep(p:last-child) {
  margin-bottom: 0;
}

.answer-content :deep(code) {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.answer-content :deep(ul),
.answer-content :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}
</style>
