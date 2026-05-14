<template>
  <aside class="session-sidebar" :class="{ open: isOpen }">
    <div class="sidebar-header">
      <h3>会话列表</h3>
      <button @click="$emit('close')" class="close-btn">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"/>
        </svg>
      </button>
    </div>

    <button @click="handleNewSession" class="new-session-btn" :disabled="loading">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
        <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
      新建会话
    </button>

    <div class="session-list">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="sessions.length === 0" class="empty">
        暂无会话
      </div>
      <div
        v-else
        v-for="session in sessions"
        :key="session.session_id"
        class="session-item"
        :class="{ active: session.session_id === currentSessionId }"
        @click="handleSelectSession(session.session_id)"
      >
        <div class="session-info">
          <span class="session-title">{{ session.title || '新会话' }}</span>
          <span class="session-meta">{{ session.message_count }} 条消息</span>
        </div>
        <button
          @click.stop="handleDeleteSession(session.session_id)"
          class="delete-btn"
          title="删除会话"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
            <path d="M4.5 3V2a1 1 0 011-1h3a1 1 0 011 1v1h3v1h-1v8a1 1 0 01-1 1H3.5a1 1 0 01-1-1V4H1V3h3.5zM5 4v7h1V4H5zm3 0v7h1V4H8z"/>
          </svg>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listSessions, createSession, deleteSession } from '../services/api.js'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  currentSessionId: { type: String, default: null }
})

const emit = defineEmits(['close', 'select-session', 'session-created'])

const sessions = ref([])
const loading = ref(false)

async function loadSessions() {
  loading.value = true
  try {
    const data = await listSessions()
    sessions.value = data.sessions
  } catch (e) {
    console.error('加载会话列表失败:', e)
  } finally {
    loading.value = false
  }
}

async function handleNewSession() {
  try {
    const data = await createSession(null, 'risk_rule')
    sessions.value.unshift({
      session_id: data.session_id,
      title: '新会话',
      message_count: 0
    })
    emit('session-created', data.session_id)
  } catch (e) {
    console.error('创建会话失败:', e)
  }
}

async function handleDeleteSession(sessionId) {
  if (!confirm('确定要删除这个会话吗？')) return

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

onMounted(() => {
  loadSessions()
})

defineExpose({ loadSessions })
</script>

<style scoped>
.session-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 280px;
  background: white;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  transform: translateX(-100%);
  transition: transform 0.3s ease;
  z-index: 200;
}

.session-sidebar.open {
  transform: translateX(0);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  padding: 4px;
}

.new-session-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 12px 16px;
  padding: 10px 16px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.new-session-btn:hover:not(:disabled) {
  background: #40a9ff;
}

.new-session-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.loading, .empty {
  text-align: center;
  color: #999;
  padding: 20px;
  font-size: 14px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.session-item:hover {
  background: #f5f5f5;
}

.session-item.active {
  background: #e6f7ff;
}

.session-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.session-title {
  font-size: 14px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  font-size: 12px;
  color: #999;
}

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  padding: 4px;
  opacity: 0;
  transition: opacity 0.2s, color 0.2s;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  color: #ff4d4f;
}
</style>
