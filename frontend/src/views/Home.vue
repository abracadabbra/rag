<template>
  <div class="home">
    <div class="hero">
      <h1>RAG 智能问答系统</h1>
      <p>基于检索增强生成，为您解答各领域专业问题</p>
    </div>

    <div class="scene-grid">
      <router-link to="/risk-rules" class="scene-card" style="--delay: 0">
        <div class="scene-icon">
          <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
            <rect width="56" height="56" rx="14" fill="#1890ff"/>
            <path d="M18 28h20M28 18v20" stroke="white" stroke-width="3" stroke-linecap="round"/>
          </svg>
        </div>
        <h2>风控规则问答</h2>
        <p>查询风控政策、制度与规则信息</p>
        <div class="scene-features">
          <span>政策查询</span>
          <span>规则解读</span>
          <span>合规建议</span>
        </div>
      </router-link>

      <router-link to="/model-cards" class="scene-card" style="--delay: 1">
        <div class="scene-icon">
          <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
            <rect width="56" height="56" rx="14" fill="#722ed1"/>
            <rect x="14" y="14" width="28" height="28" rx="5" stroke="white" stroke-width="2.5" fill="none"/>
            <circle cx="28" cy="28" r="7" stroke="white" stroke-width="2.5" fill="none"/>
          </svg>
        </div>
        <h2>模型卡片查询</h2>
        <p>查询模型部署、特征与适用场景</p>
        <div class="scene-features">
          <span>部署信息</span>
          <span>模型特征</span>
          <span>选型建议</span>
        </div>
      </router-link>

      <router-link to="/simulation" class="scene-card" style="--delay: 2">
        <div class="scene-icon">
          <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
            <rect width="56" height="56" rx="14" fill="#fa8c16"/>
            <path d="M18 38V24l10-8 10 8v14" stroke="white" stroke-width="2.5" fill="none" stroke-linejoin="round"/>
            <circle cx="28" cy="30" r="3" stroke="white" stroke-width="2" fill="none"/>
          </svg>
        </div>
        <h2>仿真解读</h2>
        <p>解读仿真结果与分析模型表现</p>
        <div class="scene-features">
          <span>结果分析</span>
          <span>性能对比</span>
          <span>数据洞察</span>
        </div>
      </router-link>

      <router-link to="/profit" class="scene-card" style="--delay: 3">
        <div class="scene-icon">
          <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
            <rect width="56" height="56" rx="14" fill="#52c41a"/>
            <path d="M28 16v24M18 24l10-8 10 8M18 32l10 8 10-8" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h2>毛利抽成查询</h2>
        <p>查询分成比例与结算规则</p>
        <div class="scene-features">
          <span>分成比例</span>
          <span>结算规则</span>
          <span>收益分析</span>
        </div>
      </router-link>
    </div>

    <div class="tips">
      <p>选择一个场景开始探索，或直接向下滚动查看更多信息</p>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.home {
  max-width: 1100px;
  margin: 0 auto;
  padding: 80px 40px;
}

.hero {
  text-align: center;
  margin-bottom: 80px;
  animation: fadeInUp 0.6s ease;
}

.hero h1 {
  font-size: 42px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 16px 0;
  letter-spacing: -0.02em;
}

.hero p {
  font-size: 18px;
  color: #666;
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
  padding: 40px 32px;
  background: white;
  border-radius: 20px;
  text-decoration: none;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  border: 1px solid rgba(0, 0, 0, 0.04);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  animation: fadeInUp 0.5s ease backwards;
  animation-delay: calc(var(--delay) * 0.1s + 0.2s);
}

.scene-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
}

.scene-icon {
  margin-bottom: 24px;
  transition: transform 0.3s ease;
}

.scene-card:hover .scene-icon {
  transform: scale(1.05);
}

.scene-card h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
}

.scene-card p {
  font-size: 14px;
  color: #666;
  margin: 0 0 20px 0;
  text-align: center;
}

.scene-features {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.scene-features span {
  font-size: 12px;
  padding: 4px 12px;
  background: #f5f5f5;
  border-radius: 12px;
  color: #666;
}

.tips {
  text-align: center;
  margin-top: 60px;
  animation: fadeIn 0.6s ease 0.6s backwards;
}

.tips p {
  font-size: 14px;
  color: #999;
  margin: 0;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media (max-width: 768px) {
  .home {
    padding: 40px 20px;
  }

  .hero h1 {
    font-size: 32px;
  }

  .scene-grid {
    grid-template-columns: 1fr;
  }
}
</style>
