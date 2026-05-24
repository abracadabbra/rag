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
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"/>
        </svg>
      </button>
    </div>

    <button @click="handleNewSession" class="new-session-btn" :disabled="loading">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
      新建会话
    </button>

    <div class="session-list">
      <div v-if="loading && sessions.length === 0" class="loading">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>
      <div v-else-if="sessions.length === 0" class="empty">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
          <circle cx="20" cy="20" r="18" stroke="#d9d9d9" stroke-width="1.5"/>
          <path d="M14 20h12M20 14v12" stroke="#d9d9d9" stroke-width="1.5" stroke-linecap="round"/>
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
          <button
            @click.stop="startRename(session)"
            class="action-btn rename-btn"
            title="重命名"
          >
            <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor">
              <path d="M12.146.146a.5.5 0 01.708 0l3 3a.5.5 0 010 .708l-10 10a.5.5 0 01-.168.11l-5 2a.5.5 0 01-.65-.65l2-5a.5.5 0 01.11-.168l10-10zM11.207 2.5L13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v.5h.293l6.5-6.5z"/>
            </svg>
          </button>
          <button
            @click.stop="handleDeleteSession(session.session_id)"
            class="action-btn delete-btn"
            title="删除会话"
          >
            <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor">
              <path d="M5.5 5.5A.5.5 0 016 6v6a.5.5 0 01-1 0V6a.5.5 0 01.5-.5zm2.5 0a.5.5 0 01.5.5v6a.5.5 0 01-1 0V6a.5.5 0 01.5-.5zm3 .5a.5.5 0 00-1 0v6a.5.5 0 001 0V6z"/>
              <path fill-rule="evenodd" d="M14.5 3a1 1 0 01-1 1H13v9a2 2 0 01-2 2H5a2 2 0 01-2-2V4h-.5a1 1 0 01-1-1V2a1 1 0 011-1H6a1 1 0 011-1h2a1 1 0 011 1h3.5a1 1 0 011 1v1zM4.118 4L4 4.059V13a1 1 0 001 1h6a1 1 0 001-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Custom delete confirmation modal -->
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
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
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
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border-right: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  transform: translateX(-100%);
  transition: transform 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  z-index: 200;
  box-shadow: none;
}

.session-sidebar.open {
  transform: translateX(0);
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.06);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 20px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
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
  color: #999;
  transition: all 0.15s ease;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.06);
  color: #666;
}

.new-session-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 16px 16px 12px;
  padding: 10px 16px;
  background: #007aff;
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.new-session-btn:hover:not(:disabled) {
  background: #0066d6;
}

.new-session-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.new-session-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px;
}

.session-list::-webkit-scrollbar {
  width: 6px;
}

.session-list::-webkit-scrollbar-track {
  background: transparent;
}

.session-list::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 3px;
}

.loading, .empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #999;
  padding: 40px 20px;
  font-size: 14px;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e8e8e8;
  border-top-color: #007aff;
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
  transition: all 0.15s ease;
  gap: 8px;
}

.session-item:hover {
  background: rgba(0, 0, 0, 0.04);
}

.session-item.active {
  background: rgba(0, 122, 255, 0.08);
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
  color: #1a1a1a;
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
  color: #1a1a1a;
  border: 1px solid #007aff;
  border-radius: 6px;
  padding: 2px 6px;
  outline: none;
  background: white;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.scene-badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.scene-badge.risk_rule {
  background: rgba(24, 144, 255, 0.1);
  color: #1890ff;
}

.scene-badge.model_card {
  background: rgba(114, 46, 209, 0.1);
  color: #722ed1;
}

.scene-badge.simulation {
  background: rgba(250, 140, 22, 0.1);
  color: #fa8c16;
}

.scene-badge.profit {
  background: rgba(82, 196, 26, 0.1);
  color: #52c41a;
}

.message-count {
  font-size: 12px;
  color: #999;
}

.session-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.15s ease;
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
  color: #999;
  transition: all 0.15s ease;
}

.rename-btn:hover {
  background: rgba(0, 0, 0, 0.06);
  color: #666;
}

.delete-btn:hover {
  background: rgba(255, 59, 48, 0.08);
  color: #ff3b30;
}

/* Delete modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 300;
}

.modal-content {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
  border-radius: 14px;
  padding: 24px;
  width: 320px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.12);
}

.modal-content h4 {
  margin: 0 0 8px;
  font-size: 17px;
  font-weight: 600;
  color: #1a1a1a;
  text-align: center;
}

.modal-content p {
  margin: 0 0 20px;
  font-size: 14px;
  color: #666;
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
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.modal-btn.cancel {
  background: rgba(0, 0, 0, 0.06);
  color: #333;
}

.modal-btn.cancel:hover {
  background: rgba(0, 0, 0, 0.1);
}

.modal-btn.danger {
  background: #ff3b30;
  color: white;
}

.modal-btn.danger:hover {
  background: #e0342b;
}

.modal-btn:active {
  transform: scale(0.98);
}

/* Modal transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-content {
  transform: scale(0.95);
  opacity: 0;
}

.modal-leave-to .modal-content {
  transform: scale(0.95);
  opacity: 0;
}
</style>
