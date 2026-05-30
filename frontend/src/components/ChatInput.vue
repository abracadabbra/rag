<template>
  <div class="chat-input">
    <textarea
      v-model="inputText"
      @keydown.enter.exact.prevent="handleSend"
      placeholder="输入您的问题，按 Enter 发送..."
      :disabled="disabled"
      rows="1"
    ></textarea>
    <button
      @click="handleSend"
      :disabled="disabled || !inputText.trim()"
      class="send-btn"
    >
      <svg v-if="!disabled" width="18" height="18" viewBox="0 0 18 18" fill="none">
        <path d="M2 16L16 9L2 2v6l10 1L2 10v6z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
      </svg>
      <svg v-else width="18" height="18" viewBox="0 0 18 18" fill="none" class="spin">
        <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="2" opacity="0.3"/>
        <path d="M16 9a7 7 0 00-7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['send'])
const inputText = ref('')

const handleSend = () => {
  const text = inputText.value.trim()
  if (!text || props.disabled) return
  emit('send', text)
  inputText.value = ''
}
</script>

<style scoped>
.chat-input {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chat-input textarea {
  flex: 1;
  padding: 14px 18px;
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  font-size: 15px;
  resize: none;
  font-family: var(--font-body);
  background: var(--bg-surface);
  color: var(--text-primary);
  transition: all 0.2s;
  line-height: 1.5;
}

.chat-input textarea:focus {
  outline: none;
  border-color: var(--accent);
  background: var(--bg-card);
  box-shadow: 0 0 0 3px var(--glow);
}

.chat-input textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-input textarea::placeholder {
  color: var(--text-muted);
}

.send-btn {
  width: 48px;
  height: 48px;
  background: var(--accent);
  color: var(--bg-base);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  filter: brightness(1.15);
  transform: scale(1.04);
  box-shadow: 0 4px 16px var(--glow);
}

.send-btn:active:not(:disabled) {
  transform: scale(0.96);
}

.send-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
