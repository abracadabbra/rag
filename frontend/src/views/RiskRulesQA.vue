<template>
  <QAView
    title="风控规则"
    subtitle="智能检索风控政策与规则"
    sceneType="risk_rule"
    welcomeTitle="风控规则查询"
    welcomeDesc="基于检索增强生成，为您解答风控政策、规则与业务问题"
    :suggestions="suggestions"
    :answerPerspectives="answerPerspectives"
  />
</template>

<script setup>
import QAView from '../components/QAView.vue'

const suggestions = [
  '白金卡的单笔交易限额是多少？',
  '信用卡取现的手续费怎么计算？',
  '哪些情况下交易会被风控拦截？',
]

const answerPerspectives = [
  { value: '', label: '自动' },
  { value: 'strategy', label: '策略' },
  { value: 'operations', label: '运营' },
  { value: 'technical', label: '排查' },
]
</script>
