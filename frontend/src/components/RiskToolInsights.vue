<template>
  <div v-if="hasRiskEvidence" :id="panelId" class="risk-evidence">
    <div v-if="riskExecutiveSummary()" class="risk-summary-card">
      <div class="risk-summary-head">
        <span>风控结论</span>
        <strong :class="riskDecisionTone()">
          {{ riskDecisionLabel() }}
        </strong>
      </div>
      <p>{{ riskExecutiveSummary().summary }}</p>
      <div
        v-if="riskExecutiveSummary().signals?.length"
        class="risk-signal-list"
      >
        <span
          v-for="signal in riskExecutiveSummary().signals"
          :key="signal"
          class="risk-signal-chip"
        >
          {{ signal }}
        </span>
      </div>
    </div>
    <div v-if="riskEvidenceMeter" class="risk-evidence-meter">
      <div class="risk-meter-top">
        <span>证据完整度</span>
        <strong>{{ riskEvidenceMeter.coverageLabel }}</strong>
      </div>
      <div class="risk-meter-bar" aria-hidden="true">
        <span :style="{ width: riskEvidenceMeter.coveragePercent + '%' }"></span>
      </div>
      <div class="risk-meter-grid">
        <span
          v-for="item in riskEvidenceMeter.items"
          :key="item.label"
          :class="['risk-meter-item', item.ready ? 'ready' : 'missing']"
        >
          <strong>{{ item.label }}</strong>{{ item.value }}
        </span>
      </div>
    </div>
    <div class="risk-evidence-title">命中规则证据</div>
    <template v-if="riskRules().length">
      <div
        v-for="(rule, ruleIndex) in riskRules()"
        :key="rule.rule_id || rule.rule_name || ruleIndex"
        class="risk-rule-item"
      >
        <div class="risk-rule-head">
          <span class="risk-rule-name">{{ rule.rule_name || '未命名规则' }}</span>
          <span v-if="rule.rule_id" class="risk-rule-id">{{ rule.rule_id }}</span>
        </div>
        <p v-if="rule.evidence" class="risk-rule-evidence">{{ rule.evidence }}</p>
      </div>
    </template>
    <div v-else class="risk-rule-empty">
      当前接口未返回命中规则，按系统决策、风险分和建议动作解释。
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  call: { type: Object, required: true },
  panelId: { type: String, default: '' },
})

const hasRiskEvidence = computed(() => {
  if (props.call?.name !== 'get_risk_event_detail') return false
  return Boolean(riskExecutiveSummary() || riskEvidenceMeter.value || riskRules().length)
})

const riskEvidenceMeter = computed(() => buildRiskEvidenceMeter())

function riskRules() {
  const rules = props.call?.result?.hit_rules
  return Array.isArray(rules) ? rules.filter(rule => rule && (rule.rule_name || rule.evidence)) : []
}

function riskExecutiveSummary() {
  const result = props.call?.result || {}
  const decision = result.decision
  const riskScore = result.risk_score
  const riskLevel = result.risk_level
  const recommendedAction = result.recommended_action

  if (!decision && !isNumber(riskScore) && !riskLevel && !recommendedAction) {
    return null
  }

  return {
    summary: riskSummaryText(),
    signals: riskSummarySignals(),
  }
}

function riskSummaryText() {
  const result = props.call?.result || {}
  const parts = []
  if (result.decision) parts.push(`系统决策为 ${formatRiskDecision(result.decision)}`)
  if (isNumber(result.risk_score)) parts.push(`风险分 ${result.risk_score}`)
  if (result.risk_level) parts.push(`风险等级 ${formatRiskLevel(result.risk_level)}`)
  if (result.recommended_action) parts.push(`建议动作：${result.recommended_action}`)
  return parts.join('，')
}

function riskSummarySignals() {
  const result = props.call?.result || {}
  const rules = riskRules()
  const signals = []

  if (rules.length) signals.push(`命中 ${rules.length} 条规则`)
  if (isNumber(result.risk_score) && result.risk_score >= 80) signals.push('高风险分，需要优先关注')
  if (result.risk_level === 'low') signals.push('低风险等级，可结合规则证据复核')
  if (result.recommended_action) signals.push(`处置建议：${result.recommended_action}`)
  return signals
}

function buildRiskEvidenceMeter() {
  const result = props.call?.result || {}
  const rules = riskRules()
  const requiredItems = [
    {
      label: '决策',
      value: result.decision ? formatRiskDecision(result.decision) : '缺失',
      ready: Boolean(result.decision),
    },
    {
      label: '评分',
      value: isNumber(result.risk_score) ? result.risk_score : '缺失',
      ready: isNumber(result.risk_score),
    },
    {
      label: '等级',
      value: result.risk_level ? formatRiskLevel(result.risk_level) : '缺失',
      ready: Boolean(result.risk_level),
    },
    {
      label: '规则',
      value: rules.length ? `${rules.length} 条` : '未命中',
      ready: rules.length > 0,
    },
    {
      label: '动作',
      value: result.recommended_action || '缺失',
      ready: Boolean(result.recommended_action),
    },
  ]
  const readyCount = requiredItems.filter(item => item.ready).length
  if (!readyCount) return null

  return {
    coverageLabel: `${readyCount}/${requiredItems.length}`,
    coveragePercent: Math.round((readyCount / requiredItems.length) * 100),
    items: [
      ...requiredItems,
      {
        label: '来源',
        value: formatDataSource(props.call?.data_source),
        ready: Boolean(props.call?.data_source),
      },
    ],
  }
}

function riskDecisionLabel() {
  const result = props.call?.result || {}
  if (result.decision) return formatRiskDecision(result.decision)
  if (result.risk_level) return formatRiskLevel(result.risk_level)
  return '待判断'
}

function riskDecisionTone() {
  const decision = String(props.call?.result?.decision || '').toLowerCase()
  const riskLevel = String(props.call?.result?.risk_level || '').toLowerCase()
  const riskScore = props.call?.result?.risk_score

  if (decision === 'block' || riskLevel === 'high' || (isNumber(riskScore) && riskScore >= 80)) {
    return 'high'
  }
  if (decision === 'review' || riskLevel === 'medium' || (isNumber(riskScore) && riskScore >= 50)) {
    return 'medium'
  }
  return 'low'
}

function formatRiskDecision(value) {
  const normalized = String(value || '').toLowerCase()
  if (normalized === 'block') return '建议拦截'
  if (normalized === 'review') return '建议复核'
  if (normalized === 'allow' || normalized === 'pass') return '建议放行'
  return value || '待判断'
}

function formatRiskLevel(value) {
  const normalized = String(value || '').toLowerCase()
  if (normalized === 'high') return '高'
  if (normalized === 'medium') return '中'
  if (normalized === 'low') return '低'
  return value || '未知'
}

function formatDataSource(value) {
  if (value === 'http') return '真实接口'
  if (value === 'mock') return 'Mock 数据'
  return value || '未知'
}

function isNumber(value) {
  return typeof value === 'number' && Number.isFinite(value)
}
</script>

<style scoped>
.risk-evidence {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border-subtle);
}

.risk-summary-card {
  margin-bottom: 8px;
  padding: 9px 10px;
  border: 1px solid rgba(239, 68, 68, 0.16);
  border-radius: 7px;
  background: rgba(239, 68, 68, 0.05);
}

.risk-summary-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.risk-summary-head span {
  color: var(--text-muted);
  font-size: 10px;
  font-family: var(--font-display);
}

.risk-summary-head strong {
  font-size: 11px;
  font-weight: 600;
}

.risk-summary-head strong.high {
  color: #f87171;
}

.risk-summary-head strong.medium {
  color: #f59e0b;
}

.risk-summary-head strong.low {
  color: #10b981;
}

.risk-summary-card p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.55;
}

.risk-signal-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.risk-signal-chip {
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(239, 68, 68, 0.12);
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 11px;
  line-height: 1.35;
}

.risk-evidence-meter {
  margin-bottom: 9px;
  padding: 9px 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.035);
}

.risk-meter-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 7px;
}

.risk-meter-top span {
  color: var(--text-muted);
  font-size: 10px;
  font-family: var(--font-display);
}

.risk-meter-top strong {
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
}

.risk-meter-bar {
  height: 4px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
}

.risk-meter-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #f87171, #f59e0b, #10b981);
}

.risk-meter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(92px, 1fr));
  gap: 6px;
  margin-top: 8px;
}

.risk-meter-item {
  min-width: 0;
  color: var(--text-muted);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 6px;
  padding: 6px 7px;
  font-size: 11px;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.risk-meter-item strong {
  display: block;
  color: var(--text-secondary);
  font-size: 10px;
  font-weight: 600;
  margin-bottom: 2px;
}

.risk-meter-item.missing {
  opacity: 0.72;
}

.risk-evidence-title {
  color: var(--text-muted);
  font-size: 11px;
  margin-bottom: 8px;
  font-family: var(--font-display);
}

.risk-rule-item {
  padding: 8px 10px;
  border: 1px solid rgba(239, 68, 68, 0.16);
  border-radius: 7px;
  background: rgba(239, 68, 68, 0.06);
}

.risk-rule-item + .risk-rule-item {
  margin-top: 7px;
}

.risk-rule-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
}

.risk-rule-name {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  min-width: 0;
  overflow-wrap: anywhere;
}

.risk-rule-id {
  flex: 0 0 auto;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 10px;
}

.risk-rule-evidence {
  margin: 5px 0 0;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.risk-rule-empty {
  padding: 8px 10px;
  color: var(--text-muted);
  border: 1px dashed rgba(255, 255, 255, 0.12);
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.025);
  font-size: 12px;
  line-height: 1.55;
}
</style>
