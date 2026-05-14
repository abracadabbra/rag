<template>
  <div class="cache-admin">
    <div class="header">
      <div class="header-left">
        <button @click="$emit('back')" class="back-btn">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"/>
          </svg>
        </button>
        <div class="title-group">
          <h1>缓存管理</h1>
          <span class="subtitle">Redis 缓存状态与控制</span>
        </div>
      </div>
      <button @click="refresh" class="refresh-btn" :disabled="loading">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path d="M8 3v4l3-3-3-3v4A5 5 0 108 13a5 5 0 005-5H11a3 3 0 11-6 0"/>
        </svg>
        刷新
      </button>
    </div>

    <div class="content">
      <div v-if="error" class="error-banner">
        <span>{{ error }}</span>
      </div>

      <div class="stats-grid" v-if="stats">
        <div class="stat-card">
          <div class="stat-label">缓存状态</div>
          <div class="stat-value" :class="stats.enabled ? 'enabled' : 'disabled'">
            {{ stats.enabled ? '已启用' : '已禁用' }}
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">缓存 Key 数</div>
          <div class="stat-value">{{ stats.total_keys || 0 }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">TTL</div>
          <div class="stat-value">{{ stats.ttl || 0 }} 秒</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">内存使用</div>
          <div class="stat-value">{{ stats.memory_used_human || 'N/A' }}</div>
        </div>
      </div>

      <div class="actions">
        <h3>操作</h3>
        <div class="action-buttons">
          <button @click="clearAll" class="danger-btn" :disabled="loading">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M4.5 3V2a1 1 0 011-1h3a1 1 0 011 1v1h3v1h-1v8a1 1 0 01-1 1H3.5a1 1 0 01-1-1V4H1V3h3.5zM5 4v7h1V4H5zm3 0v7h1V4H8z"/>
            </svg>
            清空所有缓存
          </button>
          <button @click="clearRiskRules" class="warning-btn" :disabled="loading">
            清除风控规则缓存
          </button>
          <button @click="clearByPattern" class="warning-btn" :disabled="loading">
            清除查询缓存
          </button>
        </div>
      </div>

      <div v-if="message" class="success-banner">
        <span>{{ message }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getCacheStats, invalidateCache, clearAllCache } from '../services/api.js'

const emit = defineEmits(['back'])

const stats = ref(null)
const loading = ref(false)
const error = ref(null)
const message = ref(null)

async function loadStats() {
  loading.value = true
  error.value = null
  try {
    stats.value = await getCacheStats()
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function refresh() {
  await loadStats()
}

async function clearAll() {
  if (!confirm('确定要清空所有缓存吗？')) return
  loading.value = true
  error.value = null
  message.value = null
  try {
    const result = await clearAllCache()
    message.value = result.message
    await loadStats()
  } catch (e) {
    error.value = e.message || '操作失败'
  } finally {
    loading.value = false
  }
}

async function clearRiskRules() {
  loading.value = true
  error.value = null
  message.value = null
  try {
    const result = await invalidateCache('risk_rule')
    message.value = result.message
    await loadStats()
  } catch (e) {
    error.value = e.message || '操作失败'
  } finally {
    loading.value = false
  }
}

async function clearByPattern() {
  loading.value = true
  error.value = null
  message.value = null
  try {
    const result = await invalidateCache('rag:query:*')
    message.value = result.message
    await loadStats()
  } catch (e) {
    error.value = e.message || '操作失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.cache-admin { max-width: 800px; margin: 0 auto; padding: 0; }
.header { display: flex; justify-content: space-between; align-items: center; padding: 20px 32px; background: white; border-bottom: 1px solid #e8e8e8; }
.header-left { display: flex; align-items: center; gap: 12px; }
.back-btn { display: flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 10px; background: none; border: none; color: #666; cursor: pointer; transition: all 0.2s; }
.back-btn:hover { background: #f5f5f5; color: #333; }
.title-group h1 { margin: 0; font-size: 18px; font-weight: 600; }
.subtitle { font-size: 13px; color: #8c8c8c; }
.refresh-btn { display: flex; align-items: center; gap: 6px; padding: 10px 18px; background: white; border: 1px solid #e8e8e8; border-radius: 10px; cursor: pointer; font-size: 14px; color: #333; transition: all 0.2s; }
.refresh-btn:hover:not(:disabled) { border-color: #1890ff; color: #1890ff; }
.refresh-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.content { padding: 24px 32px; }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: white; border: 1px solid #e8e8e8; border-radius: 12px; padding: 16px; }
.stat-label { font-size: 13px; color: #8c8c8c; margin-bottom: 8px; }
.stat-value { font-size: 24px; font-weight: 600; color: #333; }
.stat-value.enabled { color: #52c41a; }
.stat-value.disabled { color: #ff4d4f; }
.actions h3 { font-size: 16px; font-weight: 600; margin: 0 0 12px 0; }
.action-buttons { display: flex; gap: 12px; flex-wrap: wrap; }
.danger-btn, .warning-btn { display: flex; align-items: center; gap: 6px; padding: 10px 18px; border-radius: 8px; cursor: pointer; font-size: 14px; transition: all 0.2s; }
.danger-btn { background: #fff2f0; border: 1px solid #ffccc7; color: #ff4d4f; }
.danger-btn:hover:not(:disabled) { background: #ffccc7; }
.warning-btn { background: #fff7e6; border: 1px solid #ffd591; color: #fa8c16; }
.warning-btn:hover:not(:disabled) { background: #ffe7ba; }
.danger-btn:disabled, .warning-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.error-banner { background: #fff2f0; border: 1px solid #ffccc7; border-radius: 8px; padding: 12px 16px; color: #ff4d4f; margin-bottom: 16px; }
.success-banner { background: #f6ffed; border: 1px solid #b7eb8f; border-radius: 8px; padding: 12px 16px; color: #52c41a; margin-top: 16px; }
</style>
