<template>
  <div :id="panelId" class="profit-chain">
    <div class="profit-chain-head">
      <div class="profit-chain-title">订单钱流链路</div>
      <span v-if="chainView.sourceLabel" class="profit-chain-source">
        {{ chainView.sourceLabel }}
      </span>
    </div>
    <div class="profit-chain-summary">
      <span>毛利口径说明</span>
      <p>{{ chainView.summary }}</p>
    </div>
    <div v-if="chainView.formulaAudit" class="profit-formula-audit">
      <div class="formula-audit-head">
        <span>公式核对</span>
        <strong :class="chainView.formulaAudit.tone">
          {{ chainView.formulaAudit.statusLabel }}
        </strong>
      </div>
      <div class="formula-audit-row">
        <template
          v-for="(part, partIndex) in chainView.formulaAudit.parts"
          :key="part.label"
        >
          <span
            v-if="partIndex > 0"
            class="formula-audit-operator"
          >
            {{ part.operator }}
          </span>
          <span class="formula-audit-part" :class="part.tone">
            <span>{{ part.label }}</span>
            <strong>{{ part.value }}</strong>
          </span>
        </template>
      </div>
      <p>{{ chainView.formulaAudit.note }}</p>
    </div>
    <div class="profit-chain-track">
      <div
        v-for="(step, stepIndex) in chainView.steps"
        :key="step.key"
        class="profit-chain-step"
      >
        <div
          class="chain-node"
          :class="[step.tone, { negative: step.isNegative }]"
        >
          <span class="chain-node-role">{{ step.role }}</span>
          <span class="chain-node-label">{{ step.node }}</span>
          <span class="chain-node-amount">{{ step.amountDisplay }}</span>
          <span v-if="step.ratio" class="chain-node-ratio">
            {{ step.ratio }}
          </span>
          <span
            v-if="step.formulaTag"
            class="chain-node-formula"
          >
            {{ step.formulaTag }}
          </span>
          <span v-if="step.note" class="chain-node-note">
            {{ step.note }}
          </span>
        </div>
        <div
          v-if="stepIndex < chainView.steps.length - 1"
          class="chain-arrow"
          aria-hidden="true"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  chainView: { type: Object, required: true },
  panelId: { type: String, default: '' },
})
</script>

<style scoped>
.profit-chain {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border-subtle);
}

.profit-chain-title {
  color: var(--text-muted);
  font-size: 11px;
  font-family: var(--font-display);
}

.profit-chain-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.profit-chain-source {
  flex: 0 0 auto;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid var(--border-subtle);
  border-radius: 999px;
  padding: 2px 7px;
  font-size: 10px;
  line-height: 1.35;
}

.profit-chain-summary {
  margin-bottom: 10px;
  padding: 9px 11px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.025);
}

.profit-chain-summary span {
  display: block;
  margin-bottom: 4px;
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
}

.profit-chain-summary p {
  margin: 0;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.5;
}

.profit-formula-audit {
  margin-bottom: 10px;
  padding: 9px 10px;
  border: 1px solid rgba(34, 211, 238, 0.14);
  border-radius: 7px;
  background: rgba(34, 211, 238, 0.035);
}

.formula-audit-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 7px;
}

.formula-audit-head span {
  color: var(--text-muted);
  font-size: 10px;
  font-family: var(--font-display);
}

.formula-audit-head strong {
  flex: 0 0 auto;
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 600;
}

.formula-audit-head strong.matched {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}

.formula-audit-head strong.mismatch {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
}

.formula-audit-head strong.partial {
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.05);
}

.formula-audit-row {
  display: flex;
  align-items: stretch;
  gap: 5px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.formula-audit-operator {
  flex: 0 0 auto;
  align-self: center;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
}

.formula-audit-part {
  flex: 0 0 auto;
  min-width: 86px;
  padding: 6px 7px;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.025);
}

.formula-audit-part span,
.formula-audit-part strong {
  display: block;
  white-space: nowrap;
}

.formula-audit-part span {
  color: var(--text-muted);
  font-size: 10px;
  margin-bottom: 2px;
}

.formula-audit-part strong {
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
}

.formula-audit-part.income {
  border-color: rgba(16, 185, 129, 0.18);
  background: rgba(16, 185, 129, 0.06);
}

.formula-audit-part.cost {
  border-color: rgba(245, 158, 11, 0.18);
  background: rgba(245, 158, 11, 0.08);
}

.formula-audit-part.net,
.formula-audit-part.matched {
  border-color: rgba(34, 211, 238, 0.18);
  background: rgba(34, 211, 238, 0.06);
}

.formula-audit-part.loss,
.formula-audit-part.mismatch {
  border-color: rgba(239, 68, 68, 0.2);
  background: rgba(239, 68, 68, 0.08);
}

.profit-formula-audit p {
  margin: 7px 0 0;
  color: var(--text-muted);
  font-size: 10px;
  line-height: 1.45;
}

.profit-chain-track {
  display: flex;
  align-items: stretch;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 3px;
}

.profit-chain-step {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
}

.chain-node {
  min-width: 92px;
  border: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.025);
  border-radius: 7px;
  padding: 7px 9px;
}

.chain-node.income {
  border-color: rgba(16, 185, 129, 0.18);
  background: rgba(16, 185, 129, 0.08);
}

.chain-node.payout {
  border-color: rgba(148, 163, 184, 0.18);
  background: rgba(148, 163, 184, 0.06);
}

.chain-node.cost,
.chain-node.negative {
  border-color: rgba(245, 158, 11, 0.18);
  background: rgba(245, 158, 11, 0.08);
}

.chain-node.net {
  border-color: rgba(34, 211, 238, 0.2);
  background: rgba(34, 211, 238, 0.08);
}

.chain-node.loss {
  border-color: rgba(239, 68, 68, 0.22);
  background: rgba(239, 68, 68, 0.08);
}

.chain-node.neutral {
  border-color: var(--border-subtle);
  background: var(--bg-elevated);
}

.chain-node-role,
.chain-node-label,
.chain-node-amount,
.chain-node-ratio,
.chain-node-formula {
  display: block;
  white-space: nowrap;
}

.chain-node-role {
  width: fit-content;
  max-width: 100%;
  margin-bottom: 4px;
  padding: 1px 5px;
  border-radius: 4px;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.045);
  font-size: 9px;
  line-height: 1.35;
}

.chain-node-label {
  color: var(--text-secondary);
  font-size: 11px;
  margin-bottom: 2px;
}

.chain-node-amount {
  color: #10b981;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
}

.chain-node-ratio {
  margin-top: 3px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 10px;
  line-height: 1.35;
}

.chain-node-formula {
  width: fit-content;
  max-width: 100%;
  margin-top: 3px;
  padding: 1px 5px;
  border-radius: 999px;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.05);
  font-size: 9px;
  line-height: 1.35;
}

.chain-node-note {
  display: block;
  margin-top: 3px;
  max-width: 128px;
  color: var(--text-muted);
  font-size: 10px;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.chain-node.negative .chain-node-amount {
  color: #f59e0b;
}

.chain-node.income .chain-node-amount {
  color: #10b981;
}

.chain-node.payout .chain-node-amount {
  color: #cbd5e1;
}

.chain-node.cost .chain-node-amount {
  color: #f59e0b;
}

.chain-node.net .chain-node-amount {
  color: #22d3ee;
}

.chain-node.loss .chain-node-amount {
  color: #ef4444;
}

.chain-arrow {
  width: 18px;
  height: 1px;
  margin: 0 4px;
  background: var(--border-default);
  position: relative;
}

.chain-arrow::after {
  content: '';
  position: absolute;
  right: -1px;
  top: -3px;
  width: 6px;
  height: 6px;
  border-right: 1px solid var(--border-default);
  border-top: 1px solid var(--border-default);
  transform: rotate(45deg);
}
</style>
