<template>
  <div>
    <div v-if="showToolIntent" class="tool-intent-card">
      <div class="tool-intent-top">
        <div class="tool-intent-heading">
          <span class="tool-intent-title">{{ toolIntent.label || toolIntent.tool_name }}</span>
          <code class="tool-intent-name">{{ toolIntent.tool_name }}</code>
        </div>
        <div class="tool-intent-badges">
          <span :class="['tool-intent-state', toolIntentStateTone(toolIntent)]">
            {{ toolIntentStateLabel(toolIntent) }}
          </span>
          <span class="tool-intent-confidence">{{ formatConfidence(toolIntent.confidence) }}</span>
        </div>
      </div>
      <div class="tool-intent-grid">
        <span>
          <strong>选择来源</strong>{{ formatSelectionSource(toolIntent.selection_source) }}
        </span>
        <span v-if="toolIntent.order_id">
          <strong>订单号</strong>{{ toolIntent.order_id }}
        </span>
        <span>
          <strong>下一状态</strong>{{ toolIntentActionHint(toolIntent) }}
        </span>
      </div>
      <p v-if="toolIntent.reason" class="tool-intent-reason">
        <strong>命中依据</strong>{{ toolIntent.reason }}
      </p>
      <div v-if="toolIntent.missing_fields?.length" class="tool-intent-missing">
        <span>缺少字段</span>
        <div class="tool-intent-chip-list">
          <strong
            v-for="field in toolIntent.missing_fields"
            :key="field"
            class="tool-intent-chip"
          >
            {{ formatIntentMissingField(field) }}
          </strong>
        </div>
      </div>
      <div
        v-if="toolIntent.needs_clarification && toolIntent.clarification_options?.length"
        class="tool-intent-next"
      >
        <span>建议补充</span>
        <strong>{{ toolIntent.clarification_options[0] }}</strong>
      </div>
    </div>

    <div v-if="decisionTimeline.length" class="tool-decision-track">
      <div class="tool-decision-head">工具决策时间线</div>
      <div class="tool-decision-list">
        <div
          v-for="item in decisionTimeline"
          :key="item.key"
          class="tool-decision-item"
          :class="item.tone"
        >
          <div class="tool-decision-marker">
            <span></span>
          </div>
          <div class="tool-decision-body">
            <div class="tool-decision-title">
              <strong>{{ item.title }}</strong>
              <em>{{ item.state }}</em>
            </div>
            <p>{{ item.detail }}</p>
            <div v-if="item.targets?.length" class="tool-decision-actions">
              <button
                v-for="target in item.targets"
                :key="target.id"
                type="button"
                class="tool-decision-action"
                @click="jumpToTarget(target.id)"
              >
                {{ target.label }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="toolCalls.length" class="tool-call-list">
      <div class="tool-call-header">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M5.2 8.8L2.7 6.3a2.5 2.5 0 013.5-3.5l.8.8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          <path d="M8.8 5.2l2.5 2.5a2.5 2.5 0 01-3.5 3.5l-.8-.8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          <path d="M5.5 8.5l3-3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        <span>系统接口调用</span>
      </div>
      <div v-for="call in toolCalls" :key="call.name" class="tool-call-item">
        <div class="tool-call-top">
          <span class="tool-name">{{ call.label || call.name }}</span>
          <div class="tool-call-meta">
            <span v-if="call.duration_ms !== undefined && call.duration_ms !== null" class="tool-duration">
              {{ call.duration_ms }}ms
            </span>
            <span :class="['tool-status', call.status]">
              {{ call.status === 'success' ? '成功' : '失败' }}
            </span>
          </div>
        </div>
        <p class="tool-summary">{{ call.summary }}</p>
        <div v-if="call.selection_reason || call.confidence !== undefined" class="tool-selection">
          <span v-if="call.selection_source">来源 {{ formatSelectionSource(call.selection_source) }}</span>
          <span v-if="call.selection_reason">{{ call.selection_reason }}</span>
          <span v-if="call.confidence !== undefined && call.confidence !== null">
            置信度 {{ formatConfidence(call.confidence) }}
          </span>
        </div>
        <div class="tool-fields">
          <span
            v-for="field in toolFields(call)"
            :key="field.label"
            class="tool-field"
          >
            <strong>{{ field.label }}</strong>{{ field.value }}
          </span>
        </div>
        <div v-if="call.status === 'error'" class="tool-degrade">
          <div class="tool-degrade-title">接口降级提示</div>
          <div class="tool-degrade-grid">
            <span>
              <strong>审计ID</strong>{{ call.audit_id || '-' }}
            </span>
            <span>
              <strong>错误类型</strong>{{ call.error_type || '未返回' }}
            </span>
            <span v-if="call.diagnostic_code">
              <strong>合同诊断</strong>{{ formatDiagnosticCode(call.diagnostic_code) }}
            </span>
            <span v-if="call.missing_fields?.length">
              <strong>缺失字段</strong>{{ call.missing_fields.join('、') }}
            </span>
            <span v-if="call.invalid_fields?.length">
              <strong>异常字段</strong>{{ call.invalid_fields.join('、') }}
            </span>
            <span>
              <strong>建议动作</strong>稍后重试，或在 API 设置中使用接口探测和响应样例校验。
            </span>
          </div>
          <p v-if="call.diagnostic" class="tool-degrade-diagnostic">
            {{ call.diagnostic }}
          </p>
        </div>

        <ProfitToolInsights :call="call" :anchor-prefix="callAnchorPrefix(call)" />
        <RiskToolInsights :call="call" :panel-id="riskEvidenceAnchorId(call)" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ProfitToolInsights from './ProfitToolInsights.vue'
import RiskToolInsights from './RiskToolInsights.vue'

const props = defineProps({
  toolCalls: { type: Array, default: () => [] },
  toolIntent: { type: Object, default: null },
})

const showToolIntent = computed(() => {
  const intent = props.toolIntent
  return Boolean(intent?.tool_name)
})

const primaryCall = computed(() => props.toolCalls?.[0] || null)

const decisionTimeline = computed(() => buildDecisionTimeline(props.toolIntent, primaryCall.value))

function toolIntentStateLabel(intent) {
  if (props.toolCalls?.length) return '已执行'
  if (intent?.needs_clarification) return '待澄清'
  return '待执行'
}

function toolIntentStateTone(intent) {
  if (props.toolCalls?.length) return 'executed'
  if (intent?.needs_clarification) return 'pending'
  return 'ready'
}

function toolIntentActionHint(intent) {
  const missingFields = intent?.missing_fields || []
  if (missingFields.includes('tool_intent_confirmation')) {
    return '等待你确认后再调用接口'
  }
  if (missingFields.includes('order_id')) {
    return '等待补充订单号'
  }
  if (props.toolCalls?.length) {
    return '已进入接口执行'
  }
  return '已完成预判'
}

function formatIntentMissingField(value) {
  if (value === 'order_id') return '订单号'
  if (value === 'tool_intent_confirmation') return '执行确认'
  return value
}

function buildDecisionTimeline(intent, call) {
  if (!intent?.tool_name && !call?.name) return []

  const toolLabel = intent?.label || call?.label || call?.name || intent?.tool_name || '业务接口'
  const missingFields = intent?.missing_fields || []
  const targets = buildEvidenceTargets(call)
  const steps = [
    {
      key: 'intent',
      title: '意图识别',
      state: '已识别',
      tone: 'done',
      detail: `${toolLabel} · ${formatSelectionSource(intent?.selection_source || call?.selection_source || 'none')}`,
    },
  ]

  if (missingFields.length || intent?.needs_clarification) {
    steps.push({
      key: 'clarify',
      title: '信息补齐',
      state: '等待输入',
      tone: 'waiting',
      detail: missingFields.length
        ? `待补充：${missingFields.map(formatIntentMissingField).join('、')}`
        : '等待继续确认后再发起调用',
    })
  } else {
    steps.push({
      key: 'clarify',
      title: '信息补齐',
      state: '已就绪',
      tone: 'done',
      detail: intent?.order_id ? `订单号 ${intent.order_id} 已进入执行条件` : '执行条件已满足',
    })
  }

  if (call?.name) {
    steps.push({
      key: 'execute',
      title: '接口执行',
      state: call.status === 'success' ? '执行成功' : '执行失败',
      tone: call.status === 'success' ? 'done' : 'error',
      detail: `${formatDataSource(call.data_source)} · ${call.endpoint_path || toolLabel}`,
    })
    steps.push({
      key: 'result',
      title: '结果返回',
      state: call.status === 'success' ? '已返回' : '已降级',
      tone: call.status === 'success' ? 'done' : 'error',
      detail: call.summary || '接口已返回结构化数据',
      targets,
    })
    return steps
  }

  steps.push({
    key: 'execute',
    title: '接口执行',
    state: '待执行',
    tone: 'idle',
    detail: intent?.needs_clarification ? '补齐后会自动进入接口调用' : '已完成预判，等待执行',
  })
  steps.push({
    key: 'result',
    title: '结果返回',
    state: '未返回',
    tone: 'idle',
    detail: '当前还没有订单级结构化数据返回',
  })
  return steps
}

function buildEvidenceTargets(call) {
  if (!call?.name) return []
  if (call.name === 'get_profit_chain_detail') {
    const targets = []
    const result = call.result || {}
    if (Array.isArray(result.chain) && result.chain.length) {
      targets.push({
        id: `${callAnchorPrefix(call)}-chain`,
        label: '查看钱流链路',
      })
    }
    if (
      [result.gross_amount, result.platform_commission, result.driver_income, result.platform_net_profit]
        .some(value => typeof value === 'number' && Number.isFinite(value))
    ) {
      targets.push({
        id: `${callAnchorPrefix(call)}-analysis`,
        label: '查看毛利拆解',
      })
    }
    return targets
  }
  if (call.name === 'get_risk_event_detail') {
    const rules = call.result?.hit_rules
    if (Array.isArray(rules) && rules.length) {
      return [{
        id: riskEvidenceAnchorId(call),
        label: '查看命中证据',
      }]
    }
  }
  return []
}

function callAnchorPrefix(call) {
  return call?.audit_id || call?.name || 'tool-call'
}

function riskEvidenceAnchorId(call) {
  const prefix = callAnchorPrefix(call)
  return prefix ? `${prefix}-risk` : ''
}

function jumpToTarget(targetId) {
  if (!targetId) return
  const element = document.getElementById(targetId)
  if (!element) return
  element.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
}

function toolFields(call) {
  const result = call?.result || {}
  const args = call?.arguments || {}

  if (call?.name === 'get_risk_event_detail') {
    return [
      { label: '数据源', value: formatDataSource(call.data_source) },
      { label: '模式', value: formatIntegrationMode(call.integration_mode) },
      { label: '合同版本', value: call.contract_version },
      { label: '接口模板', value: call.endpoint_template },
      { label: '接口', value: call.endpoint_path },
      { label: '审计ID', value: call.audit_id },
      { label: '订单', value: result.order_id || args.order_id },
      { label: '决策', value: result.decision },
      { label: '风险分', value: result.risk_score },
      { label: '等级', value: result.risk_level },
    ].filter(field => field.value !== undefined && field.value !== null && field.value !== '')
  }

  if (call?.name === 'get_profit_chain_detail') {
    return [
      { label: '数据源', value: formatDataSource(call.data_source) },
      { label: '模式', value: formatIntegrationMode(call.integration_mode) },
      { label: '合同版本', value: call.contract_version },
      { label: '接口模板', value: call.endpoint_template },
      { label: '接口', value: call.endpoint_path },
      { label: '审计ID', value: call.audit_id },
      { label: '订单', value: result.order_id || args.order_id },
      { label: '总金额', value: formatMoney(result.gross_amount) },
      { label: '平台抽成', value: formatMoney(result.platform_commission) },
      { label: '司机收入', value: formatMoney(result.driver_income) },
      { label: '净毛利', value: formatMoney(result.platform_net_profit) },
      { label: '链路来源', value: formatChainSource(result.chain_source) },
    ].filter(field => field.value !== undefined && field.value !== null && field.value !== '')
  }

  return Object.entries(args).map(([label, value]) => ({ label, value }))
}

function formatDataSource(value) {
  if (value === 'http') return '真实接口'
  if (value === 'mock') return 'Mock 数据'
  return value
}

function formatSelectionSource(value) {
  if (value === 'rules') return '规则命中'
  if (value === 'llm') return 'LLM 兜底'
  if (value === 'probe') return '手动探测'
  if (value === 'none') return '未触发'
  return value || '未知'
}

function formatIntegrationMode(value) {
  if (value === 'external_http') return '外部真实 HTTP'
  if (value === 'fake_http') return '进程内 fake-http 验证'
  if (value === 'mock') return 'Mock 模式'
  return value
}

function formatMoney(value) {
  if (typeof value !== 'number') return value
  return `${value.toFixed(2)} 元`
}

function formatChainSource(value) {
  if (value === 'api') return '接口原生链路'
  if (value === 'derived') return '自动派生链路'
  return value
}

function formatDiagnosticCode(value) {
  const labels = {
    missing_required_fields: '缺少必填字段',
    invalid_field_types: '字段类型不匹配',
    invalid_hit_rules: '命中规则结构异常',
    invalid_chain: '毛利链路结构异常',
    invalid_json: 'JSON 无法解析',
    non_object_json: '响应不是对象',
  }
  return labels[value] || value
}

function formatConfidence(value) {
  if (typeof value !== 'number') return value ?? ''
  return `${Math.round(value * 100)}%`
}
</script>

<style scoped>
.tool-intent-card {
  margin-top: 10px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 10px 12px;
}

.tool-intent-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.tool-intent-heading {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tool-intent-title {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
}

.tool-intent-name {
  width: fit-content;
  max-width: 100%;
  color: var(--text-muted);
  background: var(--bg-elevated);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 10px;
  overflow-wrap: anywhere;
}

.tool-intent-badges {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.tool-intent-state {
  font-size: 11px;
  border-radius: 4px;
  padding: 2px 6px;
  background: var(--bg-elevated);
  color: var(--text-muted);
}

.tool-intent-state.executed {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.tool-intent-state.pending {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
}

.tool-intent-state.ready {
  color: #60a5fa;
  background: rgba(96, 165, 250, 0.12);
}

.tool-intent-confidence {
  color: var(--text-muted);
  background: var(--bg-elevated);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 11px;
  flex-shrink: 0;
}

.tool-intent-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.tool-intent-grid span,
.tool-intent-reason {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.tool-intent-grid span {
  background: var(--bg-elevated);
  border-radius: 4px;
  padding: 4px 8px;
}

.tool-intent-grid strong,
.tool-intent-reason strong,
.tool-intent-next span,
.tool-intent-missing span {
  color: var(--text-muted);
  margin-right: 6px;
  font-weight: 600;
}

.tool-intent-reason {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
  margin: 0 0 8px;
}

.tool-intent-missing {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 6px;
  color: var(--text-muted);
  font-size: 11px;
}

.tool-intent-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tool-intent-chip {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
  border-radius: 4px;
  padding: 4px 8px;
  font-weight: 600;
}

.tool-intent-next {
  margin-top: 8px;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  padding: 7px 8px;
  font-size: 11px;
  line-height: 1.5;
}

.tool-call-list {
  margin-top: 10px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 12px 14px;
}

.tool-decision-track {
  margin-top: 10px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 12px 14px;
}

.tool-decision-head {
  color: var(--text-muted);
  font-size: 12px;
  font-family: var(--font-display);
  margin-bottom: 10px;
}

.tool-decision-list {
  display: grid;
  gap: 8px;
}

.tool-decision-item {
  display: grid;
  grid-template-columns: 14px minmax(0, 1fr);
  gap: 10px;
  align-items: start;
}

.tool-decision-marker {
  position: relative;
  min-height: 100%;
  display: flex;
  justify-content: center;
}

.tool-decision-marker::after {
  content: '';
  position: absolute;
  top: 14px;
  bottom: -8px;
  width: 1px;
  background: var(--border-subtle);
}

.tool-decision-item:last-child .tool-decision-marker::after {
  display: none;
}

.tool-decision-marker span {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  margin-top: 4px;
  background: var(--text-muted);
  border: 2px solid rgba(255, 255, 255, 0.08);
}

.tool-decision-item.done .tool-decision-marker span {
  background: #10b981;
}

.tool-decision-item.waiting .tool-decision-marker span {
  background: #f59e0b;
}

.tool-decision-item.error .tool-decision-marker span {
  background: #ef4444;
}

.tool-decision-item.idle .tool-decision-marker span {
  background: #64748b;
}

.tool-decision-body {
  min-width: 0;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 8px 10px;
}

.tool-decision-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 4px;
}

.tool-decision-title strong {
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 600;
}

.tool-decision-title em {
  font-style: normal;
  color: var(--text-muted);
  background: var(--bg-elevated);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 10px;
  flex-shrink: 0;
}

.tool-decision-item.done .tool-decision-title em {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.tool-decision-item.waiting .tool-decision-title em {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
}

.tool-decision-item.error .tool-decision-title em {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.12);
}

.tool-decision-item.idle .tool-decision-title em {
  color: #94a3b8;
}

.tool-decision-body p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 11px;
  line-height: 1.5;
}

.tool-decision-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.tool-decision-action {
  border: 1px solid var(--border-subtle);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 11px;
  line-height: 1.35;
  cursor: pointer;
}

.tool-decision-action:hover {
  color: var(--text-primary);
  border-color: rgba(34, 211, 238, 0.22);
}

.tool-call-header {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 12px;
  font-family: var(--font-display);
  margin-bottom: 10px;
}

.tool-call-item {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 10px 12px;
}

.tool-call-item + .tool-call-item {
  margin-top: 8px;
}

.tool-call-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.tool-call-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.tool-name {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
}

.tool-duration {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  background: var(--bg-elevated);
  border-radius: 4px;
  padding: 2px 6px;
}

.tool-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--text-muted);
  background: var(--bg-elevated);
}

.tool-status.success {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.tool-status.error {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.tool-summary {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.5;
  margin: 0 0 8px;
}

.tool-selection {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.45;
  margin: 0 0 8px;
}

.tool-selection span {
  background: var(--bg-elevated);
  border-radius: 4px;
  padding: 3px 6px;
}

.tool-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tool-field {
  color: var(--text-muted);
  background: var(--bg-elevated);
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 11px;
}

.tool-field strong {
  color: var(--text-secondary);
  margin-right: 5px;
  font-weight: 600;
}

.tool-degrade {
  margin-top: 8px;
  padding: 9px 10px;
  border: 1px solid rgba(239, 68, 68, 0.18);
  border-radius: 7px;
  background: rgba(239, 68, 68, 0.055);
}

.tool-degrade-title {
  color: #f87171;
  font-size: 11px;
  font-family: var(--font-display);
  font-weight: 600;
  margin-bottom: 7px;
}

.tool-degrade-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  gap: 6px;
}

.tool-degrade-grid span {
  min-width: 0;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid rgba(239, 68, 68, 0.12);
  border-radius: 6px;
  padding: 6px 7px;
  font-size: 11px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.tool-degrade-grid strong {
  display: block;
  color: var(--text-secondary);
  font-size: 10px;
  font-weight: 600;
  margin-bottom: 2px;
}

.tool-degrade-diagnostic {
  margin: 7px 0 0;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid rgba(239, 68, 68, 0.12);
  border-radius: 6px;
  padding: 7px 8px;
  font-size: 11px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}
</style>
