/**
 * Pinia 全局状态管理
 */
import { createPinia, defineStore } from 'pinia'

export const pinia = createPinia()

// 自选股存储
const STORAGE_KEY = 'stock_watchlist'

function loadWatchlist() {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    if (data) return JSON.parse(data)
  } catch (e) {
    console.error('加载自选股失败:', e)
  }
  // 默认分组
  return {
    groups: [
      { id: 'default', name: '我的自选', stocks: [] },
    ],
    activeGroup: 'default',
  }
}

function saveWatchlist(data) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (e) {
    console.error('保存自选股失败:', e)
  }
}

export const useWatchlistStore = defineStore('watchlist', {
  state: () => {
    const data = loadWatchlist()
    return {
      groups: data.groups,
      activeGroup: data.activeGroup,
    }
  },

  getters: {
    activeStocks: (state) => {
      const group = state.groups.find(g => g.id === state.activeGroup)
      return group ? group.stocks : []
    },
    groupNames: (state) => {
      return state.groups.map(g => ({ id: g.id, name: g.name }))
    },
  },

  actions: {
    // 添加股票到当前分组
    addStock(stock) {
      const group = this.groups.find(g => g.id === this.activeGroup)
      if (!group) return false
      // 避免重复
      if (group.stocks.some(s => s.code === stock.code)) return false
      group.stocks.push({
        code: stock.code,
        name: stock.name,
        cost: stock.cost || 0,
        remark: stock.remark || '',
      })
      this._persist()
      return true
    },

    // 移除股票
    removeStock(code) {
      const group = this.groups.find(g => g.id === this.activeGroup)
      if (!group) return
      group.stocks = group.stocks.filter(s => s.code !== code)
      this._persist()
    },

    // 更新持仓成本
    updateCost(code, cost) {
      const group = this.groups.find(g => g.id === this.activeGroup)
      if (!group) return
      const stock = group.stocks.find(s => s.code === code)
      if (stock) {
        stock.cost = cost
        this._persist()
      }
    },

    // 切换分组
    setActiveGroup(groupId) {
      this.activeGroup = groupId
      this._persist()
    },

    // 新建分组
    addGroup(name) {
      const id = 'g_' + Date.now()
      this.groups.push({ id, name, stocks: [] })
      this._persist()
      return id
    },

    // 删除分组
    removeGroup(groupId) {
      if (this.groups.length <= 1) return false
      this.groups = this.groups.filter(g => g.id !== groupId)
      if (this.activeGroup === groupId) {
        this.activeGroup = this.groups[0].id
      }
      this._persist()
      return true
    },

    // 检查是否已收藏
    isWatched(code) {
      const group = this.groups.find(g => g.id === this.activeGroup)
      if (!group) return false
      return group.stocks.some(s => s.code === code)
    },

    // 持久化
    _persist() {
      saveWatchlist({
        groups: this.groups,
        activeGroup: this.activeGroup,
      })
    },
  },
})
