<template>
  <div class="api-settings">
    <header class="header">
      <router-link to="/" class="back-btn">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M12 4L6 9l6 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </router-link>
      <div class="title-group">
        <h1>API 设置</h1>
        <span class="subtitle">配置大语言模型服务</span>
      </div>
    </header>

    <div class="content">
      <div class="settings-card">
        <h2>LLM 提供商</h2>
        <div class="form-group">
          <label>当前提供商</label>
          <select v-model="form.llm_provider" class="select-input">
            <option value="minimax">MiniMax</option>
            <option value="openai">OpenAI</option>
            <option value="local">本地 LLM</option>
          </select>
        </div>
      </div>

      <div v-if="form.llm_provider === 'minimax'" class="settings-card">
        <h2>MiniMax API</h2>
        <div class="form-group">
          <label>API Key</label>
          <input v-model="form.minimax_api_key" type="password" placeholder="sk-..." class="text-input" />
          <span class="hint">从 MiniMax 控制台获取 API Key</span>
        </div>
        <div class="form-group">
          <label>API Base URL</label>
          <input v-model="form.minimax_api_base" type="text" placeholder="https://api.minimax.chat/v1" class="text-input" />
        </div>
        <div class="form-group">
          <label>模型名称</label>
          <input v-model="form.minimax_model" type="text" placeholder="MiniMax-M2.7-highspeed" class="text-input" />
        </div>
      </div>

      <div v-if="form.llm_provider === 'openai'" class="settings-card">
        <h2>OpenAI API</h2>
        <div class="form-group">
          <label>API Key</label>
          <input v-model="form.openai_api_key" type="password" placeholder="sk-..." class="text-input" />
        </div>
        <div class="form-group">
          <label>API Base URL</label>
          <input v-model="form.openai_api_base" type="text" placeholder="https://api.openai.com/v1" class="text-input" />
        </div>
        <div class="form-group">
          <label>模型名称</label>
          <input v-model="form.openai_model" type="text" placeholder="gpt-4-turbo-preview" class="text-input" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Temperature</label>
            <input v-model.number="form.openai_temperature" type="number" min="0" max="2" step="0.1" class="text-input small" />
          </div>
          <div class="form-group">
            <label>Max Tokens</label>
            <input v-model.number="form.openai_max_tokens" type="number" min="1" max="32000" class="text-input small" />
          </div>
        </div>
      </div>

      <div v-if="form.llm_provider === 'local'" class="settings-card">
        <h2>本地 LLM</h2>
        <div class="form-group">
          <label>API Base URL</label>
          <input v-model="form.local_llm_base_url" type="text" placeholder="http://localhost:11434" class="text-input" />
        </div>
        <div class="form-group">
          <label>模型名称</label>
          <input v-model="form.local_llm_model" type="text" placeholder="qwen2.5:72b" class="text-input" />
        </div>
      </div>

      <div v-if="error" class="error-banner">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.2"/>
          <path d="M9 6v3M9 11.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span>{{ error }}</span>
      </div>

      <div v-if="success" class="success-banner">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.2"/>
          <path d="M6 9l2 2 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>配置已保存到 .env 文件</span>
      </div>

      <div class="actions">
        <button @click="loadSettings" class="btn secondary" :disabled="loading">重置</button>
        <button @click="saveSettings" class="btn primary" :disabled="loading">
          {{ loading ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getLlmSettings, updateLlmSettings } from '../services/api.js'

const loading = ref(false)
const error = ref(null)
const success = ref(false)

const form = reactive({
  llm_provider: 'minimax',
  minimax_api_key: '',
  minimax_api_base: '',
  minimax_model: '',
  openai_api_key: '',
  openai_api_base: '',
  openai_model: '',
  openai_temperature: 0.7,
  openai_max_tokens: 2000,
  local_llm_base_url: '',
  local_llm_model: '',
})

const fieldsByProvider = {
  minimax: ['llm_provider', 'minimax_api_key', 'minimax_api_base', 'minimax_model'],
  openai: ['llm_provider', 'openai_api_key', 'openai_api_base', 'openai_model', 'openai_temperature', 'openai_max_tokens'],
  local: ['llm_provider', 'local_llm_base_url', 'local_llm_model'],
}

const requiredByProvider = {
  minimax: ['minimax_api_key'],
  openai: ['openai_api_key'],
  local: ['local_llm_base_url', 'local_llm_model'],
}

const loadSettings = async () => {
  loading.value = true
  error.value = null
  success.value = false
  try {
    const data = await getLlmSettings()
    form.llm_provider = data.llm_provider || 'minimax'
    form.minimax_api_key = ''
    form.minimax_api_base = data.minimax_api_base || ''
    form.minimax_model = data.minimax_model || ''
    form.openai_api_key = ''
    form.openai_api_base = data.openai_api_base || ''
    form.openai_model = data.openai_model || ''
    form.openai_temperature = parseFloat(data.openai_temperature) || 0.7
    form.openai_max_tokens = parseInt(data.openai_max_tokens) || 2000
    form.local_llm_base_url = data.local_llm_base_url || ''
    form.local_llm_model = data.local_llm_model || ''
  } catch (e) {
    error.value = e.message || '加载配置失败'
  } finally {
    loading.value = false
  }
}

const validate = () => {
  const provider = form.llm_provider
  const required = requiredByProvider[provider] || []
  for (const field of required) {
    if (!form[field] || !form[field].toString().trim()) {
      return `${field} 为必填项`
    }
  }
  if (provider === 'openai') {
    if (form.openai_temperature < 0 || form.openai_temperature > 2) return 'Temperature 必须在 0-2 之间'
    if (form.openai_max_tokens < 1 || form.openai_max_tokens > 32000) return 'Max Tokens 必须在 1-32000 之间'
  }
  return null
}

const saveSettings = async () => {
  error.value = null
  success.value = false
  const validationError = validate()
  if (validationError) { error.value = validationError; return }
  loading.value = true
  const provider = form.llm_provider
  const fields = fieldsByProvider[provider] || fieldsByProvider.minimax
  const updates = {}
  for (const key of fields) { updates[key] = form[key] }
  try {
    await updateLlmSettings(updates)
    success.value = true
    setTimeout(() => { success.value = false }, 3000)
  } catch (e) {
    error.value = e.message || '保存配置失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => loadSettings())
</script>

<style scoped>
.api-settings {
  max-width: 640px;
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
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background: rgba(14, 19, 34, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-subtle);
  position: sticky;
  top: 0;
  z-index: 100;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  color: var(--text-muted);
  transition: all 0.2s;
}

.back-btn:hover {
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

.content {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.settings-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  padding: 20px;
}

.settings-card h2 {
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-subtle);
  letter-spacing: -0.01em;
}

.form-group {
  margin-bottom: 14px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.text-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-surface);
  transition: all 0.2s;
  font-family: var(--font-body);
}

.text-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--glow);
}

.text-input::placeholder {
  color: var(--text-muted);
}

.text-input.small {
  width: 140px;
}

.select-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary);
  background: var(--bg-surface);
  cursor: pointer;
  font-family: var(--font-body);
}

.select-input:focus {
  outline: none;
  border-color: var(--accent);
}

.hint {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

.form-row {
  display: flex;
  gap: 14px;
}

.form-row .form-group {
  flex: 1;
}

.error-banner,
.success-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 13px;
  animation: fadeSlideIn 0.3s ease;
}

.error-banner {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.success-banner {
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.2);
  color: #10b981;
}

@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 4px;
}

.btn {
  padding: 10px 22px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  font-family: var(--font-display);
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn.primary {
  background: var(--accent);
  color: var(--bg-base);
}

.btn.primary:hover:not(:disabled) {
  filter: brightness(1.15);
  box-shadow: 0 4px 16px var(--glow);
}

.btn.secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
}

.btn.secondary:hover:not(:disabled) {
  border-color: var(--border-default);
  color: var(--text-primary);
}
</style>
