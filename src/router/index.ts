import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: () => import('../pages/DashboardPage.vue') },
    { path: '/replay', name: 'replay', component: () => import('../pages/ReplayPage.vue') },
    { path: '/simulator', name: 'simulator', component: () => import('../pages/SimulatorPage.vue') },
    { path: '/model-analysis', name: 'model-analysis', component: () => import('../pages/ModelAnalysisPage.vue') },
  ],
})

export default router
