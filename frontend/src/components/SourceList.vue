<template>
  <div class="source-list">
    <div class="source-header">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
        <path d="M2 2h12v12H2V2zm1 1v10h10V3H3z"/>
        <path d="M5 5h6v1H5V5zm0 2h6v1H5V7zm0 2h4v1H5V9z"/>
      </svg>
      <span class="source-label">来源文档</span>
      <span class="source-count">({{ sources.length }})</span>
      <div v-if="metadata" class="retrieval-info">
        <span v-if="metadata.used_bm25" class="meta-tag bm25">BM25</span>
        <span v-if="metadata.used_rerank" class="meta-tag rerank">精排</span>
        <span class="meta-count">向量{{ metadata.vector_count }} / BM25{{ metadata.bm25_count }}</span>
      </div>
    </div>
    <div class="source-items">
      <div
        v-for="(source, index) in sources"
        :key="index"
        class="source-item"
      >
        <div class="source-top">
          <div class="source-tags">
            <span v-if="source.rule_id" class="tag rule-id">{{ source.rule_id }}</span>
            <span v-if="source.rule_name" class="tag rule-name">{{ source.rule_name }}</span>
            <span v-if="source.source_type" :class="['tag', 'source-type', source.source_type]">
              {{ sourceTypeLabel(source.source_type) }}
            </span>
          </div>
          <div class="score-badge">
            <span class="score-value">{{ (source.score * 100).toFixed(0) }}%</span>
            <span class="score-label">匹配</span>
          </div>
        </div>
        <div class="source-preview">{{ source.content_preview }}</div>
      </div>
    </div>
    <div v-if="sources.length === 0" class="no-sources">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
      </svg>
      <span>未找到相关文档</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  sources: {
    type: Array,
    default: () => []
  },
  metadata: {
    type: Object,
    default: null
  }
})

function sourceTypeLabel(type) {
  const labels = { vector: '向量', bm25: 'BM25', rerank: '精排' }
  return labels[type] || type
}
</script>

<style scoped>
.source-list {
  margin-top: 12px;
  background: #fafbfc;
  border-radius: 12px;
  padding: 12px 16px;
  border: 1px solid #f0f0f0;
}

.source-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  color: #8c8c8c;
  font-size: 13px;
  flex-wrap: wrap;
}

.source-label {
  font-weight: 500;
}

.source-count {
  color: #bfbfbf;
}

.retrieval-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.meta-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.meta-tag.bm25 {
  background: #fff7e6;
  color: #fa8c16;
  border: 1px solid #ffd591;
}

.meta-tag.rerank {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.meta-count {
  font-size: 11px;
  color: #8c8c8c;
}

.tag.source-type {
  background: #f0f0f0;
  color: #666;
}

.tag.source-type.rerank {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.source-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-item {
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 10px 12px;
  transition: all 0.2s;
}

.source-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.source-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
}

.source-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.rule-id {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.rule-name {
  background: #f0f7ff;
  color: #1890ff;
  border: 1px solid #d9e8ff;
}

.score-badge {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  flex-shrink: 0;
}

.score-value {
  font-size: 14px;
  font-weight: 600;
  color: #52c41a;
}

.score-label {
  font-size: 10px;
  color: #8c8c8c;
}

.source-preview {
  color: #666;
  font-size: 13px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.no-sources {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: #bfbfbf;
  font-size: 14px;
}

.no-sources svg {
  opacity: 0.5;
}
</style>
