import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

import Home from './views/Home.vue'
import RiskRulesQA from './views/RiskRulesQA.vue'
import ModelCardsQA from './views/ModelCardsQA.vue'
import SimulationQA from './views/SimulationQA.vue'
import ProfitQA from './views/ProfitQA.vue'
import ApiSettings from './views/ApiSettings.vue'

const routes = [
  { path: '/', name: 'home', component: Home },
  { path: '/risk-rules', name: 'risk-rules', component: RiskRulesQA },
  { path: '/model-cards', name: 'model-cards', component: ModelCardsQA },
  { path: '/simulation', name: 'simulation', component: SimulationQA },
  { path: '/profit', name: 'profit', component: ProfitQA },
  { path: '/settings', name: 'settings', component: ApiSettings },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

createApp(App).use(router).mount('#app')
