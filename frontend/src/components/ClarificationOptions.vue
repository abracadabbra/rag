<template>
  <div class="clarification-options">
    <div class="clarification-header">
      <span class="clarification-label">请选择您想查询的方面：</span>
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
  background: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: 8px;
  padding: 16px;
}

.clarification-header {
  margin-bottom: 12px;
}

.clarification-label {
  color: #ad6800;
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
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.option-btn:hover {
  border-color: #1890ff;
  color: #1890ff;
}
</style>
