<template>
  <div class="cache-admin">
    <header class="header">
      <div class="header-left">
        <button @click="$emit('back')" class="back-btn">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M12 4L6 9l6 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <div class="title-group"><h1>缓存管理</h1><span class="subtitle">管理系统缓存</span></div>
      </div>
      <button @click="loadStats" class="refresh-btn" :disabled="loading"><svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M12 7A5 5 0 113.5 3M3.5 3V1M3.5 3h2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>刷新</button>
    </header>
    <div class="content">
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-label">总缓存数</div><div class="stat-value">{{ stats.total_keys || 0 }}</div></div>
        <div class="stat-card"><div class="stat-label">缓存状态</div><div class="stat-value" :class="stats.cache_enabled ? 'enabled' : 'disabled'">{{ stats.cache_enabled ? '已启用' : '已禁用' }}</div></div>
        <div class="stat-card"><div class="stat-label">命中/总数</div><div class="stat-value">{{ stats.hit_count || 0 }}/{{ stats.total_requests || 0 }}</div></div>
        <div class="stat-card"><div class="stat-label">命中率</div><div class="stat-value">{{ stats.hit_rate || '0%' }}</div></div>
      </div>
      <div class="actions"><h3>操作</h3><div class="action-buttons">
        <button @click="clearAll" class="danger-btn" :disabled="loading">清空所有缓存</button>
        <button @click="clearRiskRules" class="warning-btn" :disabled="loading">清除风控规则缓存</button>
        <button @click="clearByPattern" class="warning-btn" :disabled="loading">清除查询缓存</button>
      </div></div>
      <div v-if="error" class="error-banner"><span>{{ error }}</span></div>
      <div v-if="message" class="success-banner"><span>{{ message }}</span></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getCacheStats, clearAllCache, invalidateCache } from '../services/api.js'

defineEmits(['back'])
const loading = ref(false); const error = ref(null); const message = ref(null); const stats = ref({})

async function loadStats() {
  loading.value = true; error.value = null; message.value = null
  try { stats.value = await getCacheStats() } catch (e) { error.value = e.message || '获取缓存统计失败' } finally { loading.value = false }
}

async function clearAll() { loading.value = true; error.value = null; message.value = null; try { message.value = (await clearAllCache()).message; await loadStats() } catch (e) { error.value = e.message || '操作失败' } finally { loading.value = false } }
async function clearRiskRules() { loading.value = true; error.value = null; message.value = null; try { message.value = (await invalidateCache('risk_rule')).message; await loadStats() } catch (e) { error.value = e.message || '操作失败' } finally { loading.value = false } }
async function clearByPattern() { loading.value = true; error.value = null; message.value = null; try { message.value = (await invalidateCache('rag:query:*')).message; await loadStats() } catch (e) { error.value = e.message || '操作失败' } finally { loading.value = false } }

onMounted(() => loadStats())
</script>

<style scoped>
.cache-admin { max-width: 800px; margin: 0 auto; padding: 0; min-height: 100vh; position: relative; z-index: 1; }
.header { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; background: rgba(14, 19, 34, 0.8); backdrop-filter: blur(20px); border-bottom: 1px solid var(--border-subtle); position: sticky; top: 0; z-index: 100; }
.header-left { display: flex; align-items: center; gap: 12px; }
.back-btn { display: flex; align-items: center; justify-content: center; width: 34px; height: 34px; border-radius: 10px; color: var(--text-muted); background: none; border: none; cursor: pointer; transition: all 0.2s; }
.back-btn:hover { background: var(--bg-hover); color: var(--text-secondary); }
.title-group h1 { font-family: var(--font-display); font-size: 17px; font-weight: 600; color: var(--text-primary); margin: 0; letter-spacing: -0.01em; }
.subtitle { font-size: 12px; color: var(--text-muted); }
.refresh-btn { display: flex; align-items: center; gap: 6px; padding: 8px 16px; background: transparent; border: 1px solid var(--border-subtle); border-radius: 10px; cursor: pointer; font-size: 13px; color: var(--text-secondary); transition: all 0.2s; font-family: var(--font-display); }
.refresh-btn:hover:not(:disabled) { border-color: var(--glow); color: var(--accent); background: var(--accent-dim); }
.refresh-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.content { padding: 24px; }
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
.stat-card { background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 16px; }
.stat-label { font-size: 12px; color: var(--text-muted); margin-bottom: 8px; }
.stat-value { font-size: 22px; font-weight: 600; color: var(--text-primary); font-family: var(--font-display); }
.stat-value.enabled { color: #10b981; }
.stat-value.disabled { color: #ef4444; }
.actions h3 { font-family: var(--font-display); font-size: 15px; font-weight: 600; color: var(--text-primary); margin: 0 0 14px; letter-spacing: -0.01em; }
.action-buttons { display: flex; gap: 12px; flex-wrap: wrap; }
.danger-btn, .warning-btn { display: flex; align-items: center; gap: 6px; padding: 10px 18px; border-radius: 10px; cursor: pointer; font-size: 13px; transition: all 0.2s; font-family: var(--font-display); border: none; }
.danger-btn { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); color: #ef4444; }
.danger-btn:hover:not(:disabled) { background: rgba(239, 68, 68, 0.2); }
.warning-btn { background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); color: #f59e0b; }
.warning-btn:hover:not(:disabled) { background: rgba(245, 158, 11, 0.2); }
.danger-btn:disabled, .warning-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.error-banner { background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 10px; padding: 12px 16px; color: #ef4444; margin-top: 16px; font-size: 13px; }
.success-banner { background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 10px; padding: 12px 16px; color: #10b981; margin-top: 16px; font-size: 13px; }
</style>
