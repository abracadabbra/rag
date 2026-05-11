<template>
  <div class="chat-input">
    <textarea
      v-model="inputText"
      @keydown.enter.exact.prevent="handleSend"
      placeholder="请输入您的问题... (按 Enter 发送)"
      :disabled="disabled"
      rows="3"
    ></textarea>
    <button
      @click="handleSend"
      :disabled="disabled || !inputText.trim()"
      class="send-btn"
    >
      {{ disabled ? '发送中...' : '发送' }}
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
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.chat-input textarea {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  resize: none;
  font-family: inherit;
}

.chat-input textarea:focus {
  outline: none;
  border-color: #1890ff;
}

.chat-input textarea:disabled {
  background: #f0f0f0;
  cursor: not-allowed;
}

.send-btn {
  padding: 8px 24px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  align-self: flex-end;
}

.send-btn:hover:not(:disabled) {
  background: #40a9ff;
}

.send-btn:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}
</style>
