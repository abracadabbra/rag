<template>
  <div class="app-wrapper" :class="currentSceneClass">
    <div class="bg-grid"></div>
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
    <footer class="app-footer">
      <span>© 2026 RAG System</span>
      <span class="divider">·</span>
      <span>v0.1.0</span>
      <span class="divider">·</span>
      <router-link to="/settings" class="settings-link">API 设置</router-link>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const currentSceneClass = computed(() => {
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
  --bg-base: #080c18;
  --bg-surface: #0e1322;
  --bg-card: #141a2e;
  --bg-elevated: #1a2140;
  --bg-hover: rgba(255, 255, 255, 0.04);

  --text-primary: rgba(255, 255, 255, 0.92);
  --text-secondary: rgba(255, 255, 255, 0.6);
  --text-muted: rgba(255, 255, 255, 0.35);

  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.1);

  --accent-risk: #d4a843;
  --glow-risk: rgba(212, 168, 67, 0.15);
  --accent-risk-dim: rgba(212, 168, 67, 0.08);

  --accent-model: #7c3aed;
  --glow-model: rgba(124, 58, 237, 0.15);
  --accent-model-dim: rgba(124, 58, 237, 0.08);

  --accent-simulation: #f59e0b;
  --glow-simulation: rgba(245, 158, 11, 0.15);
  --accent-simulation-dim: rgba(245, 158, 11, 0.08);

  --accent-profit: #10b981;
  --glow-profit: rgba(16, 185, 129, 0.15);
  --accent-profit-dim: rgba(16, 185, 129, 0.08);

  --accent: var(--accent-risk);
  --accent-dim: var(--accent-risk-dim);
  --glow: var(--glow-risk);

  --font-display: 'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-body: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Noto Sans CJK SC', 'Microsoft YaHei', sans-serif;
}

html {
  background: var(--bg-base);
}

body {
  font-family: var(--font-body);
  background: var(--bg-base);
  color: var(--text-primary);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
}

a {
  text-decoration: none;
}

.app-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow-x: hidden;
}

.bg-grid {
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px);
  background-size: 60px 60px;
  pointer-events: none;
  z-index: 0;
}

.bg-grid::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 80% 60% at 50% -20%, rgba(212, 168, 67, 0.04) 0%, transparent 60%);
  pointer-events: none;
}

/* Scene themes */
.scene-risk {
  --accent: var(--accent-risk);
  --accent-dim: var(--accent-risk-dim);
  --glow: var(--glow-risk);
}
.scene-model {
  --accent: var(--accent-model);
  --accent-dim: var(--accent-model-dim);
  --glow: var(--glow-model);
}
.scene-simulation {
  --accent: var(--accent-simulation);
  --accent-dim: var(--accent-simulation-dim);
  --glow: var(--glow-simulation);
}
.scene-profit {
  --accent: var(--accent-profit);
  --accent-dim: var(--accent-profit-dim);
  --glow: var(--glow-profit);
}

.scene-risk .bg-grid::before {
  background: radial-gradient(ellipse 80% 60% at 50% -20%, rgba(212, 168, 67, 0.06) 0%, transparent 60%);
}
.scene-model .bg-grid::before {
  background: radial-gradient(ellipse 80% 60% at 50% -20%, rgba(124, 58, 237, 0.06) 0%, transparent 60%);
}
.scene-simulation .bg-grid::before {
  background: radial-gradient(ellipse 80% 60% at 50% -20%, rgba(245, 158, 11, 0.06) 0%, transparent 60%);
}
.scene-profit .bg-grid::before {
  background: radial-gradient(ellipse 80% 60% at 50% -20%, rgba(16, 185, 129, 0.06) 0%, transparent 60%);
}

.app-footer {
  padding: 20px;
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
  border-top: 1px solid var(--border-subtle);
  margin-top: auto;
  position: relative;
  z-index: 1;
}

.app-footer .divider {
  margin: 0 8px;
  opacity: 0.4;
}

.settings-link {
  color: var(--text-muted);
  transition: color 0.2s;
}

.settings-link:hover {
  color: var(--accent-risk);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.15);
}

::selection {
  background: rgba(212, 168, 67, 0.3);
  color: white;
}
</style>
