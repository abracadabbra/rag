/**
 * RAG API 服务
 */

const API_BASE = '/api/v1'

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
