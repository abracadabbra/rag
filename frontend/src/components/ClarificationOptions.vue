<template>
  <div class="clarification-options">
    <div class="clarification-header">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.2"/>
        <path d="M8 5v3.5M8 10.5v.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
      <span>请选择您想查询的方面：</span>
    </div>
    <div class="options-list">
      <button
        v-for="(option, index) in options"
        :key="index"
        @click="handleSelect(option)"
        class="option-btn"
      >
        {{ option }}
      </button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  options: { type: Array, required: true }
})
const emit = defineEmits(['select'])
const handleSelect = (option) => emit('select', option)
</script>

<style scoped>
.clarification-options {
  background: var(--bg-card);
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-radius: 16px 16px 16px 4px;
  padding: 14px 18px;
}

.clarification-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #f59e0b;
  font-size: 14px;
  font-weight: 500;
}

.options-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.option-btn {
  padding: 7px 16px;
  background: var(--bg-surface);
  border: 1px solid rgba(245, 158, 11, 0.15);
  border-radius: 20px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  font-family: var(--font-body);
  transition: all 0.2s;
}

.option-btn:hover {
  background: rgba(245, 158, 11, 0.1);
  border-color: var(--accent-simulation);
  color: var(--accent-simulation);
  transform: translateY(-1px);
}
</style>
