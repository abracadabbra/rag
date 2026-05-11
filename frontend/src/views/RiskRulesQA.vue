<template>
  <div class="risk-rules-qa">
    <div class="header">
      <div class="header-left">
        <router-link to="/" class="back-btn">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"/>
          </svg>
        </router-link>
        <div class="logo">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="#1890ff"/>
            <path d="M8 16h16M16 8v16" stroke="white" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="title-group">
          <h1>风控规则问答</h1>
          <span class="subtitle">智能检索风控政策与规则</span>
        </div>
      </div>
      <button @click="resetSession" class="new-chat-btn">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        新建会话
      </button>
    </div>

    <div class="status-bar">
      <div class="status-item" :class="{ connected: apiConnected }">
        <span class="status-dot"></span>
        <span>{{ apiConnected ? '后端已连接' : '后端未连接' }}</span>
      </div>
      <div v-if="sessionId" class="status-item">
        <span class="session-label">会话ID:</span>
        <span class="session-id">{{ sessionId.substring(0, 8) }}...</span>
      </div>
    </div>

    <div class="messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="welcome">
        <div class="welcome-icon">
          <svg width="72" height="72" viewBox="0 0 72 72" fill="none">
            <circle cx="36" cy="36" r="34" stroke="#e8e8e8" stroke-width="2"/>
            <path d="M22 36h28M36 22v28" stroke="#1890ff" stroke-width="3" stroke-linecap="round"/>
          </svg>
        </div>
        <h2>欢迎使用风控规则问答</h2>
        <p>我可以帮您查询风控政策、制度与各类规则信息</p>
        <div class="suggestions">
          <button v-for="q in suggestions" :key="q" @click="handleSend(q)" class="suggestion-btn">
            {{ q }}
          </button>
        </div>
      </div>

      <TransitionGroup name="message" tag="div" class="messages-list">
        <div v-for="(msg, index) in messages" :key="index" class="message-wrapper" :class="msg.role">
          <div class="avatar">
            <div v-if="msg.role === 'user'" class="user-avatar">U</div>
            <div v-else class="ai-avatar">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="white">
                <path d="M10 2L3 7v11h14V7l-7-5zm0 2.5L14.5 7H5.5L10 4.5z"/>
              </svg>
            </div>
          </div>
          <div class="message-content">
            <div v-if="msg.role === 'user'" class="user-bubble">
              {{ msg.content }}
            </div>
            <template v-else>
              <AnswerDisplay :answer="msg.answer" />
              <SourceList :sources="msg.sources" />
            </template>
          </div>
        </div>
      </TransitionGroup>

      <div v-if="clarificationOptions.length > 0" class="message-wrapper assistant">
        <div class="avatar">
          <div class="ai-avatar">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="white">
              <path d="M10 2L3 7v11h14V7l-7-5zm0 2.5L14.5 7H5.5L10 4.5z"/>
            </svg>
          </div>
        </div>
        <div class="message-content">
          <ClarificationOptions :options="clarificationOptions" @select="handleClarificationSelect" />
        </div>
      </div>

      <div v-if="loading" class="message-wrapper assistant">
        <div class="avatar">
          <div class="ai-avatar">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="white">
              <path d="M10 2L3 7v11h14V7l-7-5zm0 2.5L14.5 7H5.5L10 4.5z"/>
            </svg>
          </div>
        </div>
        <div class="message-content">
          <div class="loading-bubble">
            <div class="loading-dots">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="error" class="error-banner">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10 0C4.48 0 0 4.48 0 10s4.48 10 10 10 10-4.48 10-10S15.52 0 10 0zm1 15H9v-2h2v2zm0-4H9V5h2v6z"/>
        </svg>
        <span>{{ error }}</span>
      </div>
    </div>

    <div class="input-area">
      <ChatInput :disabled="loading" @send="handleSend" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
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
const apiConnected = ref(false)
const messagesContainer = ref(null)

const suggestions = [
  '白金卡的单笔交易限额是多少？',
  '信用卡取现的手续费怎么计算？',
  '哪些情况下交易会被风控拦截？',
]

onMounted(async () => {
  try {
    await checkHealth()
    apiConnected.value = true
  } catch {
    apiConnected.value = false
    error.value = '无法连接到 API 服务，请确保后端已启动'
  }
})

watch(messages, () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
})

const handleSend = async (query) => {
  if (loading.value) return

  error.value = null
  clarificationOptions.value = []

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

    sessionId.value = result.session_id
    apiConnected.value = true

    if (result.needs_clarification && result.clarification_options.length > 0) {
      clarificationOptions.value = result.clarification_options
    }

    messages.value.push({
      role: 'assistant',
      answer: result.answer,
      sources: result.sources,
      retrieved_count: result.retrieved_count
    })
  } catch (e) {
    error.value = e.message || '查询失败，请稍后重试'
    apiConnected.value = false
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
  max-width: 1000px;
  margin: 0 auto;
  padding: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 32px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  color: #666;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f5f5f5;
  color: #333;
}

.logo {
  flex-shrink: 0;
}

.title-group h1 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.subtitle {
  font-size: 13px;
  color: #8c8c8c;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 12px 32px;
  background: rgba(255, 255, 255, 0.5);
  font-size: 13px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #8c8c8c;
}

.status-item.connected {
  color: #52c41a;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d9d9d9;
}

.status-item.connected .status-dot {
  background: #52c41a;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.session-label {
  color: #8c8c8c;
}

.session-id {
  font-family: monospace;
  background: #f5f5f5;
  padding: 2px 8px;
  border-radius: 4px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
  display: flex;
  flex-direction: column;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.welcome {
  text-align: center;
  padding: 80px 20px;
  animation: fadeIn 0.5s ease;
}

.welcome-icon {
  margin-bottom: 24px;
}

.welcome h2 {
  font-size: 24px;
  color: #1a1a1a;
  margin: 0 0 12px 0;
}

.welcome p {
  font-size: 15px;
  color: #666;
  margin: 0 0 32px 0;
}

.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.suggestion-btn {
  padding: 12px 24px;
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 24px;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
}

.suggestion-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
  transform: translateY(-2px);
}

.message-wrapper {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.message-wrapper.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.avatar {
  flex-shrink: 0;
}

.user-avatar,
.ai-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.user-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.ai-avatar {
  background: linear-gradient(135deg, #1890ff 0%, #0050b3 100%);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.message-content {
  max-width: 100%;
}

.user-bubble {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 14px 18px;
  border-radius: 20px 20px 6px 20px;
  font-size: 15px;
  line-height: 1.5;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.loading-bubble {
  background: white;
  padding: 18px 28px;
  border-radius: 20px 20px 20px 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #1890ff;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 消息过渡动画 */
.message-enter-active {
  animation: slideIn 0.3s ease;
}

.message-leave-active {
  animation: slideOut 0.2s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideOut {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-10px);
  }
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 18px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 12px;
  color: #ff4d4f;
  font-size: 14px;
  animation: shake 0.5s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

.input-area {
  padding: 20px 32px 28px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}
</style>
