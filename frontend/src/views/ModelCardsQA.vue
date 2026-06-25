<template>
  <QAView
    title="模型卡片"
    subtitle="查询模型部署与特征"
    sceneType="model_card"
    welcomeTitle="模型卡片查询"
    welcomeDesc="查询模型部署信息、特征与适用场景"
    :suggestions="suggestions"
  />
</template>

<script setup>
import QAView from '../components/QAView.vue'

const suggestions = [
  '最新部署了哪些模型？',
  'A 模型的离线指标如何？',
  'B 模型适合什么场景？',
]
</script>
