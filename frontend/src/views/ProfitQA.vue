<template>
  <QAView
    title="毛利抽成"
    subtitle="查询分成比例与结算规则"
    sceneType="profit"
    welcomeTitle="毛利抽成查询"
    welcomeDesc="查询分成比例、结算规则与收益分析"
    :suggestions="suggestions"
    :answerPerspectives="answerPerspectives"
  />
</template>

<script setup>
import QAView from '../components/QAView.vue'

const suggestions = [
  '查询订单 ORD88888 的抽成和司机收入',
  '订单 ORD88888 的钱流链路是怎样的？',
  '当前毛利抽成怎么计算？',
]

const answerPerspectives = [
  { value: '', label: '自动' },
  { value: 'finance', label: '财务' },
  { value: 'operations', label: '运营' },
  { value: 'technical', label: '排查' },
]
</script>
