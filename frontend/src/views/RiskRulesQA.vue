<template>
  <div class="risk-rules-qa">
    <SessionSidebar
      :isOpen="sidebarOpen"
      :currentSessionId="sessionId"
      sceneType="risk_rule"
      @close="sidebarOpen = false"
      @select-session="handleSelectSession"
      @session-created="handleSessionCreated"
      ref="sidebar"
    />

    <header class="header">
      <div class="header-left">
        <button @click="sidebarOpen = true" class="menu-btn">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M2 4h14M2 9h14M2 14h14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
        <router-link to="/" class="back-btn">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M12 4L6 9l6 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </router-link>
        <div class="title-group">
          <h1>风控规则</h1>
          <span class="subtitle">智能检索风控政策与规则</span>
        </div>
      </div>
      <button @click="resetSession" class="new-chat-btn">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M7 2v10M2 7h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        新建会话
      </button>
    </header>

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
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
            <circle cx="32" cy="32" r="30" stroke="currentColor" stroke-width="1" opacity="0.15"/>
            <path d="M20 32h24M32 20v24" stroke="#d4a843" stroke-width="2" stroke-linecap="round" opacity="0.6"/>
          </svg>
        </div>
        <h2>风控规则问答</h2>
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
            <div v-else class="ai-avatar">AI</div>
          </div>
          <div class="message-content">
            <div v-if="msg.role === 'user'" class="user-bubble">
              {{ msg.content }}
            </div>
            <template v-else>
              <AnswerDisplay :answer="msg.answer" />
              <SourceList :sources="msg.sources" :metadata="msg.retrieval_metadata" />
            </template>
          </div>
        </div>
      </TransitionGroup>

      <div v-if="clarificationOptions.length > 0" class="message-wrapper assistant">
        <div class="avatar">
          <div class="ai-avatar">AI</div>
        </div>
        <div class="message-content">
          <ClarificationOptions :options="clarificationOptions" @select="handleClarificationSelect" />
        </div>
      </div>

      <div v-if="loading" class="message-wrapper assistant">
        <div class="avatar">
          <div class="ai-avatar">AI</div>
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
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.2"/>
          <path d="M9 6v3M9 11.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
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
import { queryRiskRules, checkHealth, getSession } from '../services/api.js'
import ChatInput from '../components/ChatInput.vue'
import AnswerDisplay from '../components/AnswerDisplay.vue'
import SourceList from '../components/SourceList.vue'
import ClarificationOptions from '../components/ClarificationOptions.vue'
import SessionSidebar from '../components/SessionSidebar.vue'

const sessionId = ref(null)
const messages = ref([])
const loading = ref(false)
const error = ref(null)
const clarificationOptions = ref([])
const apiConnected = ref(false)
const messagesContainer = ref(null)
const sidebarOpen = ref(false)
const sidebar = ref(null)

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
  messages.value.push({ role: 'user', content: query })
  loading.value = true

  try {
    const result = await queryRiskRules({ query, session_id: sessionId.value })
    sessionId.value = result.session_id
    apiConnected.value = true

    if (result.needs_clarification && result.clarification_options.length > 0) {
      clarificationOptions.value = result.clarification_options
    }

    messages.value.push({
      role: 'assistant',
      answer: result.answer,
      sources: result.sources,
      retrieved_count: result.retrieved_count,
      retrieval_metadata: result.retrieval_metadata
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
    const result = await queryRiskRules({ query: '', session_id: sessionId.value, clarification_choice: selectedOption })
    messages.value.push({
      role: 'assistant',
      answer: result.answer,
      sources: result.sources,
      retrieved_count: result.retrieved_count,
      retrieval_metadata: result.retrieval_metadata
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

const handleSelectSession = async (newSessionId) => {
  if (!newSessionId) return
  sessionId.value = newSessionId
  sidebarOpen.value = false
  messages.value = []
  clarificationOptions.value = []
  try {
    const session = await getSession(newSessionId)
    if (session && session.messages) {
      for (const msg of session.messages) {
        if (msg.role === 'user') {
          messages.value.push({ role: 'user', content: msg.content })
        } else if (msg.role === 'assistant') {
          messages.value.push({ role: 'assistant', answer: msg.content, sources: [], retrieved_count: 0 })
        }
      }
    }
  } catch (e) {
    console.error('加载会话失败:', e)
  }
}

const handleSessionCreated = (newSessionId) => {
  sessionId.value = newSessionId
  sidebarOpen.value = false
  messages.value = []
}
</script>

<style scoped>
.risk-rules-qa {
  max-width: 960px;
  margin: 0 auto;
  padding: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(14, 19, 34, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-subtle);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.back-btn, .menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  color: var(--text-muted);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover, .menu-btn:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.title-group h1 {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.subtitle {
  font-size: 12px;
  color: var(--text-muted);
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  font-family: var(--font-display);
  font-weight: 500;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  border-color: var(--glow);
  color: var(--accent);
  background: var(--accent-dim);
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 8px 24px;
  font-size: 12px;
  border-bottom: 1px solid var(--border-subtle);
  background: rgba(8, 12, 24, 0.5);
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
}

.status-item.connected {
  color: #10b981;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
}

.status-item.connected .status-dot {
  background: #10b981;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.session-label {
  color: var(--text-muted);
}

.session-id {
  font-family: 'SF Mono', 'Fira Code', monospace;
  background: var(--bg-hover);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 28px 24px;
  display: flex;
  flex-direction: column;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.welcome {
  text-align: center;
  padding: 60px 20px;
  animation: fadeIn 0.5s ease;
}

.welcome-icon {
  margin-bottom: 20px;
  opacity: 0.6;
}

.welcome h2 {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 10px;
  letter-spacing: -0.01em;
}

.welcome p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 28px;
}

.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.suggestion-btn {
  padding: 10px 20px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 20px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  font-family: var(--font-body);
  transition: all 0.2s;
}

.suggestion-btn:hover {
  border-color: var(--glow);
  color: var(--accent);
  background: var(--accent-dim);
  transform: translateY(-1px);
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

.user-avatar, .ai-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font-display);
}

.user-avatar {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
}

.ai-avatar {
  background: linear-gradient(135deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 80%, black) 100%);
  color: var(--bg-base);
}

.message-content {
  max-width: 100%;
}

.user-bubble {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  padding: 12px 18px;
  border-radius: 18px 18px 6px 18px;
  font-size: 15px;
  line-height: 1.5;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.2);
}

.loading-bubble {
  background: var(--bg-card);
  padding: 16px 24px;
  border-radius: 18px 18px 18px 4px;
  border: 1px solid var(--border-subtle);
}

.loading-dots {
  display: flex;
  gap: 5px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
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

.message-enter-active {
  animation: slideIn 0.3s ease;
}
.message-leave-active {
  animation: slideOut 0.2s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideOut {
  from { opacity: 1; transform: translateY(0); }
  to { opacity: 0; transform: translateY(-10px); }
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 10px;
  color: #ef4444;
  font-size: 13px;
  animation: shake 0.4s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

.input-area {
  padding: 16px 24px 20px;
  background: rgba(14, 19, 34, 0.8);
  backdrop-filter: blur(20px);
  border-top: 1px solid var(--border-subtle);
}
</style>
