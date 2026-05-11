<template>
  <div class="app-wrapper" :class="currentScene">
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
    <footer class="app-footer">
      <span>© 2026 RAG System</span>
      <span class="divider">·</span>
      <span>版本 0.1.0</span>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const currentScene = computed(() => {
  const path = route.path
  if (path.includes('risk-rules')) return 'scene-risk'
  if (path.includes('model-cards')) return 'scene-model'
  if (path.includes('simulation')) return 'scene-simulation'
  if (path.includes('profit')) return 'scene-profit'
  return ''
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --bg-base: #f5f7fa;
  --bg-risk: linear-gradient(180deg, #e6f7ff 0%, #f5f7fa 100%);
  --bg-model: linear-gradient(180deg, #f9f0ff 0%, #f5f7fa 100%);
  --bg-simulation: linear-gradient(180deg, #fff7e6 0%, #f5f7fa 100%);
  --bg-profit: linear-gradient(180deg, #f6ffed 0%, #f5f7fa 100%);
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-base);
  color: #333;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

a {
  text-decoration: none;
}

.app-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  transition: background 0.3s ease;
}

.app-wrapper.scene-risk {
  background: var(--bg-risk);
}

.app-wrapper.scene-model {
  background: var(--bg-model);
}

.app-wrapper.scene-simulation {
  background: var(--bg-simulation);
}

.app-wrapper.scene-profit {
  background: var(--bg-profit);
}

.app-footer {
  padding: 20px;
  text-align: center;
  font-size: 12px;
  color: #8c8c8c;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  margin-top: auto;
}

.app-footer .divider {
  margin: 0 8px;
}

/* 路由过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
