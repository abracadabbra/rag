<template>
  <div>
    <ProfitAnalysisPanel
      v-if="analysisModel"
      :analysis="analysisModel"
      :panel-id="profitAnalysisAnchorId"
    />
    <ProfitChainTimeline
      v-if="chainViewModel"
      :chain-view="chainViewModel"
      :panel-id="profitChainAnchorId"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ProfitAnalysisPanel from './ProfitAnalysisPanel.vue'
import ProfitChainTimeline from './ProfitChainTimeline.vue'

const props = defineProps({
  call: { type: Object, required: true },
  anchorPrefix: { type: String, default: '' },
})

const profitAnalysisAnchorId = computed(() => {
  return props.anchorPrefix ? `${props.anchorPrefix}-analysis` : ''
})

const profitChainAnchorId = computed(() => {
  return props.anchorPrefix ? `${props.anchorPrefix}-chain` : ''
})

const hasProfitAnalysis = computed(() => {
  const result = props.call?.result || {}
  return props.call?.name === 'get_profit_chain_detail' && (
    isNumber(result.gross_amount) ||
    isNumber(result.platform_commission) ||
    isNumber(result.driver_income) ||
    isNumber(result.platform_net_profit)
  )
})

const analysisModel = computed(() => {
  if (!hasProfitAnalysis.value) return null

  return {
    toneClass: profitToneClass(),
    toneLabel: profitToneLabel(),
    summary: profitExecutiveSummary(),
    metrics: profitMetrics(),
    equationParts: profitEquationParts(),
    ledgerRows: profitLedgerRows(),
    signals: profitSignals(),
  }
})

const hasProfitChain = computed(() => {
  return props.call?.name === 'get_profit_chain_detail' && profitChain().length > 0
})

const chainViewModel = computed(() => {
  if (!hasProfitChain.value) return null

  return {
    summary: profitChainFormulaSummary(),
    sourceLabel: profitChainSourceLabel(),
    formulaAudit: profitFormulaAudit(),
    steps: profitChain().map((step, stepIndex) => ({
      key: `${step.node}-${stepIndex}`,
      node: step.node,
      role: profitChainStepRole(step),
      tone: profitChainStepTone(step),
      isNegative: Number(step.amount) < 0,
      amountDisplay: formatChainAmount(step.amount),
      ratio: profitChainStepRatio(step),
      formulaTag: profitChainStepFormulaTag(step),
      note: profitChainStepNote(step),
    })),
  }
})

function profitMetrics() {
  const result = props.call?.result || {}
  const gross = result.gross_amount
  const commission = result.platform_commission
  const driverIncome = result.driver_income
  const netProfit = result.platform_net_profit
  return [
    {
      label: '乘客支付',
      value: formatMoney(gross),
      hint: 'GMV',
      tone: 'income',
    },
    {
      label: '平台抽成',
      value: formatMoney(commission),
      hint: ratioHint(commission, gross),
      tone: 'income',
    },
    {
      label: '司机收入',
      value: formatMoney(driverIncome),
      hint: ratioHint(driverIncome, gross),
      tone: 'neutral',
    },
    {
      label: '净毛利',
      value: formatMoney(netProfit),
      hint: ratioHint(netProfit, gross),
      tone: isNumber(netProfit) && netProfit < 0 ? 'loss' : 'net',
    },
  ].filter(metric => metric.value !== undefined && metric.value !== null && metric.value !== '')
}

function profitLedgerRows() {
  const result = props.call?.result || {}
  return [
    { label: '收入项：平台抽成', value: formatMoney(result.platform_commission), tone: 'income' },
    { label: '成本项：平台补贴', value: formatSignedCost(result.subsidy), tone: 'cost' },
    { label: '成本项：用户优惠', value: formatSignedCost(result.coupon), tone: 'cost' },
    { label: '成本项：渠道费', value: formatSignedCost(result.channel_fee), tone: 'cost' },
    { label: '结论：平台净毛利', value: formatMoney(result.platform_net_profit), tone: 'net' },
  ].filter(row => row.value !== undefined && row.value !== null && row.value !== '')
}

function profitEquationParts() {
  const result = props.call?.result || {}
  const netProfit = result.platform_net_profit
  return [
    { label: '平台抽成', value: formatMoney(result.platform_commission), operator: '', tone: 'income' },
    { label: '平台补贴', value: formatAbsoluteMoney(result.subsidy), operator: '-', tone: 'cost' },
    { label: '用户优惠', value: formatAbsoluteMoney(result.coupon), operator: '-', tone: 'cost' },
    { label: '渠道费', value: formatAbsoluteMoney(result.channel_fee), operator: '-', tone: 'cost' },
    {
      label: '平台净毛利',
      value: formatMoney(netProfit),
      operator: '=',
      tone: isNumber(netProfit) && netProfit < 0 ? 'loss' : 'net',
    },
  ].filter(part => part.value !== undefined && part.value !== null && part.value !== '')
}

function profitSignals() {
  const result = props.call?.result || {}
  const gross = result.gross_amount
  const commission = result.platform_commission
  const subsidy = result.subsidy
  const coupon = result.coupon
  const channelFee = result.channel_fee
  const netProfit = result.platform_net_profit
  const signals = []

  if (isNumber(netProfit) && netProfit < 0) {
    signals.push('净毛利为负，需要核查补贴、优惠或渠道成本。')
  } else if (isNumber(netProfit) && isNumber(gross) && gross > 0 && netProfit / gross < 0.03) {
    signals.push('净毛利率低于 3%，建议复核活动成本。')
  }
  if (isNumber(subsidy) && isNumber(gross) && gross > 0 && subsidy / gross >= 0.06) {
    signals.push('平台补贴占比偏高。')
  }
  if (isNumber(coupon) && isNumber(commission) && commission > 0 && coupon / commission >= 0.3) {
    signals.push('用户优惠消耗超过抽成的 30%。')
  }
  if (isNumber(channelFee) && isNumber(gross) && gross > 0 && channelFee / gross >= 0.03) {
    signals.push('渠道费占比偏高。')
  }

  return signals
}

function profitExecutiveSummary() {
  const result = props.call?.result || {}
  const gross = result.gross_amount
  const netProfit = result.platform_net_profit
  const commission = result.platform_commission
  const driverIncome = result.driver_income

  if (!isNumber(gross) && !isNumber(netProfit) && !isNumber(commission) && !isNumber(driverIncome)) {
    return null
  }

  return {
    headline: profitHeadline(),
    summary: profitSummaryText(),
    drivers: profitTopDrivers(),
  }
}

function profitHeadline() {
  const netProfit = props.call?.result?.platform_net_profit
  const gross = props.call?.result?.gross_amount

  if (isNumber(netProfit) && netProfit < 0) return '当前订单处于亏损状态'
  if (isNumber(netProfit) && isNumber(gross) && gross > 0 && netProfit / gross < 0.03) {
    return '当前订单毛利偏薄'
  }
  return '当前订单毛利结构正常'
}

function profitSummaryText() {
  const result = props.call?.result || {}
  const netProfit = result.platform_net_profit
  const gross = result.gross_amount
  const commission = result.platform_commission
  const driverIncome = result.driver_income
  const margin = isNumber(netProfit) && isNumber(gross) && gross > 0
    ? `${(netProfit / gross * 100).toFixed(1)}%`
    : null

  const parts = []
  if (isNumber(gross)) parts.push(`乘客实付 ${formatMoney(gross)}`)
  if (isNumber(commission)) parts.push(`平台留存抽成 ${formatMoney(commission)}`)
  if (isNumber(driverIncome)) parts.push(`司机结算 ${formatMoney(driverIncome)}`)
  if (isNumber(netProfit)) {
    parts.push(
      margin
        ? `最终净毛利 ${formatMoney(netProfit)}，净毛利率 ${margin}`
        : `最终净毛利 ${formatMoney(netProfit)}`
    )
  }
  return parts.join('，')
}

function profitTopDrivers() {
  const result = props.call?.result || {}
  const drivers = [
    buildProfitDriver('平台补贴', result.subsidy),
    buildProfitDriver('用户优惠', result.coupon),
    buildProfitDriver('渠道成本', result.channel_fee),
    buildProfitDriver('平台抽成', result.platform_commission, true),
  ].filter(Boolean)

  return drivers
    .sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount))
    .slice(0, 3)
    .map(driver => driver.label)
}

function buildProfitDriver(label, value, positive = false) {
  if (!isNumber(value) || value === 0) return null
  const amount = positive ? value : -Math.abs(value)
  const display = positive ? formatMoney(value) : formatSignedCost(value)
  return {
    amount,
    label: `${label} ${display}`,
  }
}

function profitToneClass() {
  const netProfit = props.call?.result?.platform_net_profit
  if (isNumber(netProfit) && netProfit < 0) return 'loss'
  if (profitSignals().length) return 'warning'
  return 'healthy'
}

function profitToneLabel() {
  const tone = profitToneClass()
  if (tone === 'loss') return '亏损'
  if (tone === 'warning') return '需关注'
  return '正常'
}

function profitChain() {
  const chain = props.call?.result?.chain
  return Array.isArray(chain) ? chain.filter(step => step && step.node) : []
}

function profitChainStepTone(step) {
  if (typeof step?.tone === 'string' && step.tone.trim()) return step.tone.trim()
  const role = profitChainStepRole(step)
  if (role === '经营结果') return Number(step?.amount) < 0 ? 'loss' : 'net'
  if (role === '平台收入' || role === '订单收入') return 'income'
  if (role === '司机结算') return 'payout'
  if (role === '平台成本' || role === '营销成本' || role === '渠道成本') return 'cost'
  return Number(step?.amount) < 0 ? 'cost' : 'neutral'
}

function profitChainStepRole(step) {
  if (typeof step?.role === 'string' && step.role.trim()) return step.role.trim()
  const node = String(step?.node || '')
  if (node.includes('乘客支付')) return '订单收入'
  if (node.includes('平台抽成')) return '平台收入'
  if (node.includes('司机收入')) return '司机结算'
  if (node.includes('平台补贴')) return '平台成本'
  if (node.includes('用户优惠')) return '营销成本'
  if (node.includes('渠道成本') || node.includes('渠道费')) return '渠道成本'
  if (node.includes('净毛利')) return '经营结果'
  return '链路节点'
}

function profitChainStepRatio(step) {
  const gross = props.call?.result?.gross_amount
  const amount = step?.amount
  if (!isNumber(amount) || !isNumber(gross) || gross === 0) return ''
  const ratio = amount / gross * 100
  const prefix = ratio > 0 ? '+' : ''
  return `${prefix}${ratio.toFixed(1)}% GMV`
}

function profitChainStepNote(step) {
  if (typeof step?.note === 'string' && step.note.trim()) return step.note.trim()
  const role = profitChainStepRole(step)
  const amount = step?.amount
  if (role === '订单收入') return '乘客实付基数'
  if (role === '平台收入') return '收入进入毛利公式'
  if (role === '司机结算') return '履约侧结算'
  if (role === '平台成本') return '平台承担成本'
  if (role === '营销成本') return '优惠消耗抽成'
  if (role === '渠道成本') return '获客/支付渠道成本'
  if (role === '经营结果') return isNumber(amount) && amount < 0 ? '最终亏损' : '最终留存'
  return ''
}

function profitChainStepFormulaTag(step) {
  const role = profitChainStepRole(step)
  if (role === '订单收入') return 'GMV 基数'
  if (role === '司机结算') return '履约分账参考'
  if (role === '经营结果') return '毛利结果'
  if (role === '平台收入' || role === '平台成本' || role === '营销成本' || role === '渠道成本') {
    return '计入毛利公式'
  }
  return ''
}

function profitChainFormulaSummary() {
  if (!hasProfitChain.value) return ''
  return '净毛利 = 平台抽成 - 平台补贴 - 用户优惠 - 渠道成本；司机收入用于展示履约分账，不重复计入净毛利。'
}

function profitFormulaAudit() {
  const result = props.call?.result || {}
  const commission = result.platform_commission
  const subsidy = result.subsidy
  const coupon = result.coupon
  const channelFee = result.channel_fee
  const netProfit = result.platform_net_profit
  const requiredValues = [commission, subsidy, coupon, netProfit]
  const hasRequiredValues = requiredValues.every(isNumber)
  if (!hasRequiredValues) return null

  const safeChannelFee = isNumber(channelFee) ? channelFee : 0
  const calculated = roundMoney(commission - subsidy - coupon - safeChannelFee)
  const reported = roundMoney(netProfit)
  const delta = roundMoney(calculated - reported)
  const matched = Math.abs(delta) < 0.01
  const channelFeeNote = isNumber(channelFee) ? '' : '，未返回渠道费时按 0 参与核对'

  return {
    tone: matched ? 'matched' : 'mismatch',
    statusLabel: matched ? '与接口净毛利一致' : '与接口净毛利不一致',
    note: matched
      ? `计算净毛利 ${formatMoney(calculated)}，与接口返回值一致${channelFeeNote}。`
      : `按公式计算为 ${formatMoney(calculated)}，接口返回 ${formatMoney(reported)}，差异 ${formatSignedDelta(delta)}${channelFeeNote}。`,
    parts: [
      { label: '平台抽成', value: formatMoney(commission), operator: '', tone: 'income' },
      { label: '平台补贴', value: formatAbsoluteMoney(subsidy), operator: '-', tone: 'cost' },
      { label: '用户优惠', value: formatAbsoluteMoney(coupon), operator: '-', tone: 'cost' },
      { label: '渠道费', value: formatAbsoluteMoney(safeChannelFee), operator: '-', tone: 'cost' },
      {
        label: '计算净毛利',
        value: formatMoney(calculated),
        operator: '=',
        tone: matched ? 'matched' : 'mismatch',
      },
    ],
  }
}

function profitChainSourceLabel() {
  const source = props.call?.result?.chain_source
  if (source === 'api') return '接口原生链路'
  if (source === 'derived') return '自动派生链路'
  return ''
}

function formatMoney(value) {
  if (typeof value !== 'number') return value
  return `${value.toFixed(2)} 元`
}

function formatSignedCost(value) {
  if (!isNumber(value)) return value
  if (value === 0) return '0.00 元'
  return `-${Math.abs(value).toFixed(2)} 元`
}

function formatAbsoluteMoney(value) {
  if (!isNumber(value)) return value
  return `${Math.abs(value).toFixed(2)} 元`
}

function formatSignedDelta(value) {
  if (!isNumber(value)) return value
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${value.toFixed(2)} 元`
}

function formatChainAmount(value) {
  if (typeof value !== 'number') return value ?? ''
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${value.toFixed(2)} 元`
}

function ratioHint(value, base) {
  if (!isNumber(value) || !isNumber(base) || base === 0) return ''
  return `${(value / base * 100).toFixed(1)}%`
}

function isNumber(value) {
  return typeof value === 'number' && Number.isFinite(value)
}

function roundMoney(value) {
  return Math.round(value * 100) / 100
}
</script>
