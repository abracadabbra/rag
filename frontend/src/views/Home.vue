<template>
  <div class="home">
    <div class="hero">
      <div class="hero-badge">
        <span class="badge-dot"></span>
        INTELLIGENT RAG SYSTEM
      </div>
      <h1 class="hero-title">
        <span class="title-line">风控知识</span>
        <span class="title-line accent">智能问答</span>
      </h1>
      <p class="hero-desc">基于检索增强生成，为您解答风控政策、规则与业务问题</p>
      <div class="hero-typing">
        <span class="typing-text">{{ typedText }}</span>
        <span class="typing-cursor">|</span>
      </div>
    </div>

    <div class="scene-grid">
      <router-link
        v-for="(card, i) in cards"
        :key="card.route"
        :to="card.route"
        class="scene-card"
        :class="card.class"
        :style="{ '--delay': i, '--accent-c': card.accent }"
        @mouseenter="onCardEnter($event)"
        @mouseleave="onCardLeave($event)"
      >
        <div class="card-stripe"></div>
        <div class="card-glow"></div>
        <div class="card-body">
          <div class="card-icon" v-html="card.icon"></div>
          <div class="card-content">
            <h2 class="card-title">{{ card.title }}</h2>
            <p class="card-desc">{{ card.desc }}</p>
            <div class="card-tags">
              <span v-for="tag in card.tags" :key="tag">{{ tag }}</span>
            </div>
          </div>
          <div class="card-right">
            <div class="card-stat">
              <span class="stat-value">{{ card.stat }}</span>
              <span class="stat-label">{{ card.statLabel }}</span>
            </div>
            <div class="card-arrow">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M5 10h10M12 7l3 3-3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
          </div>
        </div>
      </router-link>
    </div>

    <div class="bottom-hint">
      <span class="hint-pulse"></span>
      <span>选择一个场景开始探索</span>
      <span class="hint-time">{{ currentTime }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const cards = [
  {
    route: '/risk-rules',
    class: 'card-risk',
    accent: 'var(--accent-risk)',
    title: '风控规则',
    desc: '查询风控政策、制度与规则信息',
    tags: ['政策查询', '规则解读', '合规建议'],
    stat: '2.4k',
    statLabel: '规则条目',
    icon: `<svg width="52" height="52" viewBox="0 0 36 36" fill="none"><rect x="3" y="3" width="30" height="30" rx="8" stroke="currentColor" stroke-width="1.2"/><path d="M12 18h12M18 12v12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>`
  },
  {
    route: '/model-cards',
    class: 'card-model',
    accent: 'var(--accent-model)',
    title: '模型卡片',
    desc: '查询模型部署、特征与适用场景',
    tags: ['部署信息', '模型特征', '选型建议'],
    stat: '18',
    statLabel: '模型实例',
    icon: `<svg width="52" height="52" viewBox="0 0 36 36" fill="none"><rect x="3" y="3" width="30" height="30" rx="8" stroke="currentColor" stroke-width="1.2"/><rect x="10" y="10" width="16" height="16" rx="3" stroke="currentColor" stroke-width="1.2" fill="none"/><circle cx="18" cy="18" r="4" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>`
  },
  {
    route: '/simulation',
    class: 'card-simulation',
    accent: 'var(--accent-simulation)',
    title: '仿真解读',
    desc: '解读仿真结果与分析模型表现',
    tags: ['结果分析', '性能对比', '数据洞察'],
    stat: '96%',
    statLabel: '准确率',
    icon: `<svg width="52" height="52" viewBox="0 0 36 36" fill="none"><rect x="3" y="3" width="30" height="30" rx="8" stroke="currentColor" stroke-width="1.2"/><path d="M11 25V16l7-5 7 5v9" stroke="currentColor" stroke-width="1.2" fill="none" stroke-linejoin="round"/><circle cx="18" cy="20" r="2.5" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>`
  },
  {
    route: '/profit',
    class: 'card-profit',
    accent: 'var(--accent-profit)',
    title: '毛利抽成',
    desc: '查询分成比例与结算规则',
    tags: ['分成比例', '结算规则', '收益分析'],
    stat: '¥8.6M',
    statLabel: '月均结算',
    icon: `<svg width="52" height="52" viewBox="0 0 36 36" fill="none"><rect x="3" y="3" width="30" height="30" rx="8" stroke="currentColor" stroke-width="1.2"/><path d="M18 11v14M13 15l5-5 5 5M13 22l5 5 5-5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>`
  }
]

const typingPhrases = [
  '正在分析风控策略...',
  '模型推理就绪，等待输入...',
  '仿真引擎加载完成',
  '毛利计算服务运行中'
]

const typedText = ref('')
const currentTime = ref('')
let phraseIndex = 0
let charIndex = 0
let typingTimer = null
let timeTimer = null

function typeNext() {
  const phrase = typingPhrases[phraseIndex]
  if (charIndex <= phrase.length) {
    typedText.value = phrase.slice(0, charIndex)
    charIndex++
    typingTimer = setTimeout(typeNext, 60 + Math.random() * 40)
  } else {
    typingTimer = setTimeout(() => {
      charIndex = 0
      phraseIndex = (phraseIndex + 1) % typingPhrases.length
      typedText.value = ''
      typeNext()
    }, 2000)
  }
}

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { hour12: false })
}

function onCardEnter(e) {
  const card = e.currentTarget
  card.addEventListener('mousemove', onCardMove)
}

function onCardLeave(e) {
  const card = e.currentTarget
  card.removeEventListener('mousemove', onCardMove)
  card.style.transform = ''
}

function onCardMove(e) {
  const card = e.currentTarget
  const rect = card.getBoundingClientRect()
  const x = e.clientX - rect.left - rect.width / 2
  const y = e.clientY - rect.top - rect.height / 2
  card.style.transform = `translateY(-4px) perspective(800px) rotateX(${-y * 0.01}deg) rotateY(${x * 0.01}deg)`
}

onMounted(() => {
  typeNext()
  updateTime()
  timeTimer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
  clearTimeout(typingTimer)
  clearInterval(timeTimer)
})
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 56px 40px 40px;
  position: relative;
  z-index: 1;
  flex: 1;
}

/* ── Hero ── */
.hero {
  text-align: center;
  margin-bottom: 56px;
  position: relative;
  animation: fadeUp 0.7s ease;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: 'DM Sans', sans-serif;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 3px;
  color: var(--accent);
  background: var(--accent-dim);
  padding: 6px 18px 6px 14px;
  border-radius: 20px;
  margin-bottom: 24px;
  border: 1px solid var(--glow);
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulse 2s infinite;
  box-shadow: 0 0 8px var(--glow);
}

.hero-title {
  font-family: 'DM Sans', sans-serif;
  font-size: 52px;
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
}

.title-line {
  color: var(--text-primary);
  letter-spacing: -0.03em;
}

.title-line.accent {
  background: linear-gradient(135deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 60%, white) 50%, var(--accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 15px;
  color: var(--text-secondary);
  max-width: 460px;
  margin: 0 auto 16px;
  line-height: 1.6;
}

.hero-typing {
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.02em;
  min-height: 20px;
}

.typing-cursor {
  animation: blink 1s step-end infinite;
  color: var(--accent);
  font-weight: 300;
}

/* ── Cards ── */
.scene-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.scene-card {
  position: relative;
  display: flex;
  align-items: stretch;
  padding: 0;
  background: var(--bg-card);
  border-radius: 14px;
  border: 1px solid var(--border-subtle);
  transition: all 0.35s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  overflow: hidden;
  animation: fadeUp 0.5s ease backwards;
  animation-delay: calc(var(--delay) * 0.08s + 0.25s);
  will-change: transform;
}

.scene-card:hover {
  border-color: var(--border-default);
  background: var(--bg-elevated);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.25);
}

/* Left accent stripe */
.card-stripe {
  position: absolute;
  left: 0;
  top: 14px;
  bottom: 14px;
  width: 4px;
  border-radius: 0 3px 3px 0;
  background: var(--accent-c);
  opacity: 0.3;
  transition: opacity 0.3s, top 0.3s, bottom 0.3s;
}

.scene-card:hover .card-stripe {
  opacity: 1;
  top: 8px;
  bottom: 8px;
}

.card-glow {
  position: absolute;
  top: -60%;
  right: -10%;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--accent-c) 10%, transparent) 0%, transparent 60%);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.5s ease;
}

.scene-card:hover .card-glow {
  opacity: 1;
}

.card-body {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 36px 36px 36px 42px;
  position: relative;
  z-index: 1;
}

.card-icon {
  flex-shrink: 0;
  color: var(--text-muted);
  transition: color 0.3s;
}

.scene-card:hover .card-icon {
  color: var(--accent-c);
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-title {
  font-family: 'DM Sans', sans-serif;
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
  letter-spacing: -0.01em;
}

.card-desc {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  line-height: 1.5;
}

.card-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.card-tags span {
  font-size: 13px;
  padding: 4px 12px;
  border-radius: 10px;
  color: var(--text-muted);
  border: 1px solid var(--border-subtle);
  transition: all 0.3s;
}

.scene-card:hover .card-tags span {
  border-color: color-mix(in srgb, var(--accent-c) 25%, transparent);
  color: var(--accent-c);
  background: color-mix(in srgb, var(--accent-c) 5%, transparent);
}

.card-right {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 28px;
}

.card-stat {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.stat-value {
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 28px;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: -0.02em;
  transition: color 0.3s;
}

.scene-card:hover .stat-value {
  color: var(--accent-c);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.04em;
}

.card-arrow {
  color: var(--text-muted);
  opacity: 0;
  transform: translateX(-6px);
  transition: all 0.3s ease;
}

.scene-card:hover .card-arrow {
  opacity: 1;
  transform: translateX(0);
  color: var(--accent-c);
}

/* ── Bottom hint ── */
.bottom-hint {
  text-align: center;
  margin-top: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 12px;
  color: var(--text-muted);
  animation: fadeUp 0.6s ease 0.7s backwards;
}

.hint-pulse {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
  animation: pulse 2s infinite;
}

.hint-time {
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 11px;
  opacity: 0.5;
  margin-left: 4px;
}

/* ── Animations ── */
@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes blink {
  50% { opacity: 0; }
}

@media (max-width: 768px) {
  .home { padding: 36px 20px; }
  .hero-title { font-size: 36px; }
  .scene-grid { grid-template-columns: 1fr; gap: 14px; }
  .card-body { padding: 22px 20px; gap: 16px; }
  .card-right { display: none; }
  .card-icon svg { width: 36px; height: 36px; }
  .hero-typing { display: none; }
}
</style>
