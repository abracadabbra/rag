<template>
  <div class="source-list">
    <div class="source-header">
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <rect x="1" y="1" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.2"/>
        <path d="M4 4h6v1H4V4zm0 3h6v1H4V7zm0 3h4v1H4v-1z" fill="currentColor"/>
      </svg>
      <span class="source-label">来源文档</span>
      <span class="source-count">({{ sources.length }})</span>
      <div v-if="metadata" class="retrieval-info">
        <span v-if="metadata.used_bm25" class="meta-tag bm25">BM25</span>
        <span v-if="metadata.used_rerank" class="meta-tag rerank">精排</span>
      </div>
    </div>
    <div class="source-items">
      <div v-for="(source, index) in sources" :key="index" class="source-item">
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
          </div>
        </div>
        <div class="source-preview">{{ source.content_preview }}</div>
      </div>
    </div>
    <div v-if="sources.length === 0" class="no-sources">
      <span>未找到相关文档</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  sources: { type: Array, default: () => [] },
  metadata: { type: Object, default: null }
})

function sourceTypeLabel(type) {
  const labels = { vector: '向量', bm25: 'BM25', rerank: '精排' }
  return labels[type] || type
}
</script>

<style scoped>
.source-list {
  margin-top: 10px;
  background: var(--bg-surface);
  border-radius: 12px;
  padding: 12px 14px;
  border: 1px solid var(--border-subtle);
}

.source-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  color: var(--text-muted);
  font-size: 12px;
  flex-wrap: wrap;
}

.source-label {
  font-weight: 500;
}

.source-count {
  opacity: 0.6;
}

.retrieval-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.meta-tag {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.meta-tag.bm25 {
  background: rgba(245, 158, 11, 0.12);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.meta-tag.rerank {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.source-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.source-item {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 10px 12px;
  transition: all 0.2s;
}

.source-item:hover {
  border-color: var(--glow);
  box-shadow: 0 2px 12px var(--glow);
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
  gap: 4px;
}

.tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.rule-id {
  background: var(--glow);
  color: var(--accent);
}

.rule-name {
  background: var(--bg-elevated);
  color: var(--text-secondary);
}

.tag.source-type {
  background: var(--bg-elevated);
  color: var(--text-muted);
}

.tag.source-type.rerank {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.score-badge {
  flex-shrink: 0;
}

.score-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
}

.source-preview {
  color: var(--text-muted);
  font-size: 12px;
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
  padding: 16px;
  color: var(--text-muted);
  font-size: 13px;
}
</style>
