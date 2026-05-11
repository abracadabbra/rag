<template>
  <div class="clarification-options">
    <div class="clarification-header">
      <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor">
        <path d="M9 1a8 8 0 100 16A8 8 0 009 1zm0 14.5a6.5 6.5 0 110-13 6.5 6.5 0 010 13zM9 4a1 1 0 00-1 1v3.5a1 1 0 102 0V5a1 1 0 00-1-1zm0 7a1 1 0 011 1v.5a1 1 0 11-2 0v-.5a1 1 0 011-1z"/>
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
  options: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['select'])

const handleSelect = (option) => {
  emit('select', option)
}
</script>

<style scoped>
.clarification-options {
  background: linear-gradient(135deg, #fffbe6 0%, #fff7e6 100%);
  border: 1px solid #ffe58f;
  border-radius: 16px 16px 16px 4px;
  padding: 14px 18px;
}

.clarification-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #ad6800;
  font-size: 14px;
  font-weight: 500;
}

.options-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.option-btn {
  padding: 8px 16px;
  background: white;
  border: 1px solid #ffe58f;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  color: #8c6d1f;
  transition: all 0.2s;
}

.option-btn:hover {
  background: #1890ff;
  border-color: #1890ff;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
}
</style>
