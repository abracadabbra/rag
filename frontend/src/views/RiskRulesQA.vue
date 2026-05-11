<template>
  <div class="risk-rules-qa">
    <div class="header">
      <h1>风控规则问答</h1>
      <button @click="resetSession" class="new-chat-btn">新建会话</button>
    </div>

    <div class="session-info">
      <span class="session-id">会话ID: {{ sessionId || '无' }}</span>
    </div>

    <div class="messages">
      <!-- User messages -->
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="message-wrapper"
        :class="msg.role"
      >
        <div class="message-content">
          <div v-if="msg.role === 'user'" class="user-question">
            <span class="role-label">问题</span>
            <p>{{ msg.content }}</p>
          </div>

          <template v-else>
            <AnswerDisplay :answer="msg.answer" />
            <SourceList :sources="msg.sources" />
          </template>
        </div>
      </div>

      <!-- Clarification options -->
      <div v-if="clarificationOptions.length > 0" class="message-wrapper assistant">
        <ClarificationOptions
          :options="clarificationOptions"
          @select="handleClarificationSelect"
        />
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="loading">
        <span>AI 正在思考...</span>
      </div>

      <!-- Error state -->
      <div v-if="error" class="error">
        <span class="error-icon">!</span>
        <span>{{ error }}</span>
      </div>
    </div>

    <ChatInput :disabled="loading" @send="handleSend" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { queryRiskRules, checkHealth } from '../services/api.js'
import ChatInput from '../components/ChatInput.vue'
import AnswerDisplay from '../components/AnswerDisplay.vue'
import SourceList from '../components/SourceList.vue'
import ClarificationOptions from '../components/ClarificationOptions.vue'

const sessionId = ref(null)
const messages = ref([])
const loading = ref(false)
const error = ref(null)
const clarificationOptions = ref([])

onMounted(async () => {
  try {
    await checkHealth()
  } catch (e) {
    error.value = '无法连接到 API 服务，请确保后端已启动'
  }
})

const handleSend = async (query) => {
  if (loading.value) return

  error.value = null
  clarificationOptions.value = []

  // Add user message
  messages.value.push({
    role: 'user',
    content: query
  })

  loading.value = true

  try {
    const result = await queryRiskRules({
      query,
      session_id: sessionId.value
    })

    // Update session ID
    sessionId.value = result.session_id

    // Check if needs clarification
    if (result.needs_clarification && result.clarification_options.length > 0) {
      clarificationOptions.value = result.clarification_options
    }

    // Add assistant response
    messages.value.push({
      role: 'assistant',
      answer: result.answer,
      sources: result.sources,
      retrieved_count: result.retrieved_count
    })
  } catch (e) {
    error.value = e.message || '查询失败，请稍后重试'
    // Remove user message on error
    messages.value.pop()
  } finally {
    loading.value = false
  }
}

const handleClarificationSelect = async (selectedOption) => {
  if (!clarificationOptions.value.length) return

  clarificationOptions.value = []

  try {
    const result = await queryRiskRules({
      query: '',
      session_id: sessionId.value,
      clarification_choice: selectedOption
    })

    // Add clarification response
    messages.value.push({
      role: 'assistant',
      answer: result.answer,
      sources: result.sources,
      retrieved_count: result.retrieved_count
    })
  } catch (e) {
    error.value = e.message || '查询失败，请稍后重试'
  }
}

const resetSession = () => {
  sessionId.value = null
  messages.value = []
  error.value = null
  clarificationOptions.value = []
}
</script>

<style scoped>
.risk-rules-qa {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header h1 {
  font-size: 24px;
  color: #333;
  margin: 0;
}

.new-chat-btn {
  padding: 8px 16px;
  background: white;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.new-chat-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.session-info {
  margin-bottom: 16px;
}

.session-id {
  font-size: 13px;
  color: #888;
}

.messages {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
}

.message-wrapper {
  display: flex;
}

.message-wrapper.user {
  justify-content: flex-end;
}

.message-wrapper.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 85%;
}

.user-question {
  background: #1890ff;
  color: white;
  padding: 12px 16px;
  border-radius: 12px 12px 4px 12px;
}

.user-question .role-label {
  font-size: 12px;
  opacity: 0.8;
  display: block;
  margin-bottom: 4px;
}

.user-question p {
  margin: 0;
  line-height: 1.5;
}

.loading {
  padding: 16px;
  text-align: center;
  color: #888;
}

.error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 6px;
  color: #ff4d4f;
}

.error-icon {
  width: 20px;
  height: 20px;
  background: #ff4d4f;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}
</style>
