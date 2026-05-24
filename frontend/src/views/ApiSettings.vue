<template>
  <div class="api-settings">
    <div class="header">
      <router-link to="/" class="back-btn">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"/>
        </svg>
      </router-link>
      <div class="logo">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="#52c41a"/>
          <path d="M10 16a6 6 0 1112 0 6 6 0 01-12 0zm6-3a3 3 0 100 6 3 3 0 000-6z" fill="white"/>
          <path d="M10 22h12M16 19v6" stroke="white" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="title-group">
        <h1>API 设置</h1>
        <span class="subtitle">配置大语言模型 API</span>
      </div>
    </div>

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

      <!-- MiniMax 配置 -->
      <div v-if="form.llm_provider === 'minimax'" class="settings-card">
        <h2>MiniMax API</h2>
        <div class="form-group">
          <label>API Key</label>
          <input
            v-model="form.minimax_api_key"
            type="password"
            placeholder="sk-..."
            class="text-input"
          />
          <span class="hint">从 MiniMax 控制台获取 API Key</span>
        </div>
        <div class="form-group">
          <label>API Base URL</label>
          <input
            v-model="form.minimax_api_base"
            type="text"
            placeholder="https://api.minimax.chat/v1"
            class="text-input"
          />
        </div>
        <div class="form-group">
          <label>模型名称</label>
          <input
            v-model="form.minimax_model"
            type="text"
            placeholder="MiniMax-M2.7-highspeed"
            class="text-input"
          />
        </div>
      </div>

      <!-- OpenAI 配置 -->
      <div v-if="form.llm_provider === 'openai'" class="settings-card">
        <h2>OpenAI API</h2>
        <div class="form-group">
          <label>API Key</label>
          <input
            v-model="form.openai_api_key"
            type="password"
            placeholder="sk-..."
            class="text-input"
          />
        </div>
        <div class="form-group">
          <label>API Base URL</label>
          <input
            v-model="form.openai_api_base"
            type="text"
            placeholder="https://api.openai.com/v1"
            class="text-input"
          />
        </div>
        <div class="form-group">
          <label>模型名称</label>
          <input
            v-model="form.openai_model"
            type="text"
            placeholder="gpt-4-turbo-preview"
            class="text-input"
          />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Temperature</label>
            <input
              v-model.number="form.openai_temperature"
              type="number"
              min="0"
              max="2"
              step="0.1"
              class="text-input small"
            />
          </div>
          <div class="form-group">
            <label>Max Tokens</label>
            <input
              v-model.number="form.openai_max_tokens"
              type="number"
              min="1"
              max="32000"
              class="text-input small"
            />
          </div>
        </div>
      </div>

      <!-- 本地 LLM 配置 -->
      <div v-if="form.llm_provider === 'local'" class="settings-card">
        <h2>本地 LLM</h2>
        <div class="form-group">
          <label>API Base URL</label>
          <input
            v-model="form.local_llm_base_url"
            type="text"
            placeholder="http://localhost:11434"
            class="text-input"
          />
        </div>
        <div class="form-group">
          <label>模型名称</label>
          <input
            v-model="form.local_llm_model"
            type="text"
            placeholder="qwen2.5:72b"
            class="text-input"
          />
        </div>
      </div>

      <div v-if="error" class="error-banner">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10 0C4.48 0 0 4.48 0 10s4.48 10 10 10 10-4.48 10-10S15.52 0 10 0zm1 15H9v-2h2v2zm0-4H9V5h2v6z"/>
        </svg>
        <span>{{ error }}</span>
      </div>

      <div v-if="success" class="success-banner">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10 0C4.48 0 0 4.48 0 10s4.48 10 10 10 10-4.48 10-10S15.52 0 10 0zm-2 15l-5-5 1.41-1.41L8 12.17l7.59-7.59L17 6l-9 9z"/>
        </svg>
        <span>配置已保存到 .env 文件</span>
      </div>

      <div class="actions">
        <button @click="loadSettings" class="btn secondary" :disabled="loading">
          重置
        </button>
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

const requiredByProvider = {
  minimax: ['minimax_api_key'],
  openai: ['openai_api_key'],
  local: ['local_llm_base_url', 'local_llm_model'],
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
    if (form.openai_temperature < 0 || form.openai_temperature > 2) {
      return 'Temperature 必须在 0-2 之间'
    }
    if (form.openai_max_tokens < 1 || form.openai_max_tokens > 32000) {
      return 'Max Tokens 必须在 1-32000 之间'
    }
  }
  return null
}

const saveSettings = async () => {
  error.value = null
  success.value = false

  const validationError = validate()
  if (validationError) {
    error.value = validationError
    return
  }

  loading.value = true

  const provider = form.llm_provider
  const fields = fieldsByProvider[provider] || fieldsByProvider.minimax

  const updates = {}
  for (const key of fields) {
    updates[key] = form[key]
  }

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

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.api-settings {
  max-width: 680px;
  margin: 0 auto;
  padding: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 32px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 100;
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

.content {
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

.settings-card h2 {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 20px 0;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.form-group {
  margin-bottom: 16px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 6px;
}

.text-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
  background: white;
}

.text-input:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.1);
}

.text-input.small {
  width: 140px;
}

.select-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  font-size: 14px;
  color: #333;
  background: white;
  cursor: pointer;
}

.select-input:focus {
  outline: none;
  border-color: #1890ff;
}

.hint {
  display: block;
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-row .form-group {
  flex: 1;
}

.error-banner,
.success-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 18px;
  border-radius: 12px;
  font-size: 14px;
  animation: slideIn 0.3s ease;
}

.error-banner {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  color: #ff4d4f;
}

.success-banner {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  color: #52c41a;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 8px;
}

.btn {
  padding: 10px 24px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.primary {
  background: #1890ff;
  color: white;
}

.btn.primary:hover:not(:disabled) {
  background: #096dd9;
}

.btn.secondary {
  background: white;
  color: #333;
  border: 1px solid #e8e8e8;
}

.btn.secondary:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
}
</style>
