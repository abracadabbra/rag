<template>
  <div class="profit-qa">
    <div class="header">
      <div class="header-left">
        <div class="logo">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="#52c41a"/>
            <path d="M16 8v16M11 13l5-5 5 5M11 19l5 5 5-5" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="title-group">
          <h1>毛利抽成查询</h1>
          <span class="subtitle">查询分成比例、结算规则、收益分析</span>
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
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
            <circle cx="32" cy="32" r="30" stroke="#e8e8e8" stroke-width="2"/>
            <path d="M32 16v32M22 26l10-10 10 10M22 38l10 10 10-10" stroke="#52c41a" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h2>欢迎使用毛利抽成查询系统</h2>
        <p>查询分成比例、结算规则、收益分析等</p>
        <div class="suggestions">
          <button v-for="q in suggestions" :key="q" @click="handleSend(q)" class="suggestion-btn">
            {{ q }}
          </button>
        </div>
      </div>

      <div v-for="(msg, index) in messages" :key="index" class="message-wrapper" :class="msg.role">
        <div class="avatar">
          <div v-if="msg.role === 'user'" class="user-avatar">U</div>
          <div v-else class="ai-avatar ai-green">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="white">
              <path d="M10 4v12M5 9l5-5 5 5M5 11l5 5 5-5" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>
        <div class="message-content">
          <div v-if="msg.role === 'user'" class="user-bubble">{{ msg.content }}</div>
          <template v-else>
            <AnswerDisplay :answer="msg.answer" />
            <SourceList :sources="msg.sources" />
          </template>
        </div>
      </div>

      <div v-if="clarificationOptions.length > 0" class="message-wrapper assistant">
        <div class="avatar">
          <div class="ai-avatar ai-green">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="white">
              <path d="M10 4v12M5 9l5-5 5 5M5 11l5 5 5-5" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>
        <div class="message-content">
          <ClarificationOptions :options="clarificationOptions" @select="handleClarificationSelect" />
        </div>
      </div>

      <div v-if="loading" class="message-wrapper assistant">
        <div class="avatar">
          <div class="ai-avatar ai-green">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="white">
              <path d="M10 4v12M5 9l5-5 5 5M5 11l5 5 5-5" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>
        <div class="message-content">
          <div class="loading-bubble"><div class="loading-dots"><span></span><span></span><span></span></div></div>
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
import { queryProfit, checkHealth } from '../services/api.js'
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
  '本月毛利分成比例是多少？',
  '渠道 A 的抽成规则是什么？',
  '结算周期是什么时候？',
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
    if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  })
})

const handleSend = async (query) => {
  if (loading.value) return
  error.value = null
  clarificationOptions.value = []
  messages.value.push({ role: 'user', content: query })
  loading.value = true
  try {
    const result = await queryProfit({ query, session_id: sessionId.value })
    sessionId.value = result.session_id
    if (result.needs_clarification && result.clarification_options.length > 0) {
      clarificationOptions.value = result.clarification_options
    }
    messages.value.push({ role: 'assistant', answer: result.answer, sources: result.sources })
  } catch (e) {
    error.value = e.message || '查询失败'
    messages.value.pop()
  } finally {
    loading.value = false
  }
}

const handleClarificationSelect = async (option) => {
  if (!clarificationOptions.value.length) return
  clarificationOptions.value = []
  try {
    const result = await queryProfit({ query: '', session_id: sessionId.value, clarification_choice: option })
    messages.value.push({ role: 'assistant', answer: result.answer, sources: result.sources })
  } catch (e) {
    error.value = e.message || '查询失败'
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
.profit-qa {
  max-width: 900px;
  margin: 0 auto;
  padding: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: white;
  border-bottom: 1px solid #e8e8e8;
}
.header-left { display: flex; align-items: center; gap: 16px; }
.title-group h1 { font-size: 20px; font-weight: 600; color: #1a1a1a; margin: 0; }
.subtitle { font-size: 13px; color: #8c8c8c; }
.new-chat-btn {
  display: flex; align-items: center; gap: 6px; padding: 10px 16px;
  background: white; border: 1px solid #d9d9d9; border-radius: 8px;
  cursor: pointer; font-size: 14px; color: #333; transition: all 0.2s;
}
.new-chat-btn:hover { border-color: #52c41a; color: #52c41a; }
.status-bar {
  display: flex; align-items: center; gap: 24px; padding: 12px 24px;
  background: #fafafa; border-bottom: 1px solid #e8e8e8; font-size: 13px;
}
.status-item { display: flex; align-items: center; gap: 6px; color: #8c8c8c; }
.status-item.connected { color: #52c41a; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #d9d9d9; }
.status-item.connected .status-dot { background: #52c41a; }
.messages { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 24px; }
.welcome { text-align: center; padding: 60px 20px; }
.welcome-icon { margin-bottom: 24px; }
.welcome h2 { font-size: 24px; color: #1a1a1a; margin: 0 0 12px 0; }
.welcome p { font-size: 15px; color: #8c8c8c; margin: 0 0 32px 0; }
.suggestions { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; }
.suggestion-btn {
  padding: 10px 20px; background: white; border: 1px solid #e8e8e8;
  border-radius: 20px; font-size: 14px; color: #333; cursor: pointer; transition: all 0.2s;
}
.suggestion-btn:hover { border-color: #52c41a; color: #52c41a; }
.message-wrapper { display: flex; gap: 12px; max-width: 100%; }
.message-wrapper.user { flex-direction: row-reverse; }
.avatar { flex-shrink: 0; }
.user-avatar, .ai-avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 600; }
.user-avatar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
.ai-avatar { background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%); }
.ai-green { background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%); }
.message-content { max-width: 75%; }
.user-bubble { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 16px; border-radius: 18px 18px 4px 18px; font-size: 15px; line-height: 1.5; }
.loading-bubble { background: white; padding: 16px 24px; border-radius: 18px 18px 18px 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.loading-dots { display: flex; gap: 4px; }
.loading-dots span { width: 8px; height: 8px; border-radius: 50%; background: #52c41a; animation: bounce 1.4s infinite ease-in-out both; }
.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
.error-banner { display: flex; align-items: center; gap: 8px; padding: 12px 16px; background: #fff2f0; border: 1px solid #ffccc7; border-radius: 8px; color: #ff4d4f; font-size: 14px; }
.input-area { padding: 16px 24px 24px; background: white; border-top: 1px solid #e8e8e8; }
</style>
