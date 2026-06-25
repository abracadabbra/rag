<template>
  <QAView
    title="仿真解读"
    subtitle="解读仿真结果与分析模型表现"
    sceneType="simulation"
    welcomeTitle="仿真结果解读"
    welcomeDesc="查看仿真运行结果与模型性能分析"
    :suggestions="suggestions"
  />
</template>

<script setup>
import QAView from '../components/QAView.vue'

const suggestions = [
  '最新一次仿真结果如何？',
  'A 模型和 B 模型哪个表现更好？',
  '仿真的 KS 值是多少？',
]
</script>
