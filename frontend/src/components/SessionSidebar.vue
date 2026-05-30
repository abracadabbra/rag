<template>
  <Teleport to="body">
    <Transition name="overlay">
      <div v-if="isOpen" class="sidebar-overlay" @click="$emit('close')"></div>
    </Transition>
  </Teleport>

  <aside class="session-sidebar" :class="{ open: isOpen }">
    <div class="sidebar-header">
      <h3>会话列表</h3>
      <button @click="$emit('close')" class="close-btn" aria-label="关闭">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M5 5l8 8M13 5l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <button @click="handleNewSession" class="new-session-btn" :disabled="loading">
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M7 2v10M2 7h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
      新建会话
    </button>

    <div class="session-list">
      <div v-if="loading && sessions.length === 0" class="loading">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>
      <div v-else-if="sessions.length === 0" class="empty">
        <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
          <circle cx="18" cy="18" r="16" stroke="currentColor" stroke-width="1" opacity="0.3"/>
          <path d="M13 18h10M18 13v10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" opacity="0.3"/>
        </svg>
        <span>暂无会话</span>
      </div>
      <div
        v-for="session in sessions"
        :key="session.session_id"
        class="session-item"
        :class="{ active: session.session_id === currentSessionId }"
        @click="handleSelectSession(session.session_id)"
      >
        <div class="session-info">
          <div v-if="renamingId === session.session_id" class="rename-input-wrapper">
            <input
              ref="renameInput"
              v-model="renameValue"
              class="rename-input"
              @keydown.enter="confirmRename(session.session_id)"
              @keydown.escape="cancelRename"
              @blur="confirmRename(session.session_id)"
              @click.stop
            />
          </div>
          <span v-else class="session-title" @dblclick.stop="startRename(session)">
            {{ session.title || '新会话' }}
          </span>
          <div class="session-meta">
            <span v-if="session.scene_type" class="scene-badge" :class="session.scene_type">
              {{ sceneLabels[session.scene_type] || session.scene_type }}
            </span>
            <span class="message-count">{{ session.message_count }} 条消息</span>
          </div>
        </div>
        <div class="session-actions">
          <button @click.stop="startRename(session)" class="action-btn" title="重命名">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M9 1l2 2-7 7H2V8l7-7z" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/>
            </svg>
          </button>
          <button @click.stop="handleDeleteSession(session.session_id)" class="action-btn delete" title="删除会话">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M2 3h8M5 3V2a1 1 0 012 0v1M4 5v5M6 5v5M8 5v5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              <path d="M2.5 3l.5 7.5a1 1 0 001 1h4a1 1 0 001-1L9.5 3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <Transition name="modal">
      <div v-if="deleteTarget" class="modal-overlay" @click="deleteTarget = null">
        <div class="modal-content" @click.stop>
          <h4>删除会话</h4>
          <p>确定要删除这个会话吗？此操作无法撤销。</p>
          <div class="modal-actions">
            <button @click="deleteTarget = null" class="modal-btn cancel">取消</button>
            <button @click="confirmDelete" class="modal-btn danger">删除</button>
          </div>
        </div>
      </div>
    </Transition>
  </aside>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { listSessions, createSession, deleteSession, updateSessionTitle } from '../services/api.js'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  currentSessionId: { type: String, default: null },
  sceneType: { type: String, default: null }
})

const emit = defineEmits(['close', 'select-session', 'session-created'])

const sessions = ref([])
const loading = ref(false)
const deleteTarget = ref(null)
const renamingId = ref(null)
const renameValue = ref('')
const renameInput = ref(null)

const sceneLabels = {
  risk_rule: '风控',
  model_card: '模型',
  simulation: '仿真',
  profit: '毛利'
}

watch(() => props.isOpen, (open) => {
  if (open) loadSessions()
})

async function loadSessions() {
  loading.value = true
  try {
    const data = await listSessions()
    sessions.value = data.sessions || []
  } catch (e) {
    console.error('加载会话列表失败:', e)
  } finally {
    loading.value = false
  }
}

async function handleNewSession() {
  try {
    const data = await createSession(null, props.sceneType)
    const newSession = {
      session_id: data.session_id,
      title: '新会话',
      message_count: 0,
      scene_type: props.sceneType
    }
    sessions.value.unshift(newSession)
    emit('session-created', data.session_id)
  } catch (e) {
    console.error('创建会话失败:', e)
  }
}

function handleDeleteSession(sessionId) {
  deleteTarget.value = sessionId
}

async function confirmDelete() {
  const sessionId = deleteTarget.value
  if (!sessionId) return
  deleteTarget.value = null
  try {
    await deleteSession(sessionId)
    sessions.value = sessions.value.filter(s => s.session_id !== sessionId)
    if (props.currentSessionId === sessionId) {
      emit('select-session', null)
    }
  } catch (e) {
    console.error('删除会话失败:', e)
  }
}

function handleSelectSession(sessionId) {
  emit('select-session', sessionId)
}

function startRename(session) {
  renamingId.value = session.session_id
  renameValue.value = session.title || ''
  nextTick(() => {
    const input = renameInput.value
    if (input && input[0]) {
      input[0].focus()
      input[0].select()
    }
  })
}

function cancelRename() {
  renamingId.value = null
  renameValue.value = ''
}

async function confirmRename(sessionId) {
  const newTitle = renameValue.value.trim()
  cancelRename()
  if (!newTitle) return
  try {
    await updateSessionTitle(sessionId, newTitle)
    const session = sessions.value.find(s => s.session_id === sessionId)
    if (session) session.title = newTitle
  } catch (e) {
    console.error('重命名失败:', e)
  }
}

defineExpose({ loadSessions })
</script>

<style scoped>
.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 199;
}

.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.3s ease;
}
.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}

.session-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 300px;
  background: rgba(14, 19, 34, 0.95);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  transform: translateX(-100%);
  visibility: hidden;
  transition: transform 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  z-index: 200;
}

.session-sidebar.open {
  transform: translateX(0);
  visibility: visible;
  box-shadow: 4px 0 40px rgba(0, 0, 0, 0.3);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 20px 16px;
  border-bottom: 1px solid var(--border-subtle);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-display);
  letter-spacing: -0.01em;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  transition: all 0.15s;
}

.close-btn:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.new-session-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 14px 16px 10px;
  padding: 10px 16px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  font-family: var(--font-display);
  transition: all 0.15s;
}

.new-session-btn:hover:not(:disabled) {
  filter: brightness(1.15);
  box-shadow: 0 4px 16px var(--glow);
}

.new-session-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.new-session-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 2px 8px;
}

.loading, .empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-muted);
  padding: 40px 20px;
  font-size: 13px;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(212, 168, 67, 0.15);
  border-top-color: var(--accent-risk);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.session-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
  gap: 8px;
}

.session-item:hover {
  background: var(--bg-hover);
}

.session-item.active {
  background: var(--accent-dim);
  border: 1px solid var(--glow);
  padding: 9px 11px;
}

.session-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.rename-input-wrapper {
  display: flex;
}

.rename-input {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  border: 1px solid var(--accent);
  border-radius: 6px;
  padding: 2px 6px;
  outline: none;
  background: var(--bg-card);
  box-shadow: 0 0 0 3px var(--glow);
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.scene-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.scene-badge.risk_rule {
  background: rgba(212, 168, 67, 0.12);
  color: #d4a843;
}
.scene-badge.model_card {
  background: rgba(124, 58, 237, 0.12);
  color: #7c3aed;
}
.scene-badge.simulation {
  background: rgba(245, 158, 11, 0.12);
  color: #f59e0b;
}
.scene-badge.profit {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

.message-count {
  font-size: 11px;
  color: var(--text-muted);
}

.session-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.15s;
}

.session-item:hover .session-actions {
  opacity: 1;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  transition: all 0.15s;
}

.action-btn:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.action-btn.delete:hover {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 300;
}

.modal-content {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  padding: 24px;
  width: 320px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3);
}

.modal-content h4 {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  text-align: center;
  font-family: var(--font-display);
}

.modal-content p {
  margin: 0 0 20px;
  font-size: 14px;
  color: var(--text-secondary);
  text-align: center;
  line-height: 1.5;
}

.modal-actions {
  display: flex;
  gap: 12px;
}

.modal-btn {
  flex: 1;
  padding: 10px 16px;
  border-radius: 10px;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.modal-btn.cancel {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.modal-btn.cancel:hover {
  background: rgba(255, 255, 255, 0.08);
}

.modal-btn.danger {
  background: #ef4444;
  color: white;
}

.modal-btn.danger:hover {
  background: #dc2626;
}

.modal-btn:active {
  transform: scale(0.98);
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal-content {
  transform: scale(0.95);
}
.modal-leave-to .modal-content {
  transform: scale(0.95);
}
</style>
