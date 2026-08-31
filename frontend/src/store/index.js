/**
 * Pinia 全局状态管理
 */
import { createPinia, defineStore } from 'pinia'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'

import { watchlistApi } from '../api/watchlist'
import { adaptGroupFromCloud } from './watchlistAdapters'
import {
  handleWatchlistLogin,
  handleWatchlistLogout,
  enterCloudMode,
  initWatchlistStore,
  syncLocalToCloudAndEnter,
} from './watchlistModeActions'
import { loadWatchlistLocal, saveWatchlistLocal } from './watchlistPersistence'

export const pinia = createPinia()

// ===== Store 定义 =====
export const useWatchlistStore = defineStore('watchlist', {
  state: () => {
    const data = loadWatchlistLocal()
    return {
      // 是否云端模式
      cloudMode: false,
      // 云端模式错误态
      cloudError: '',
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
    init: initWatchlistStore,

    // 登录后处理：切换云端模式 + 首次同步提示
    _handleLogin: handleWatchlistLogin,

    // 登出后处理：切回本地模式
    _handleLogout: handleWatchlistLogout,

    // 进入云端模式：拉取云端数据
    _enterCloudMode: enterCloudMode,

    // 将本地数据同步到云端，然后进入云端模式
    _syncLocalToCloudAndEnter: syncLocalToCloudAndEnter,

    // ===== 增删改操作（根据模式自动分派）=====

    async addStock(stock) {
      const result = await this.addStockToGroup(this.activeGroup, stock)
      return result.success
    },

    async addStockToGroup(groupId, stock) {
      const group = this.groups.find(g => g.id === groupId)
      if (!group) {
        return { success: false, reason: 'group-not-found' }
      }
      if (group.stocks.some(s => s.code === stock.code)) {
        return { success: false, reason: 'duplicate', groupName: group.name }
      }

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
          return { success: true, groupId, groupName: group.name }
        } catch (e) {
          console.error('添加股票失败:', e)
          ElMessage.error('添加失败')
          return { success: false, reason: 'request-failed', groupName: group.name }
        }
      }

      group.stocks.push({
        code: stock.code,
        name: stock.name,
        cost: stock.cost || 0,
        remark: stock.remark || '',
      })
      this._persist()
      return { success: true, groupId, groupName: group.name }
    },

    // 移除股票
    async removeStock(code, groupId = this.activeGroup) {
      const group = this.groups.find(g => g.id === groupId)
      if (!group) return false
      const stock = group.stocks.find(s => s.code === code)
      if (!stock) return false

      if (this.cloudMode) {
        if (!stock._id) {
          ElMessage.error('云端数据异常，请刷新后重试')
          return false
        }
        try {
          await watchlistApi.deleteItem(stock._id)
          group.stocks = group.stocks.filter(s => s.code !== code)
          return true
        } catch (e) {
          console.error('删除股票失败:', e)
          ElMessage.error('删除失败')
          return false
        }
      }

      group.stocks = group.stocks.filter(s => s.code !== code)
      this._persist()
      return true
    },

    async updateStock(code, payload, groupId = this.activeGroup) {
      const group = this.groups.find(g => g.id === groupId)
      if (!group) return { success: false, reason: 'group-not-found' }
      const stock = group.stocks.find(s => s.code === code)
      if (!stock) return { success: false, reason: 'stock-not-found' }

      const nextPayload = {
        cost: payload.cost ?? stock.cost ?? 0,
        remark: payload.remark ?? stock.remark ?? '',
      }

      if (this.cloudMode) {
        if (!stock._id) {
          ElMessage.error('云端数据异常，请刷新后重试')
          return { success: false, reason: 'missing-cloud-id' }
        }
        try {
          const res = await watchlistApi.updateItem(stock._id, nextPayload)
          stock.cost = res.data.cost || 0
          stock.remark = res.data.remark || ''
          return { success: true }
        } catch (e) {
          console.error('更新自选股失败:', e)
          ElMessage.error('更新失败')
          return { success: false }
        }
      }

      stock.cost = nextPayload.cost
      stock.remark = nextPayload.remark
      this._persist()
      return { success: true }
    },

    // 更新持仓成本
    async updateCost(code, cost) {
      const result = await this.updateStock(code, { cost })
      return result?.success || false
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

    async renameGroup(groupId, name) {
      const group = this.groups.find(item => item.id === groupId)
      if (!group) return false

      if (this.cloudMode) {
        try {
          const res = await watchlistApi.updateGroup(Number(groupId), name)
          group.name = res.data.name
          return true
        } catch (e) {
          console.error('重命名分组失败:', e)
          ElMessage.error('重命名失败')
          return false
        }
      }

      group.name = name
      this._persist()
      return true
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
    isWatched(code, groupId = null) {
      if (groupId) {
        const group = this.groups.find(item => item.id === groupId)
        return Boolean(group?.stocks.some(stock => stock.code === code))
      }
      return this.groups.some(group => group.stocks.some(stock => stock.code === code))
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
