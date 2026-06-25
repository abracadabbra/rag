/**
 * RAG API 服务
 */

const API_BASE = '/api/v1'
const BUSINESS_TOOL_TOKEN_HEADER = 'X-Business-Tool-Token'
const BUSINESS_TOOL_REQUEST_TOKEN_KEY = 'rag.businessToolRequestToken'
const BUSINESS_SCENES = new Set(['risk_rule', 'profit'])

function readSessionValue(key) {
  try {
    return window.sessionStorage.getItem(key) || ''
  } catch (_e) {
    return ''
  }
}

function writeSessionValue(key, value) {
  try {
    if (value) window.sessionStorage.setItem(key, value)
    else window.sessionStorage.removeItem(key)
  } catch (_e) {
    // Ignore unavailable storage, for example in strict privacy modes.
  }
}

export function getBusinessToolRequestToken() {
  return readSessionValue(BUSINESS_TOOL_REQUEST_TOKEN_KEY)
}

export function setBusinessToolRequestToken(token = '') {
  writeSessionValue(BUSINESS_TOOL_REQUEST_TOKEN_KEY, String(token || '').trim())
}

function withBusinessToolToken(headers = {}) {
  const token = getBusinessToolRequestToken()
  if (!token) return headers
  return { ...headers, [BUSINESS_TOOL_TOKEN_HEADER]: token }
}

function businessSceneHeaders(sceneType, headers = {}) {
  return BUSINESS_SCENES.has(sceneType) ? withBusinessToolToken(headers) : headers
}

async function fetchWithRetry(url, options = {}, maxRetries = 2) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, options)
      if (response.ok || attempt === maxRetries) return response
      // Retry on 5xx errors
      if (response.status >= 500) {
        await new Promise(r => setTimeout(r, 1000 * (attempt + 1)))
        continue
      }
      return response
    } catch (e) {
      if (attempt === maxRetries) throw e
      await new Promise(r => setTimeout(r, 1000 * (attempt + 1)))
    }
  }
}

/**
 * 会话管理
 */
export async function listSessions(limit = 50, offset = 0) {
  const response = await fetch(`${API_BASE}/sessions?limit=${limit}&offset=${offset}`)
  if (!response.ok) throw new Error('获取会话列表失败')
  return response.json()
}

export async function createSession(sessionId = null, sceneType = null) {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, scene_type: sceneType })
  })
  if (!response.ok) throw new Error('创建会话失败')
  return response.json()
}

export async function deleteSession(sessionId) {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`, { method: 'DELETE' })
  if (!response.ok) throw new Error('删除会话失败')
  return response.json()
}

export async function getSession(sessionId) {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`)
  if (!response.ok) throw new Error('获取会话失败')
  return response.json()
}

export async function updateSessionTitle(sessionId, title) {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/title`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  })
  if (!response.ok) throw new Error('更新标题失败')
  return response.json()
}

/**
 * 场景路由映射
 */
const SCENE_ROUTES = {
  risk_rule: 'risk_rule',
  model_card: 'model_card',
  simulation: 'simulation',
  profit: 'profit'
}

/**
 * 通用场景查询
 * @param {string} sceneType - 场景类型 (risk_rule, model_card, simulation, profit)
 * @param {Object} params - 查询参数
 */
export async function queryScene(sceneType, {
  query,
  session_id = null,
  top_k = 5,
  score_threshold = 0.7,
  clarification_choice = null,
  answer_perspective = null
}) {
  const route = SCENE_ROUTES[sceneType]
  if (!route) throw new Error(`未知场景类型: ${sceneType}`)

  const response = await fetchWithRetry(`${API_BASE}/${route}/query`, {
    method: 'POST',
    headers: businessSceneHeaders(sceneType, { 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      query,
      session_id,
      top_k,
      score_threshold,
      clarification_choice,
      answer_perspective
    })
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * 流式场景查询 (SSE)
 * @param {string} sceneType - 场景类型
 * @param {Object} params - 查询参数
 * @param {Object} callbacks - { onSources, onChunk, onDone, onError, onClarification, onProgress }
 */
export async function querySceneStream(
  sceneType,
  params,
  { onSources, onChunk, onDone, onError, onClarification, onProgress }
) {
  const route = SCENE_ROUTES[sceneType]
  if (!route) throw new Error(`未知场景类型: ${sceneType}`)

  try {
    const response = await fetch(`${API_BASE}/${route}/query-stream`, {
      method: 'POST',
      headers: businessSceneHeaders(sceneType, { 'Content-Type': 'application/json' }),
      body: JSON.stringify(params)
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '请求失败' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()

      let eventType = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (eventType === 'sources') onSources?.(data)
          else if (eventType === 'chunk') onChunk?.(data)
          else if (eventType === 'done') onDone?.(data)
          else if (eventType === 'clarification') onClarification?.(data)
          else if (eventType === 'progress') onProgress?.(data)
          else if (eventType === 'error') onError?.(data)
        }
      }
    }
  } catch (e) {
    onError?.({ error: e.message })
  }
}

/** @deprecated 使用 queryScene 代替 */
export const queryRiskRules = (params) => queryScene('risk_rule', params)
export const queryModelCards = (params) => queryScene('model_card', params)
export const querySimulation = (params) => queryScene('simulation', params)
export const queryProfit = (params) => queryScene('profit', params)

/**
 * 检查 API 健康状态
 * @returns {Promise<Object>} 健康状态
 */
export async function checkReady() {
  const response = await fetch(`${API_BASE}/ready`)
  if (!response.ok) {
    throw new Error('API 服务不可用')
  }
  return response.json()
}

/**
 * 检查 API 及依赖服务健康状态
 * @returns {Promise<Object>} 健康状态
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`)
  if (!response.ok) {
    throw new Error('API 服务不可用')
  }
  return response.json()
}

/**
 * 获取缓存统计信息
 */
export async function getCacheStats() {
  const response = await fetch(`${API_BASE}/cache/stats`)
  if (!response.ok) throw new Error('获取缓存状态失败')
  return response.json()
}

/**
 * 清除指定模式的缓存
 * @param {string|null} pattern - 缓存 key 模式
 * @param {string|null} sceneType - 场景类型 (risk_rule, model_card 等)
 */
export async function invalidateCache(pattern = null, sceneType = null) {
  const response = await fetch(`${API_BASE}/cache/invalidate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pattern, scene_type: sceneType })
  })
  if (!response.ok) throw new Error('清除缓存失败')
  return response.json()
}

/**
 * 清空所有缓存
 */
export async function clearAllCache() {
  const response = await fetch(`${API_BASE}/cache/clear`, { method: 'DELETE' })
  if (!response.ok) throw new Error('清空缓存失败')
  return response.json()
}

/**
 * 获取 LLM 配置
 */
export async function getLlmSettings() {
  const response = await fetch(`${API_BASE}/settings/`)
  if (!response.ok) throw new Error('获取配置失败')
  return response.json()
}

/**
 * 更新 LLM 配置
 * @param {Object} updates - 要更新的字段
 */
export async function updateLlmSettings(updates) {
  const response = await fetch(`${API_BASE}/settings/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  })
  if (!response.ok) throw new Error('更新配置失败')
  return response.json()
}

/**
 * 获取业务工具接口合同
 * @returns {Promise<Object>} 风控/毛利工具合同
 */
export async function getBusinessToolContracts() {
  const response = await fetch(`${API_BASE}/business-tools/contracts`)
  if (!response.ok) throw new Error('获取业务工具接口合同失败')
  return response.json()
}

/**
 * 获取业务工具运行态自检
 * @returns {Promise<Object>} 脱敏运行态摘要
 */
export async function getBusinessToolRuntimeStatus() {
  const response = await fetch(`${API_BASE}/business-tools/runtime-status`, {
    headers: withBusinessToolToken()
  })
  if (!response.ok) throw new Error('获取业务工具运行态失败')
  return response.json()
}

/**
 * 获取业务工具接入检查
 * @returns {Promise<Object>} 脱敏接入检查摘要
 */
export async function getBusinessToolReadiness(limit = 20) {
  const response = await fetch(`${API_BASE}/business-tools/readiness?limit=${limit}`, {
    headers: withBusinessToolToken()
  })
  if (!response.ok) throw new Error('获取业务工具接入检查失败')
  return response.json()
}

/**
 * 获取最近业务工具审计事件
 * @param {number} limit - 返回条数
 */
export async function getBusinessToolAuditEvents(limit = 20) {
  const response = await fetch(`${API_BASE}/business-tools/audit-events?limit=${limit}`, {
    headers: withBusinessToolToken()
  })
  if (!response.ok) throw new Error('获取业务工具审计事件失败')
  return response.json()
}

/**
 * 探测业务工具接口
 * @param {Object} params - 探测参数
 * @param {string} params.tool_name - 工具名称
 * @param {string} params.order_id - 订单号
 */
export async function probeBusinessTool({ tool_name, order_id }) {
  const response = await fetch(`${API_BASE}/business-tools/probe`, {
    method: 'POST',
    headers: withBusinessToolToken({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ tool_name, order_id })
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '接口探测失败' }))
    throw new Error(error.detail || '接口探测失败')
  }
  return response.json()
}

/**
 * 预检业务工具意图，不执行真实业务接口
 * @param {Object} params - 意图预检参数
 * @param {string} params.query - 用户问题
 * @param {string} params.scene_type - 场景类型
 */
export async function inspectBusinessToolIntent({ query, scene_type }) {
  const response = await fetch(`${API_BASE}/business-tools/intent`, {
    method: 'POST',
    headers: withBusinessToolToken({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ query, scene_type })
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '业务工具意图预检失败' }))
    throw new Error(error.detail || '业务工具意图预检失败')
  }
  return response.json()
}

/**
 * 离线校验业务工具响应样例
 * @param {Object} params - 校验参数
 * @param {string} params.tool_name - 工具名称
 * @param {Object} params.payload - 响应样例
 */
export async function validateBusinessToolResponse({ tool_name, payload }) {
  const response = await fetch(`${API_BASE}/business-tools/validate-response`, {
    method: 'POST',
    headers: withBusinessToolToken({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ tool_name, payload })
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '响应样例校验失败' }))
    throw new Error(error.detail || '响应样例校验失败')
  }
  return response.json()
}

/**
 * 批量离线校验业务工具响应样例
 * @param {Object} params - 批量校验参数
 * @param {string} params.tool_name - 工具名称
 * @param {Array<Object>} params.payloads - 响应样例列表
 */
export async function validateBusinessToolResponses({ tool_name, payloads }) {
  const response = await fetch(`${API_BASE}/business-tools/validate-responses`, {
    method: 'POST',
    headers: withBusinessToolToken({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ tool_name, payloads })
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '批量响应样例校验失败' }))
    throw new Error(error.detail || '批量响应样例校验失败')
  }
  return response.json()
}
