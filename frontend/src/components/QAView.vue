<template>
  <div class="qa-view">
    <div class="qa-layout" :class="{ 'sidebar-open': sidebarOpen }">
      <div class="sidebar-wrapper">
        <SessionSidebar
          :isOpen="sidebarOpen"
          :currentSessionId="sessionId"
          :sceneType="sceneType"
          @close="sidebarOpen = false"
          @select-session="handleSelectSession"
          @session-created="handleSessionCreated"
          ref="sidebar"
        />
      </div>
      <div class="qa-main">
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
              <h1>{{ title }}</h1>
              <span class="subtitle">{{ subtitle }}</span>
            </div>
          </div>
          <div class="header-actions">
            <button v-if="messages.length > 0" @click="exportChat" class="export-btn" title="导出对话">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 2v7M4 7l3 3 3-3M2 11v1a1 1 0 001 1h8a1 1 0 001-1v-1" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              导出
            </button>
            <button @click="resetSession" class="new-chat-btn">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 2v10M2 7h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              新建会话
            </button>
          </div>
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
          <div v-if="answerPerspectives.length" class="perspective-tabs" aria-label="回答口径">
            <button
              v-for="option in answerPerspectives"
              :key="option.value || 'auto'"
              type="button"
              class="perspective-tab"
              :class="{ active: selectedAnswerPerspective === option.value }"
              :disabled="loading"
              @click="selectedAnswerPerspective = option.value"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <div class="messages" ref="messagesContainer">
          <div v-if="messages.length === 0" class="welcome">
            <h2>{{ welcomeTitle }}</h2>
            <p>{{ welcomeDesc }}</p>
            <div class="suggestions">
              <button
                v-for="q in suggestions"
                :key="q"
                @click="handleSend(q)"
                class="suggestion-btn"
              >{{ q }}</button>
            </div>
          </div>

          <TransitionGroup name="message" tag="div" class="messages-list">
            <div
              v-for="(msg, index) in messages"
              :key="index"
              class="message-wrapper"
              :class="msg.role"
            >
              <div class="avatar">
                <div v-if="msg.role === 'user'" class="user-avatar">U</div>
                <div v-else class="ai-avatar">AI</div>
              </div>
              <div class="message-content">
                <div v-if="msg.role === 'user'" class="user-bubble">{{ msg.content }}</div>
                <template v-else>
                  <div v-if="msg.answer_perspective" class="answer-perspective-chip">
                    回答口径：{{ formatAnswerPerspective(msg.answer_perspective) }}
                  </div>
                  <div v-if="msg.progress_message" class="stream-progress">
                    <span class="progress-pulse"></span>
                    <span>{{ msg.progress_message }}</span>
                  </div>
                  <AnswerDisplay :answer="msg.answer" />
                  <BusinessToolCallList
                    :tool-calls="msg.tool_calls || []"
                    :tool-intent="msg.tool_intent"
                  />
                  <SourceList :sources="msg.sources" :metadata="msg.retrieval_metadata" />
                  <div class="message-actions">
                    <button @click="copyMessage(msg.answer)" class="action-btn" title="复制">
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <rect x="4" y="4" width="8" height="8" rx="2" stroke="currentColor" stroke-width="1.2"/>
                        <path d="M10 4V3a2 2 0 00-2-2H3a2 2 0 00-2 2v5a2 2 0 002 2h1" stroke="currentColor" stroke-width="1.2"/>
                      </svg>
                      <span>{{ copiedIndex === index ? '已复制' : '复制' }}</span>
                    </button>
                    <button
                      v-if="index === messages.length - 1 && msg.role === 'assistant'"
                      @click="handleRegenerate"
                      class="action-btn"
                      :disabled="loading"
                      title="重新生成"
                    >
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M11.5 2.5A5.5 5.5 0 1012 7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                        <path d="M12 2v3h-3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      <span>重新生成</span>
                    </button>
                  </div>
                </template>
              </div>
            </div>
          </TransitionGroup>

          <div v-if="pendingClarification" class="message-wrapper assistant">
            <div class="avatar"><div class="ai-avatar">AI</div></div>
            <div class="message-content">
              <form
                v-if="isOrderIdClarification(pendingClarification)"
                class="clarification-input-card"
                @submit.prevent="handleClarificationInputSubmit"
              >
                <div class="clarification-input-header">
                  <span>{{ pendingClarification.tool_intent?.label || '业务接口查询' }}</span>
                  <strong>{{ formatConfidence(pendingClarification.tool_intent?.confidence) }}</strong>
                </div>
                <div class="clarification-input-row">
                  <input
                    v-model="clarificationInput"
                    type="text"
                    placeholder="输入订单号，例如 ORD88888"
                    :disabled="loading"
                    aria-label="订单号"
                    autocomplete="off"
                  />
                  <button type="submit" :disabled="loading || !clarificationInput.trim()">继续</button>
                </div>
              </form>
              <ClarificationOptions
                v-else
                :options="clarificationOptions"
                @select="handleClarificationSelect"
              />
            </div>
          </div>

          <div v-if="loading" class="message-wrapper assistant">
            <div class="avatar"><div class="ai-avatar">AI</div></div>
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
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { checkReady, getSession, queryScene, querySceneStream } from '../services/api.js'
import ChatInput from './ChatInput.vue'
import AnswerDisplay from './AnswerDisplay.vue'
import BusinessToolCallList from './BusinessToolCallList.vue'
import SourceList from './SourceList.vue'
import ClarificationOptions from './ClarificationOptions.vue'
import SessionSidebar from './SessionSidebar.vue'

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, required: true },
  sceneType: { type: String, required: true },
  welcomeTitle: { type: String, required: true },
  welcomeDesc: { type: String, required: true },
  suggestions: { type: Array, required: true },
  answerPerspectives: { type: Array, default: () => [] }
})

const sessionId = ref(null)
const messages = ref([])
const loading = ref(false)
const error = ref(null)
const clarificationOptions = ref([])
const pendingClarification = ref(null)
const clarificationInput = ref('')
const apiConnected = ref(false)
const messagesContainer = ref(null)
const sidebarOpen = ref(false)
const copiedIndex = ref(null)
const selectedAnswerPerspective = ref('')
let copyTimer = null

onMounted(async () => {
  try {
    await checkReady()
    apiConnected.value = true
  } catch {
    apiConnected.value = false
    error.value = '无法连接到 API 服务，请确保后端已启动'
  }
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  clearTimeout(copyTimer)
})

const handleKeydown = (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    resetSession()
  }
  if (e.key === 'Escape' && sidebarOpen.value) {
    sidebarOpen.value = false
  }
}

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
  pendingClarification.value = null
  clarificationInput.value = ''
  messages.value.push({ role: 'user', content: query })
  loading.value = true

  const msgIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    answer: '',
    sources: [],
    retrieved_count: 0,
    retrieval_metadata: null,
    tool_calls: [],
    tool_intent: null,
    answer_perspective: selectedAnswerPerspective.value || null,
    progress_stage: 'intent',
    progress_message: '正在识别问题意图。'
  })

  try {
    await querySceneStream(props.sceneType, {
      query,
      session_id: sessionId.value,
      answer_perspective: selectedAnswerPerspective.value || null
    }, {
      onSources(data) {
        sessionId.value = data.session_id || sessionId.value
        apiConnected.value = true
        messages.value[msgIndex].sources = data.sources || []
        messages.value[msgIndex].retrieved_count = data.retrieved_count || 0
        messages.value[msgIndex].retrieval_metadata = data.retrieval_metadata || null
        messages.value[msgIndex].tool_calls = data.tool_calls || []
        messages.value[msgIndex].tool_intent = data.tool_intent || null
        messages.value[msgIndex].answer_perspective = data.answer_perspective || selectedAnswerPerspective.value || null
      },
      onChunk(text) {
        clearMessageProgress(msgIndex)
        messages.value[msgIndex].answer += text
      },
      onDone(data) {
        if (data?.session_id) sessionId.value = data.session_id
        clearMessageProgress(msgIndex)
      },
      onClarification(data) {
        sessionId.value = data.session_id || sessionId.value
        messages.value[msgIndex].answer = data.answer || '请补充必要信息后再查询。'
        messages.value[msgIndex].sources = []
        messages.value[msgIndex].retrieved_count = 0
        messages.value[msgIndex].retrieval_metadata = null
        messages.value[msgIndex].tool_calls = []
        messages.value[msgIndex].tool_intent = data.tool_intent || null
        messages.value[msgIndex].answer_perspective = data.answer_perspective || selectedAnswerPerspective.value || null
        clearMessageProgress(msgIndex)
        clarificationOptions.value = data.options || []
        pendingClarification.value = data
        clarificationInput.value = ''
      },
      onProgress(data) {
        setMessageProgress(msgIndex, data)
      },
      onError(data) {
        clearMessageProgress(msgIndex)
        error.value = data.error || '查询失败，请稍后重试'
      }
    })
  } catch (e) {
    error.value = e.message || '查询失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const handleClarificationSelect = async (selectedOption) => {
  if (!selectedOption) return
  clarificationOptions.value = []
  pendingClarification.value = null
  clarificationInput.value = ''
  messages.value.push({ role: 'user', content: selectedOption })
  loading.value = true

  const msgIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    answer: '',
    sources: [],
    retrieved_count: 0,
    retrieval_metadata: null,
    tool_calls: [],
    tool_intent: null,
    answer_perspective: selectedAnswerPerspective.value || null,
    progress_stage: 'intent',
    progress_message: '正在识别问题意图。'
  })

  try {
    await querySceneStream(props.sceneType, {
      query: '',
      session_id: sessionId.value,
      clarification_choice: selectedOption,
      answer_perspective: selectedAnswerPerspective.value || null
    }, {
      onSources(data) {
        if (data.session_id) sessionId.value = data.session_id
        messages.value[msgIndex].sources = data.sources || []
        messages.value[msgIndex].retrieved_count = data.retrieved_count || 0
        messages.value[msgIndex].retrieval_metadata = data.retrieval_metadata || null
        messages.value[msgIndex].tool_calls = data.tool_calls || []
        messages.value[msgIndex].tool_intent = data.tool_intent || null
        messages.value[msgIndex].answer_perspective = data.answer_perspective || selectedAnswerPerspective.value || null
      },
      onChunk(text) {
        clearMessageProgress(msgIndex)
        messages.value[msgIndex].answer += text
      },
      onDone(data) {
        if (data?.session_id) sessionId.value = data.session_id
        clearMessageProgress(msgIndex)
      },
      onClarification(data) {
        if (data.session_id) sessionId.value = data.session_id
        messages.value[msgIndex].answer = data.answer || '请补充必要信息后再查询。'
        messages.value[msgIndex].sources = []
        messages.value[msgIndex].retrieved_count = 0
        messages.value[msgIndex].retrieval_metadata = null
        messages.value[msgIndex].tool_calls = []
        messages.value[msgIndex].tool_intent = data.tool_intent || null
        messages.value[msgIndex].answer_perspective = data.answer_perspective || selectedAnswerPerspective.value || null
        clearMessageProgress(msgIndex)
        clarificationOptions.value = data.options || []
        pendingClarification.value = data
        clarificationInput.value = ''
      },
      onProgress(data) {
        setMessageProgress(msgIndex, data)
      },
      onError(data) {
        clearMessageProgress(msgIndex)
        error.value = data.error || '查询失败'
      }
    })
  } catch (e) {
    error.value = e.message || '查询失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const handleClarificationInputSubmit = async () => {
  const value = clarificationInput.value.trim()
  if (!value) return
  await handleClarificationSelect(value)
}

const copyMessage = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    const idx = messages.value.findIndex(m => m.answer === text)
    copiedIndex.value = idx
    clearTimeout(copyTimer)
    copyTimer = setTimeout(() => { copiedIndex.value = null }, 2000)
  } catch {
    error.value = '复制失败，请手动选择复制'
  }
}

const handleRegenerate = async () => {
  if (loading.value || messages.value.length < 2) return
  const lastUserMsg = [...messages.value].reverse().find(m => m.role === 'user')
  if (!lastUserMsg) return
  messages.value.pop()
  await handleSend(lastUserMsg.content)
}

const exportChat = () => {
  const lines = [`# ${props.title} - 对话记录\n`, `导出时间: ${new Date().toLocaleString('zh-CN')}\n---\n`]
  for (const msg of messages.value) {
    if (msg.role === 'user') {
      lines.push(`## 用户\n${msg.content}\n`)
    } else {
      lines.push(`## AI\n${msg.answer}\n`)
      if (msg.tool_calls?.length) {
        lines.push('**系统接口调用:**')
        for (const call of msg.tool_calls) {
          lines.push(`- ${call.label || call.name}: ${call.summary || call.status}`)
        }
        lines.push('')
      }
      if (msg.sources?.length) {
        lines.push('**来源文档:**')
        for (const s of msg.sources) {
          lines.push(`- ${s.rule_name || s.rule_id || '未知'} (匹配度: ${(s.score * 100).toFixed(0)}%)`)
        }
        lines.push('')
      }
    }
  }
  const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.title}_对话_${new Date().toISOString().slice(0, 10)}.md`
  a.click()
  URL.revokeObjectURL(url)
}

const resetSession = () => {
  sessionId.value = null
  messages.value = []
  error.value = null
  clarificationOptions.value = []
  pendingClarification.value = null
  clarificationInput.value = ''
}

const handleSelectSession = async (newSessionId) => {
  if (!newSessionId) return
  sessionId.value = newSessionId
  sidebarOpen.value = false
  messages.value = []
  clarificationOptions.value = []
  pendingClarification.value = null
  clarificationInput.value = ''
  try {
    const session = await getSession(newSessionId)
    if (session && session.messages) {
      for (const msg of session.messages) {
        if (msg.role === 'user') {
          messages.value.push({ role: 'user', content: msg.content })
        } else if (msg.role === 'assistant') {
          messages.value.push({
            role: 'assistant',
            answer: msg.content,
            sources: [],
            retrieved_count: 0,
            retrieval_metadata: null,
            tool_calls: msg.metadata?.tool_calls || [],
            tool_intent: msg.metadata?.tool_intent || null,
            answer_perspective: msg.metadata?.answer_perspective || null
          })
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
  pendingClarification.value = null
  clarificationInput.value = ''
}

function setMessageProgress(msgIndex, data) {
  const message = messages.value[msgIndex]
  if (!message) return
  message.progress_stage = data?.stage || null
  message.progress_message = data?.message || '正在处理请求。'
}

function clearMessageProgress(msgIndex) {
  const message = messages.value[msgIndex]
  if (!message) return
  message.progress_stage = null
  message.progress_message = ''
}

function formatAnswerPerspective(value) {
  const matched = props.answerPerspectives.find(option => option.value === value)
  return matched?.label || value
}

function isOrderIdClarification(clarification) {
  const missingFields = clarification?.tool_intent?.missing_fields || []
  return missingFields.includes('order_id')
}

function formatConfidence(value) {
  if (typeof value !== 'number') return value ?? ''
  return `${Math.round(value * 100)}%`
}
</script>

<style scoped>
.qa-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.qa-layout {
  display: flex;
  flex: 1;
  min-height: 0;
}

.sidebar-wrapper {
  flex: 0 0 0;
  overflow: hidden;
  transition: flex-basis 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.sidebar-open .sidebar-wrapper {
  flex: 0 0 300px;
}

.qa-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 14px;
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

.export-btn:hover {
  border-color: var(--border-default);
  color: var(--text-primary);
  background: var(--bg-hover);
}

.status-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
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

.session-label {
  color: var(--text-muted);
}

.session-id {
  font-family: var(--font-mono);
  background: var(--bg-hover);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
}

.perspective-tabs {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-surface);
}

.perspective-tab {
  min-width: 42px;
  height: 24px;
  padding: 0 8px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.perspective-tab:hover:not(:disabled) {
  color: var(--text-secondary);
  background: var(--bg-hover);
}

.perspective-tab.active {
  color: var(--text-primary);
  background: var(--accent);
}

.perspective-tab:disabled {
  cursor: not-allowed;
  opacity: 0.6;
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

.answer-perspective-chip {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  margin: 0 0 8px;
  padding: 4px 8px;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  background: var(--bg-surface);
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.3;
  word-break: break-word;
}

.stream-progress {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  max-width: 100%;
  margin: 0 0 8px;
  padding: 6px 10px;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  background: var(--bg-surface);
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.4;
  word-break: break-word;
}

.progress-pulse {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 0 color-mix(in srgb, var(--accent) 35%, transparent);
  animation: progressPulse 1.4s infinite;
  flex-shrink: 0;
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

.clarification-input-card {
  background: var(--bg-card);
  border: 1px solid rgba(245, 158, 11, 0.24);
  border-radius: 16px 16px 16px 4px;
  padding: 14px 16px;
  min-width: min(420px, 100%);
}

.clarification-input-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  color: var(--text-secondary);
  font-size: 13px;
  font-family: var(--font-display);
}

.clarification-input-header span {
  color: #f59e0b;
  font-weight: 600;
}

.clarification-input-header strong {
  color: var(--text-muted);
  background: var(--bg-elevated);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
}

.clarification-input-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.clarification-input-row input {
  flex: 1;
  min-width: 0;
  height: 38px;
  padding: 0 12px;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  background: var(--bg-surface);
  color: var(--text-primary);
  font-size: 13px;
  font-family: var(--font-body);
}

.clarification-input-row input:focus {
  outline: none;
  border-color: #f59e0b;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
}

.clarification-input-row input::placeholder {
  color: var(--text-muted);
}

.clarification-input-row button {
  height: 38px;
  padding: 0 14px;
  border: none;
  border-radius: 8px;
  background: #f59e0b;
  color: #111827;
  cursor: pointer;
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
  transition: filter 0.2s, transform 0.2s;
}

.clarification-input-row button:hover:not(:disabled) {
  filter: brightness(1.08);
  transform: translateY(-1px);
}

.clarification-input-row button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

@keyframes progressPulse {
  0% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--accent) 35%, transparent); }
  70% { box-shadow: 0 0 0 6px transparent; }
  100% { box-shadow: 0 0 0 0 transparent; }
}

.message-enter-active { animation: slideIn 0.3s ease; }
.message-leave-active { animation: slideOut 0.2s ease; }

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
}

.message-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-wrapper:hover .message-actions {
  opacity: 1;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  color: var(--text-muted);
  font-size: 11px;
  font-family: var(--font-body);
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  border-color: var(--border-default);
  color: var(--text-secondary);
  background: var(--bg-card);
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.input-area {
  padding: 16px 24px 20px;
  background: rgba(14, 19, 34, 0.8);
  backdrop-filter: blur(20px);
  border-top: 1px solid var(--border-subtle);
}
</style>
