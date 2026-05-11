<template>
  <div class="answer-display">
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

marked.setOptions({
  breaks: true,
  gfm: true
})

const renderedAnswer = computed(() => {
  return marked.parse(props.answer)
})
</script>

<style scoped>
.answer-display {
  background: white;
  border-radius: 18px 18px 18px 4px;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.answer-content {
  line-height: 1.7;
  color: #333;
  font-size: 15px;
}

.answer-content :deep(p) {
  margin: 0 0 12px 0;
}

.answer-content :deep(p:last-child) {
  margin-bottom: 0;
}

.answer-content :deep(h1),
.answer-content :deep(h2),
.answer-content :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  margin: 16px 0 8px 0;
  color: #1a1a1a;
}

.answer-content :deep(h1:first-child),
.answer-content :deep(h2:first-child),
.answer-content :deep(h3:first-child) {
  margin-top: 0;
}

.answer-content :deep(code) {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 13px;
  color: #e83e8c;
}

.answer-content :deep(pre) {
  background: #f5f5f5;
  padding: 12px 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.answer-content :deep(pre code) {
  background: none;
  padding: 0;
  color: #333;
}

.answer-content :deep(ul),
.answer-content :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.answer-content :deep(li) {
  margin: 4px 0;
}

.answer-content :deep(strong) {
  color: #1a1a1a;
  font-weight: 600;
}

.answer-content :deep(blockquote) {
  border-left: 3px solid #1890ff;
  margin: 12px 0;
  padding: 8px 16px;
  background: #f0f7ff;
  border-radius: 0 8px 8px 0;
}
</style>
