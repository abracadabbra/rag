<template>
  <div class="source-list">
    <div class="source-header">
      <span class="source-label">来源文档</span>
      <span class="source-count">({{ sources.length }} 条)</span>
    </div>
    <div class="source-items">
      <div
        v-for="(source, index) in sources"
        :key="index"
        class="source-item"
      >
        <div class="source-meta">
          <span v-if="source.rule_id" class="rule-id">{{ source.rule_id }}</span>
          <span v-if="source.rule_name" class="rule-name">{{ source.rule_name }}</span>
          <span class="score">相似度: {{ (source.score * 100).toFixed(1) }}%</span>
        </div>
        <div class="source-preview">{{ source.content_preview }}</div>
      </div>
    </div>
    <div v-if="sources.length === 0" class="no-sources">
      未找到相关文档
    </div>
  </div>
</template>

<script setup>
defineProps({
  sources: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
.source-list {
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
}

.source-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.source-label {
  font-weight: 600;
  color: #333;
}

.source-count {
  color: #888;
  font-size: 14px;
}

.source-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.source-item {
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 12px;
}

.source-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
}

.rule-id {
  background: #e6f7ff;
  color: #1890ff;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.rule-name {
  color: #333;
  font-weight: 500;
}

.score {
  color: #888;
}

.source-preview {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.no-sources {
  color: #888;
  text-align: center;
  padding: 20px;
}
</style>
