/**
 * 路由配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import { reportApi } from '@/api/report'
import { useUserStore } from '@/store/user'

const LOGIN_REQUIRED_EVENT = 'show-login'
const APP_TITLE_SUFFIX = ' - 智能股票分析平台'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { title: '首页', icon: 'Odometer' },
  },
  {
    path: '/monitor',
    name: 'Monitor',
    component: () => import('../views/Monitor.vue'),
    meta: { title: '盘中监控', icon: 'Monitor', requiresAuth: true },
  },
  {
    path: '/watchlist',
    name: 'Watchlist',
    component: () => import('../views/Watchlist.vue'),
    meta: { title: '自选股', icon: 'Star', requiresAuth: true },
  },
  {
    path: '/board',
    name: 'Board',
    component: () => import('../views/BoardMonitor.vue'),
    meta: { title: '板块监控', icon: 'DataAnalysis' },
  },
  {
    path: '/us',
    name: 'UsMarket',
    component: () => import('../views/UsMarket.vue'),
    meta: { title: '美股复盘', icon: 'Globe' },
  },
  // 二期：美股个股详情占位（本期不实现）
  // { path: '/us/stock/:symbol', name: 'UsStockDetail', component: () => import('../views/UsStockDetail.vue'), meta: { hidden: true } },
  {
    path: '/radar',
    name: 'Radar',
    component: () => import('../views/OpportunityRadar.vue'),
    meta: { title: '机会雷达', icon: 'TrendCharts' },
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('../views/Search.vue'),
    meta: { title: '搜索个股', icon: 'Search' },
  },
  {
    path: '/stock/:code',
    name: 'StockDetail',
    component: () => import('../views/StockDetail.vue'),
    meta: { title: '股票详情', hidden: true },
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('../views/Reports.vue'),
    meta: { title: '复盘报告', icon: 'Document', requiresAuth: true },
  },
  {
    path: '/reports/latest',
    name: 'LatestReport',
    beforeEnter: async () => {
      try {
        const data = await reportApi.getList({ page: 1, page_size: 20 })
        const latestReport = (data.items || []).find((item) => item.status === 'completed')
        if (!latestReport) return { path: '/reports' }

        return { name: 'ReportDetail', params: { id: latestReport.id } }
      } catch {
        return { path: '/reports' }
      }
    },
    meta: { title: '报告详情', hidden: true, requiresAuth: true },
  },
  {
    path: '/reports/:id',
    name: 'ReportDetail',
    component: () => import('../views/ReportDetail.vue'),
    meta: { title: '报告详情', hidden: true, requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

function isProtectedRoute(route) {
  return route.matched.some((record) => record.meta.requiresAuth)
}

function resolveFallbackRoute(from) {
  const canStayOnFromRoute = from.matched.length > 0 && !isProtectedRoute(from)

  if (!canStayOnFromRoute) {
    return { path: '/', replace: true }
  }

  if (from.name) {
    return {
      name: from.name,
      params: from.params,
      query: from.query,
      hash: from.hash,
      replace: true,
    }
  }

  return {
    path: from.path,
    query: from.query,
    hash: from.hash,
    replace: true,
  }
}

function updateDocumentTitle(route) {
  document.title = `${route.meta.title || '股票分析'}${APP_TITLE_SUFFIX}`
}

// 需要登录的路由（未登录弹出登录框，停留在当前页面）
router.beforeEach(async (to, from) => {
  if (!isProtectedRoute(to)) {
    return true
  }

  const userStore = useUserStore()
  await userStore.initializeAuth()

  if (!userStore.isLoggedIn) {
    userStore.setPendingRoute(to.fullPath)
    window.dispatchEvent(new CustomEvent(LOGIN_REQUIRED_EVENT, {
      detail: { targetPath: to.fullPath },
    }))
    return resolveFallbackRoute(from)
  }

  return true
})

router.afterEach((to, from, failure) => {
  if (failure) return

  updateDocumentTitle(to)
  if (to.path === from.path) return
  window.requestAnimationFrame(() => {
    const title = document.querySelector('[data-page-title]')
    if (!(title instanceof HTMLElement)) return
    title.tabIndex = -1
    title.focus()
  })
})

export default router
