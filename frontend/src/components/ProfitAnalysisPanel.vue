<template>
  <div :id="panelId" class="profit-analysis">
    <div class="profit-analysis-head">
      <span>毛利拆解</span>
      <strong :class="analysis.toneClass">
        {{ analysis.toneLabel }}
      </strong>
    </div>
    <div v-if="analysis.summary" class="profit-summary-card">
      <div class="profit-summary-head">
        <span>业务结论</span>
        <strong>{{ analysis.summary.headline }}</strong>
      </div>
      <p>{{ analysis.summary.summary }}</p>
      <div
        v-if="analysis.summary.drivers?.length"
        class="profit-driver-list"
      >
        <span
          v-for="driver in analysis.summary.drivers"
          :key="driver"
          class="profit-driver-chip"
        >
          {{ driver }}
        </span>
      </div>
    </div>
    <div class="profit-kpi-grid">
      <div
        v-for="metric in analysis.metrics"
        :key="metric.label"
        class="profit-kpi"
        :class="metric.tone"
      >
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <em v-if="metric.hint">{{ metric.hint }}</em>
      </div>
    </div>
    <div v-if="analysis.equationParts.length" class="profit-equation">
      <div class="profit-equation-title">毛利公式</div>
      <div class="profit-equation-row">
        <template
          v-for="(part, partIndex) in analysis.equationParts"
          :key="part.label"
        >
          <span
            v-if="partIndex > 0"
            class="profit-equation-operator"
          >
            {{ part.operator }}
          </span>
          <span class="profit-equation-part" :class="part.tone">
            <span>{{ part.label }}</span>
            <strong>{{ part.value }}</strong>
          </span>
        </template>
      </div>
    </div>
    <div class="profit-ledger">
      <div
        v-for="row in analysis.ledgerRows"
        :key="row.label"
        class="profit-ledger-row"
        :class="row.tone"
      >
        <span>{{ row.label }}</span>
        <strong>{{ row.value }}</strong>
      </div>
    </div>
    <div v-if="analysis.signals.length" class="profit-signals">
      <span
        v-for="signal in analysis.signals"
        :key="signal"
        class="profit-signal"
      >
        {{ signal }}
      </span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  analysis: { type: Object, required: true },
  panelId: { type: String, default: '' },
})
</script>

<style scoped>
.profit-analysis {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border-subtle);
}

.profit-analysis-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
  color: var(--text-muted);
  font-size: 11px;
  font-family: var(--font-display);
}

.profit-analysis-head strong {
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 600;
}

.profit-analysis-head strong.healthy {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.profit-analysis-head strong.warning {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
}

.profit-analysis-head strong.loss {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.profit-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(112px, 1fr));
  gap: 8px;
}

.profit-summary-card {
  margin-bottom: 8px;
  padding: 9px 10px;
  border: 1px solid rgba(34, 211, 238, 0.16);
  border-radius: 7px;
  background: rgba(34, 211, 238, 0.04);
}

.profit-summary-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.profit-summary-head span {
  color: var(--text-muted);
  font-size: 10px;
  font-family: var(--font-display);
}

.profit-summary-head strong {
  color: #22d3ee;
  font-size: 11px;
  font-weight: 600;
}

.profit-summary-card p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.55;
}

.profit-driver-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.profit-driver-chip {
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-subtle);
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 11px;
  line-height: 1.35;
}

.profit-kpi {
  min-width: 0;
  border: 1px solid var(--border-subtle);
  border-radius: 7px;
  padding: 8px 9px;
  background: var(--bg-elevated);
}

.profit-kpi span,
.profit-kpi strong,
.profit-kpi em {
  display: block;
}

.profit-kpi span {
  color: var(--text-muted);
  font-size: 10px;
  margin-bottom: 3px;
}

.profit-kpi strong {
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.profit-kpi em {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 10px;
  font-style: normal;
}

.profit-kpi.income {
  border-color: rgba(16, 185, 129, 0.18);
  background: rgba(16, 185, 129, 0.06);
}

.profit-kpi.net {
  border-color: rgba(34, 211, 238, 0.18);
  background: rgba(34, 211, 238, 0.06);
}

.profit-kpi.loss {
  border-color: rgba(239, 68, 68, 0.2);
  background: rgba(239, 68, 68, 0.08);
}

.profit-equation {
  margin-top: 8px;
  padding: 8px;
  border: 1px solid rgba(34, 211, 238, 0.14);
  border-radius: 7px;
  background: rgba(34, 211, 238, 0.035);
}

.profit-equation-title {
  color: var(--text-muted);
  font-size: 10px;
  margin-bottom: 6px;
  font-family: var(--font-display);
}

.profit-equation-row {
  display: flex;
  align-items: stretch;
  gap: 5px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.profit-equation-operator {
  flex: 0 0 auto;
  align-self: center;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
}

.profit-equation-part {
  flex: 0 0 auto;
  min-width: 84px;
  padding: 6px 7px;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.025);
}

.profit-equation-part span,
.profit-equation-part strong {
  display: block;
  white-space: nowrap;
}

.profit-equation-part span {
  color: var(--text-muted);
  font-size: 10px;
  margin-bottom: 2px;
}

.profit-equation-part strong {
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
}

.profit-equation-part.income {
  border-color: rgba(16, 185, 129, 0.18);
  background: rgba(16, 185, 129, 0.06);
}

.profit-equation-part.cost {
  border-color: rgba(245, 158, 11, 0.18);
  background: rgba(245, 158, 11, 0.06);
}

.profit-equation-part.net {
  border-color: rgba(34, 211, 238, 0.2);
  background: rgba(34, 211, 238, 0.07);
}

.profit-equation-part.loss {
  border-color: rgba(239, 68, 68, 0.2);
  background: rgba(239, 68, 68, 0.08);
}

.profit-equation-part.income strong {
  color: #10b981;
}

.profit-equation-part.cost strong {
  color: #f59e0b;
}

.profit-equation-part.net strong {
  color: #22d3ee;
}

.profit-equation-part.loss strong {
  color: #ef4444;
}

.profit-ledger {
  margin-top: 8px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(104px, 1fr));
  gap: 6px;
}

.profit-ledger-row {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 7px 8px;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid var(--border-subtle);
}

.profit-ledger-row span {
  color: var(--text-muted);
  font-size: 10px;
}

.profit-ledger-row strong {
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.profit-ledger-row.income strong,
.profit-ledger-row.net strong {
  color: #10b981;
}

.profit-ledger-row.cost strong {
  color: #f59e0b;
}

.profit-signals {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.profit-signal {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.16);
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 11px;
  line-height: 1.35;
}
</style>
