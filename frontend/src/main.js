import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

import Home from './views/Home.vue'
import RiskRulesQA from './views/RiskRulesQA.vue'
import ModelCardsQA from './views/ModelCardsQA.vue'

const routes = [
  { path: '/', name: 'home', component: Home },
  { path: '/risk-rules', name: 'risk-rules', component: RiskRulesQA },
  { path: '/model-cards', name: 'model-cards', component: ModelCardsQA },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

createApp(App).use(router).mount('#app')
