import { createRouter, createWebHistory } from 'vue-router'
import DashboardPage from '../pages/DashboardPage.vue'
import SimulatorPage from '../pages/SimulatorPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardPage },
    { path: '/replay', name: 'replay', component: () => import('../pages/ReplayPage.vue') },
    { path: '/simulator', name: 'simulator', component: SimulatorPage },
    { path: '/model-analysis', name: 'model-analysis', component: () => import('../pages/ModelAnalysisPage.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

export default router
