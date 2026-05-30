<template>
  <div class="home">
    <div class="hero">
      <div class="hero-badge">INTELLIGENT RAG SYSTEM</div>
      <h1 class="hero-title">
        <span class="title-line">风控知识</span>
        <span class="title-line accent">智能问答</span>
      </h1>
      <p class="hero-desc">基于检索增强生成，为您解答风控政策、规则与业务问题</p>
      <div class="hero-glow"></div>
    </div>

    <div class="scene-grid">
      <router-link to="/risk-rules" class="scene-card card-risk" style="--delay: 0">
        <div class="card-glow"></div>
        <div class="card-icon">
          <svg width="44" height="44" viewBox="0 0 44 44" fill="none">
            <rect x="4" y="4" width="36" height="36" rx="10" stroke="currentColor" stroke-width="1.5"/>
            <path d="M16 22h12M22 16v12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <h2 class="card-title">风控规则</h2>
        <p class="card-desc">查询风控政策、制度与规则信息</p>
        <div class="card-tags">
          <span>政策查询</span>
          <span>规则解读</span>
          <span>合规建议</span>
        </div>
        <div class="card-arrow">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M5 10h10M12 7l3 3-3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </router-link>

      <router-link to="/model-cards" class="scene-card card-model" style="--delay: 1">
        <div class="card-glow"></div>
        <div class="card-icon">
          <svg width="44" height="44" viewBox="0 0 44 44" fill="none">
            <rect x="4" y="4" width="36" height="36" rx="10" stroke="currentColor" stroke-width="1.5"/>
            <rect x="12" y="12" width="20" height="20" rx="4" stroke="currentColor" stroke-width="1.5" fill="none"/>
            <circle cx="22" cy="22" r="5" stroke="currentColor" stroke-width="1.5" fill="none"/>
          </svg>
        </div>
        <h2 class="card-title">模型卡片</h2>
        <p class="card-desc">查询模型部署、特征与适用场景</p>
        <div class="card-tags">
          <span>部署信息</span>
          <span>模型特征</span>
          <span>选型建议</span>
        </div>
        <div class="card-arrow">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M5 10h10M12 7l3 3-3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </router-link>

      <router-link to="/simulation" class="scene-card card-simulation" style="--delay: 2">
        <div class="card-glow"></div>
        <div class="card-icon">
          <svg width="44" height="44" viewBox="0 0 44 44" fill="none">
            <rect x="4" y="4" width="36" height="36" rx="10" stroke="currentColor" stroke-width="1.5"/>
            <path d="M14 30V20l8-6 8 6v10" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linejoin="round"/>
            <circle cx="22" cy="24" r="3" stroke="currentColor" stroke-width="1.5" fill="none"/>
          </svg>
        </div>
        <h2 class="card-title">仿真解读</h2>
        <p class="card-desc">解读仿真结果与分析模型表现</p>
        <div class="card-tags">
          <span>结果分析</span>
          <span>性能对比</span>
          <span>数据洞察</span>
        </div>
        <div class="card-arrow">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M5 10h10M12 7l3 3-3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </router-link>

      <router-link to="/profit" class="scene-card card-profit" style="--delay: 3">
        <div class="card-glow"></div>
        <div class="card-icon">
          <svg width="44" height="44" viewBox="0 0 44 44" fill="none">
            <rect x="4" y="4" width="36" height="36" rx="10" stroke="currentColor" stroke-width="1.5"/>
            <path d="M22 14v16M16 18l6-6 6 6M16 26l6 6 6-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h2 class="card-title">毛利抽成</h2>
        <p class="card-desc">查询分成比例与结算规则</p>
        <div class="card-tags">
          <span>分成比例</span>
          <span>结算规则</span>
          <span>收益分析</span>
        </div>
        <div class="card-arrow">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M5 10h10M12 7l3 3-3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </router-link>
    </div>

    <div class="bottom-hint">
      <span class="hint-dot"></span>
      选择一个场景开始探索
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.home {
  max-width: 1100px;
  margin: 0 auto;
  padding: 60px 40px 40px;
  position: relative;
  z-index: 1;
  flex: 1;
}

.hero {
  text-align: center;
  margin-bottom: 64px;
  position: relative;
  animation: fadeUp 0.8s ease;
}

.hero-badge {
  display: inline-block;
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 3px;
  color: var(--accent);
  background: var(--accent-dim);
  padding: 6px 16px;
  border-radius: 20px;
  margin-bottom: 24px;
  border: 1px solid var(--glow);
}

.hero-title {
  font-family: var(--font-display);
  font-size: 52px;
  font-weight: 700;
  line-height: 1.15;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.title-line {
  color: var(--text-primary);
  letter-spacing: -0.03em;
}

.title-line.accent {
  background: linear-gradient(135deg, var(--accent) 0%, color-mix(in srgb, var(--accent) 70%, white) 50%, var(--accent) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 16px;
  color: var(--text-secondary);
  max-width: 500px;
  margin: 0 auto;
}

.hero-glow {
  position: absolute;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--glow) 0%, transparent 60%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.scene-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.scene-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 32px 28px;
  background: var(--bg-card);
  border-radius: 16px;
  border: 1px solid var(--border-subtle);
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  overflow: hidden;
  animation: fadeUp 0.6s ease backwards;
  animation-delay: calc(var(--delay) * 0.1s + 0.3s);
}

.scene-card:hover {
  transform: translateY(-4px);
  border-color: var(--border-default);
  background: var(--bg-elevated);
}

.card-risk:hover {
  box-shadow: 0 8px 40px rgba(212, 168, 67, 0.08);
}
.card-model:hover {
  box-shadow: 0 8px 40px rgba(124, 58, 237, 0.08);
}
.card-simulation:hover {
  box-shadow: 0 8px 40px rgba(245, 158, 11, 0.08);
}
.card-profit:hover {
  box-shadow: 0 8px 40px rgba(16, 185, 129, 0.08);
}

.card-glow {
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.4s ease;
}

.card-risk .card-glow {
  background: radial-gradient(circle, rgba(212, 168, 67, 0.08) 0%, transparent 60%);
}
.card-model .card-glow {
  background: radial-gradient(circle, rgba(124, 58, 237, 0.08) 0%, transparent 60%);
}
.card-simulation .card-glow {
  background: radial-gradient(circle, rgba(245, 158, 11, 0.08) 0%, transparent 60%);
}
.card-profit .card-glow {
  background: radial-gradient(circle, rgba(16, 185, 129, 0.08) 0%, transparent 60%);
}

.scene-card:hover .card-glow {
  opacity: 1;
}

.card-icon {
  color: var(--text-muted);
  margin-bottom: 20px;
  transition: color 0.3s ease;
}

.card-risk:hover .card-icon { color: var(--accent-risk); }
.card-model:hover .card-icon { color: var(--accent-model); }
.card-simulation:hover .card-icon { color: var(--accent-simulation); }
.card-profit:hover .card-icon { color: var(--accent-profit); }

.card-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  letter-spacing: -0.01em;
}

.card-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.card-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.card-tags span {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 10px;
  color: var(--text-muted);
  border: 1px solid var(--border-subtle);
}

.card-risk:hover .card-tags span {
  border-color: rgba(212, 168, 67, 0.2);
  color: var(--accent-risk);
}
.card-model:hover .card-tags span {
  border-color: rgba(124, 58, 237, 0.2);
  color: var(--accent-model);
}
.card-simulation:hover .card-tags span {
  border-color: rgba(245, 158, 11, 0.2);
  color: var(--accent-simulation);
}
.card-profit:hover .card-tags span {
  border-color: rgba(16, 185, 129, 0.2);
  color: var(--accent-profit);
}

.card-arrow {
  position: absolute;
  bottom: 28px;
  right: 28px;
  color: var(--text-muted);
  opacity: 0;
  transform: translateX(-8px);
  transition: all 0.3s ease;
}

.scene-card:hover .card-arrow {
  opacity: 1;
  transform: translateX(0);
}

.card-risk:hover .card-arrow { color: var(--accent-risk); }
.card-model:hover .card-arrow { color: var(--accent-model); }
.card-simulation:hover .card-arrow { color: var(--accent-simulation); }
.card-profit:hover .card-arrow { color: var(--accent-profit); }

.bottom-hint {
  text-align: center;
  margin-top: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-muted);
  animation: fadeUp 0.6s ease 0.8s backwards;
}

.hint-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulse 2s infinite;
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(20px);
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

@media (max-width: 768px) {
  .home { padding: 40px 20px; }
  .hero-title { font-size: 36px; }
  .scene-grid { grid-template-columns: 1fr; }
  .scene-card { padding: 24px 20px; }
}
</style>
