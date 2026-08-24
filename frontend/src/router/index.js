/**
 * 路由配置
 */
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { title: '首页', icon: 'Odometer' },
  },
  {
    path: '/watchlist',
    name: 'Watchlist',
    component: () => import('../views/Watchlist.vue'),
    meta: { title: '自选股', icon: 'Star' },
  },
  {
    path: '/board',
    name: 'Board',
    component: () => import('../views/BoardMonitor.vue'),
    meta: { title: '板块监控', icon: 'TrendCharts' },
  },
  {
    path: '/stock/:code',
    name: 'StockDetail',
    component: () => import('../views/StockDetail.vue'),
    meta: { title: '股票详情', hidden: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || '股票分析'} - 智能股票分析平台`
  next()
})

// 自选股页面需要登录（未登录弹出登录框，停留在当前页面）
router.beforeEach(async (to, from, next) => {
  if (to.path === '/watchlist') {
    const mod = await import('../store/user')
    const userStore = mod.useUserStore()
    if (!userStore.isLoggedIn) {
      window.dispatchEvent(new CustomEvent('show-login'))
      next(false)
      return
    }
  }
  next()
})

export default router
