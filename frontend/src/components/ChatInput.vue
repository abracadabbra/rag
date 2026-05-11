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
      <svg v-if="!disabled" width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
        <path d="M2 18L20 10L2 2V8L14 10L2 12V18Z"/>
      </svg>
      <svg v-else width="20" height="20" viewBox="0 0 20 20" fill="currentColor" class="spin">
        <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm0 14a6 6 0 110-12 6 6 0 010 12z"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  }
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
  padding: 14px 16px;
  border: 1px solid #e8e8e8;
  border-radius: 24px;
  font-size: 15px;
  resize: none;
  font-family: inherit;
  background: #f5f7fa;
  transition: all 0.2s;
}

.chat-input textarea:focus {
  outline: none;
  border-color: #1890ff;
  background: white;
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.1);
}

.chat-input textarea:disabled {
  background: #f0f0f0;
  cursor: not-allowed;
}

.chat-input textarea::placeholder {
  color: #bfbfbf;
}

.send-btn {
  width: 48px;
  height: 48px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: #40a9ff;
  transform: scale(1.05);
}

.send-btn:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}

.send-btn:disabled svg {
  opacity: 0.5;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
