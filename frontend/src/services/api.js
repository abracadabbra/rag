/**
 * RAG API 服务
 */

const API_BASE = '/api/v1'

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
 * 发送风控规则查询
 * @param {Object} params - 查询参数
 * @param {string} params.query - 用户问题
 * @param {string|null} params.session_id - 会话ID
 * @param {number} params.top_k - 返回文档数量
 * @param {number} params.score_threshold - 相似度阈值
 * @param {string|null} params.clarification_choice - 澄清选项
 * @returns {Promise<Object>} 查询结果
 */
export async function queryRiskRules({
  query,
  session_id = null,
  top_k = 5,
  score_threshold = 0.7,
  clarification_choice = null
}) {
  const response = await fetch(`${API_BASE}/risk-rules/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query,
      session_id,
      top_k,
      score_threshold,
      clarification_choice
    })
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * 发送模型卡片查询
 * @param {Object} params - 查询参数
 * @param {string} params.query - 用户问题
 * @param {string|null} params.session_id - 会话ID
 * @param {number} params.top_k - 返回文档数量
 * @param {number} params.score_threshold - 相似度阈值
 * @param {string|null} params.clarification_choice - 澄清选项
 * @returns {Promise<Object>} 查询结果
 */
export async function queryModelCards({
  query,
  session_id = null,
  top_k = 5,
  score_threshold = 0.7,
  clarification_choice = null
}) {
  const response = await fetch(`${API_BASE}/model-cards/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query,
      session_id,
      top_k,
      score_threshold,
      clarification_choice
    })
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

/**
 * 发送仿真解读查询
 */
export async function querySimulation({
  query,
  session_id = null,
  top_k = 5,
  score_threshold = 0.7,
  clarification_choice = null
}) {
  const response = await fetch(`${API_BASE}/simulation/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, session_id, top_k, score_threshold, clarification_choice })
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 发送毛利抽成查询
 */
export async function queryProfit({
  query,
  session_id = null,
  top_k = 5,
  score_threshold = 0.7,
  clarification_choice = null
}) {
  const response = await fetch(`${API_BASE}/profit/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, session_id, top_k, score_threshold, clarification_choice })
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

/**
 * 检查 API 健康状态
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
