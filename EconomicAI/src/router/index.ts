import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true }
    }
  ]
})

// Proteção de rotas: Verifica se existe um token simulado no localStorage
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('auth_token')
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    // Se a rota exige login e não está autenticado, manda pro /login
    next({ name: 'login' })
  } else if (to.name === 'login' && isAuthenticated) {
    // Se está logado e tenta acessar a tela de login, manda pro dashboard
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router