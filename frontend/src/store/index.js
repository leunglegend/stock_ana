/**
 * Pinia 全局状态管理
 */
import { createPinia, defineStore, storeToRefs } from 'pinia'
import { watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from './user'
import { watchlistApi } from '../api/watchlist'

export const pinia = createPinia()

// ===== 本地存储（localStorage 模式）=====
const STORAGE_KEY = 'stock_watchlist'

function loadWatchlistLocal() {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    if (data) return JSON.parse(data)
  } catch (e) {
    console.error('加载自选股失败:', e)
  }
  return {
    groups: [
      { id: 'default', name: '我的自选', stocks: [] },
    ],
    activeGroup: 'default',
  }
}

function saveWatchlistLocal(data) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (e) {
    console.error('保存自选股失败:', e)
  }
}

// 检查本地是否有用户自选股数据（非空默认值）
function hasLocalData() {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    if (!data) return false
    const parsed = JSON.parse(data)
    // 只要有任何一个分组里有股票，就算有数据
    return parsed.groups?.some(g => g.stocks && g.stocks.length > 0)
  } catch (e) {
    return false
  }
}

// ===== 云端数据适配 =====
// 后端返回: { id, name, sort_order, stocks: [{id, group_id, stock_code, stock_name, cost, remark}] }
// 前端统一: { id, name, stocks: [{_id, code, name, cost, remark}] }
function adaptGroupFromCloud(group) {
  return {
    id: String(group.id),
    name: group.name,
    stocks: (group.stocks || []).map(s => ({
      _id: s.id,
      code: s.stock_code,
      name: s.stock_name,
      cost: s.cost || 0,
      remark: s.remark || '',
    })),
  }
}

// 本地数据 -> 云端同步格式
function adaptGroupsToCloud(groups) {
  return groups.map(g => ({
    id: isNaN(Number(g.id)) ? undefined : Number(g.id),
    name: g.name,
    stocks: (g.stocks || []).map(s => ({
      stock_code: s.code,
      stock_name: s.name,
      cost: s.cost || 0,
      remark: s.remark || '',
    })),
  }))
}

// ===== Store 定义 =====
export const useWatchlistStore = defineStore('watchlist', {
  state: () => {
    const data = loadWatchlistLocal()
    return {
      // 是否云端模式
      cloudMode: false,
      // 分组数据（前端统一结构）
      groups: data.groups,
      activeGroup: data.activeGroup,
      // 加载状态
      loading: false,
      // 是否已完成首次登录同步提示（避免重复弹框）
      _syncPromptShown: false,
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
    // ===== 模式切换 =====

    // 初始化：监听用户登录状态
    init() {
      const userStore = useUserStore()

      // 监听登录状态
      watch(
        () => userStore.isLoggedIn,
        (loggedIn) => {
          if (loggedIn) {
            this._handleLogin()
          } else {
            this._handleLogout()
          }
        },
        { immediate: true }
      )
    },

    // 登录后处理：切换云端模式 + 首次同步提示
    async _handleLogin() {
      // 如果本地有数据且从未提示过同步，弹框询问
      if (!this._syncPromptShown && hasLocalData()) {
        this._syncPromptShown = true
        try {
          await ElMessageBox.confirm(
            '检测到本地有自选股数据，是否同步到云端？\n\n选择「同步」将把本地数据合并到云端；选择「不同步」则直接使用云端数据。',
            '自选股同步提示',
            {
              confirmButtonText: '同步到云端',
              cancelButtonText: '使用云端数据',
              type: 'info',
              distinguishCancelAndClose: true,
            }
          )
          // 用户确认同步
          await this._syncLocalToCloudAndEnter()
          ElMessage.success('同步成功')
          return
        } catch (action) {
          // cancel: 用户选择使用云端数据
          // close: 用户关闭弹窗，也默认使用云端数据
          if (action === 'cancel' || action === 'close') {
            await this._enterCloudMode()
            return
          }
        }
      }

      // 没有本地数据或已提示过，直接进入云端模式
      await this._enterCloudMode()
    },

    // 登出后处理：切回本地模式
    _handleLogout() {
      this.cloudMode = false
      const data = loadWatchlistLocal()
      this.groups = data.groups
      this.activeGroup = data.activeGroup
      this._syncPromptShown = false
    },

    // 进入云端模式：拉取云端数据
    async _enterCloudMode() {
      this.loading = true
      try {
        const res = await watchlistApi.getGroups()
        const cloudGroups = res.data || []
        this.groups = cloudGroups.map(adaptGroupFromCloud)
        if (this.groups.length > 0) {
          // 保持当前 activeGroup 若存在，否则用第一个
          const exists = this.groups.some(g => g.id === this.activeGroup)
          if (!exists) {
            this.activeGroup = this.groups[0].id
          }
        } else {
          // 云端没有分组，创建默认分组
          const createRes = await watchlistApi.createGroup('我的自选')
          this.groups = [adaptGroupFromCloud(createRes.data)]
          this.activeGroup = this.groups[0].id
        }
        this.cloudMode = true
      } catch (e) {
        console.error('加载云端自选股失败:', e)
        ElMessage.error('加载自选股失败，请稍后重试')
      } finally {
        this.loading = false
      }
    },

    // 将本地数据同步到云端，然后进入云端模式
    async _syncLocalToCloudAndEnter() {
      this.loading = true
      try {
        const localData = loadWatchlistLocal()
        const cloudGroups = adaptGroupsToCloud(localData.groups)
        // replace=false 表示合并（如果云端有数据则追加）
        await watchlistApi.sync(cloudGroups, false)
        // 同步后重新拉取
        const res = await watchlistApi.getGroups()
        const groups = res.data || []
        this.groups = groups.map(adaptGroupFromCloud)
        if (this.groups.length > 0) {
          this.activeGroup = this.groups[0].id
        }
        this.cloudMode = true
      } catch (e) {
        console.error('同步自选股失败:', e)
        ElMessage.error('同步失败，请稍后重试')
        throw e
      } finally {
        this.loading = false
      }
    },

    // ===== 增删改操作（根据模式自动分派）=====

    // 添加股票到当前分组
    async addStock(stock) {
      const group = this.groups.find(g => g.id === this.activeGroup)
      if (!group) return false
      // 避免重复
      if (group.stocks.some(s => s.code === stock.code)) return false

      if (this.cloudMode) {
        try {
          const res = await watchlistApi.addItem(
            Number(group.id),
            stock.code,
            stock.name,
            stock.cost || 0,
            stock.remark || ''
          )
          const item = res.data
          group.stocks.push({
            _id: item.id,
            code: item.stock_code,
            name: item.stock_name,
            cost: item.cost || 0,
            remark: item.remark || '',
          })
          return true
        } catch (e) {
          console.error('添加股票失败:', e)
          ElMessage.error('添加失败')
          return false
        }
      } else {
        group.stocks.push({
          code: stock.code,
          name: stock.name,
          cost: stock.cost || 0,
          remark: stock.remark || '',
        })
        this._persist()
        return true
      }
    },

    // 移除股票
    async removeStock(code) {
      const group = this.groups.find(g => g.id === this.activeGroup)
      if (!group) return
      const stock = group.stocks.find(s => s.code === code)
      if (!stock) return

      if (this.cloudMode && stock._id) {
        try {
          await watchlistApi.deleteItem(stock._id)
          group.stocks = group.stocks.filter(s => s.code !== code)
        } catch (e) {
          console.error('删除股票失败:', e)
          ElMessage.error('删除失败')
        }
      } else {
        group.stocks = group.stocks.filter(s => s.code !== code)
        this._persist()
      }
    },

    // 更新持仓成本
    async updateCost(code, cost) {
      const group = this.groups.find(g => g.id === this.activeGroup)
      if (!group) return
      const stock = group.stocks.find(s => s.code === code)
      if (!stock) return

      if (this.cloudMode && stock._id) {
        try {
          await watchlistApi.updateItem(stock._id, { cost })
          stock.cost = cost
        } catch (e) {
          console.error('更新成本失败:', e)
          ElMessage.error('更新失败')
        }
      } else {
        stock.cost = cost
        this._persist()
      }
    },

    // 切换分组
    setActiveGroup(groupId) {
      this.activeGroup = groupId
      if (!this.cloudMode) {
        this._persist()
      }
    },

    // 新建分组
    async addGroup(name) {
      if (this.cloudMode) {
        try {
          const res = await watchlistApi.createGroup(name)
          const group = adaptGroupFromCloud(res.data)
          this.groups.push(group)
          return group.id
        } catch (e) {
          console.error('新建分组失败:', e)
          ElMessage.error('创建失败')
          return null
        }
      } else {
        const id = 'g_' + Date.now()
        this.groups.push({ id, name, stocks: [] })
        this._persist()
        return id
      }
    },

    // 删除分组
    async removeGroup(groupId) {
      if (this.groups.length <= 1) return false

      if (this.cloudMode) {
        try {
          await watchlistApi.deleteGroup(Number(groupId))
          this.groups = this.groups.filter(g => g.id !== groupId)
          if (this.activeGroup === groupId) {
            this.activeGroup = this.groups[0].id
          }
          return true
        } catch (e) {
          console.error('删除分组失败:', e)
          ElMessage.error('删除失败')
          return false
        }
      } else {
        this.groups = this.groups.filter(g => g.id !== groupId)
        if (this.activeGroup === groupId) {
          this.activeGroup = this.groups[0].id
        }
        this._persist()
        return true
      }
    },

    // 检查是否已收藏
    isWatched(code) {
      const group = this.groups.find(g => g.id === this.activeGroup)
      if (!group) return false
      return group.stocks.some(s => s.code === code)
    },

    // 本地持久化（仅 localStorage 模式使用）
    _persist() {
      if (this.cloudMode) return
      saveWatchlistLocal({
        groups: this.groups,
        activeGroup: this.activeGroup,
      })
    },
  },
})
