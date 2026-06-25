<template>
  <div class="answer-display">
    <div class="answer-content" v-html="renderedAnswer"></div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  answer: { type: String, required: true },
  streaming: { type: Boolean, default: true }
})

const displayedText = ref('')
const isTyping = ref(false)
const isStreaming = ref(false)

marked.setOptions({ breaks: true, gfm: true })

const renderedAnswer = computed(() => {
  return marked.parse(displayedText.value)
})

const startTypewriter = (text) => {
  if (!props.streaming || isStreaming.value) {
    displayedText.value = text
    return
  }
  displayedText.value = ''
  isTyping.value = true
  let index = 0
  const speed = 20
  const type = () => {
    if (index < text.length) {
      displayedText.value = text.substring(0, index + 1)
      index++
      setTimeout(type, speed)
    } else {
      isTyping.value = false
    }
  }
  type()
}

watch(() => props.answer, (newAnswer, oldAnswer) => {
  // Real streaming: text is being appended character by character
  if (newAnswer && oldAnswer && newAnswer.startsWith(oldAnswer) && newAnswer.length > oldAnswer.length) {
    isStreaming.value = true
    displayedText.value = newAnswer
    return
  }
  // New answer arrived (not streaming) — use typewriter
  if (!isStreaming.value) {
    startTypewriter(newAnswer)
  } else {
    displayedText.value = newAnswer
    isStreaming.value = false
  }
}, { immediate: true })

defineExpose({ isTyping })
</script>

<style scoped>
.answer-display {
  background: var(--bg-card);
  border-radius: 16px 16px 16px 4px;
  padding: 18px 22px;
  border: 1px solid var(--border-subtle);
}

.answer-content {
  line-height: 1.7;
  color: var(--text-primary);
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
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  margin: 16px 0 8px 0;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.answer-content :deep(h1:first-child),
.answer-content :deep(h2:first-child),
.answer-content :deep(h3:first-child) {
  margin-top: 0;
}

.answer-content :deep(code) {
  background: var(--bg-elevated);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 13px;
  color: #f0d080;
}

.answer-content :deep(pre) {
  background: var(--bg-elevated);
  padding: 16px 20px;
  border-radius: 10px;
  overflow-x: auto;
  margin: 12px 0;
  border: 1px solid var(--border-subtle);
  position: relative;
}

.answer-content :deep(pre)::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--accent);
  opacity: 0.4;
}

.answer-content :deep(pre code) {
  background: none;
  padding: 0;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.6;
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
  color: var(--text-primary);
  font-weight: 600;
}

.answer-content :deep(blockquote) {
  border-left: 3px solid var(--accent);
  margin: 12px 0;
  padding: 8px 16px;
  background: var(--accent-dim);
  border-radius: 0 8px 8px 0;
  color: var(--text-secondary);
}
</style>
