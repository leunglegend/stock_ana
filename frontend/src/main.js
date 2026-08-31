import { createApp } from 'vue'

import router from './router'
import { pinia, useWatchlistStore } from './store'
import { installElementPlus } from './plugins/elementPlus'
import { initializeTheme } from './theme'
import './style.css'
import App from './App.vue'

initializeTheme()
const app = createApp(App)

installElementPlus(app)
app.use(router)
app.use(pinia)

// 初始化自选股 store（监听登录状态，自动切换云端/本地模式）
const watchlistStore = useWatchlistStore()
watchlistStore.init()

app.mount('#app')
