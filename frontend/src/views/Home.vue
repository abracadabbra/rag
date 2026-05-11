<template>
  <div class="home">
    <div class="hero">
      <h1>RAG 智能问答系统</h1>
      <p>基于检索增强生成的智能问答，支持多场景知识库查询</p>
    </div>

    <div class="scene-grid">
      <router-link to="/risk-rules" class="scene-card">
        <div class="scene-icon risk">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="#1890ff"/>
            <path d="M14 24h20M24 14v20" stroke="white" stroke-width="3" stroke-linecap="round"/>
          </svg>
        </div>
        <h2>风控规则问答</h2>
        <p>查询风控政策、制度、规则信息</p>
      </router-link>

      <router-link to="/model-cards" class="scene-card">
        <div class="scene-icon model">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="#722ed1"/>
            <rect x="12" y="12" width="24" height="24" rx="4" stroke="white" stroke-width="2.5" fill="none"/>
            <circle cx="24" cy="24" r="6" stroke="white" stroke-width="2.5" fill="none"/>
          </svg>
        </div>
        <h2>模型卡片查询</h2>
        <p>查询模型部署、特征、场景信息</p>
      </router-link>

      <div class="scene-card disabled">
        <div class="scene-icon simulation">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="#fa8c16"/>
            <path d="M14 34V22l10-8 10 8v12" stroke="white" stroke-width="2.5" fill="none" stroke-linejoin="round"/>
            <circle cx="24" cy="28" r="4" stroke="white" stroke-width="2.5" fill="none"/>
          </svg>
        </div>
        <h2>仿真解读</h2>
        <p>即将上线</p>
      </div>

      <div class="scene-card disabled">
        <div class="scene-icon profit">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <rect width="48" height="48" rx="12" fill="#52c41a"/>
            <path d="M24 14v20M18 20l6-6 6 6M18 28l6 6 6-6" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h2>毛利抽成查询</h2>
        <p>即将上线</p>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.home {
  max-width: 900px;
  margin: 0 auto;
  padding: 60px 24px;
}

.hero {
  text-align: center;
  margin-bottom: 60px;
}

.hero h1 {
  font-size: 36px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 16px 0;
}

.hero p {
  font-size: 18px;
  color: #8c8c8c;
  margin: 0;
}

.scene-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.scene-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 24px;
  background: white;
  border-radius: 16px;
  text-decoration: none;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.scene-card:not(.disabled):hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  border-color: #1890ff;
}

.scene-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.scene-icon {
  margin-bottom: 20px;
}

.scene-card h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
}

.scene-card p {
  font-size: 14px;
  color: #8c8c8c;
  margin: 0;
}

@media (max-width: 600px) {
  .scene-grid {
    grid-template-columns: 1fr;
  }
}
</style>
