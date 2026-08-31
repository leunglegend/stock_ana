import { watch } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { ElMessageBox } from 'element-plus/es/components/message-box/index.mjs'

import { watchlistApi } from '../api/watchlist'
import { useUserStore } from './user'
import { adaptGroupFromCloud, adaptGroupsToCloud } from './watchlistAdapters'
import { hasLocalData, loadWatchlistLocal } from './watchlistPersistence'

function beginCloudRequest(store) {
  const hadCloudState = store.cloudMode
  const snapshot = {
    hadCloudState,
    groups: hadCloudState ? store.groups : [],
    activeGroup: hadCloudState ? store.activeGroup : '',
  }

  store.cloudError = ''
  store.cloudMode = true
  if (!hadCloudState) {
    store.groups = []
    store.activeGroup = ''
  }

  return snapshot
}

function restoreCloudState(store, snapshot) {
  if (!snapshot.hadCloudState) {
    return
  }

  store.groups = snapshot.groups
  store.activeGroup = snapshot.activeGroup
}

export function initWatchlistStore() {
  const userStore = useUserStore()

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
}

export async function handleWatchlistLogin() {
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
      await this._syncLocalToCloudAndEnter()
      ElMessage.success('同步成功')
      return
    } catch (action) {
      if (action === 'cancel' || action === 'close') {
        await this._enterCloudMode()
      }
      return
    }
  }

  await this._enterCloudMode()
}

export function handleWatchlistLogout() {
  this.cloudMode = false
  this.cloudError = ''

  const data = loadWatchlistLocal()
  this.groups = data.groups
  this.activeGroup = data.activeGroup
  this._syncPromptShown = false
}

export async function enterCloudMode() {
  this.loading = true
  const snapshot = beginCloudRequest(this)

  try {
    const response = await watchlistApi.getGroups()
    const cloudGroups = response.data || []
    this.groups = cloudGroups.map(adaptGroupFromCloud)

    if (this.groups.length > 0) {
      const exists = this.groups.some((group) => group.id === this.activeGroup)
      if (!exists) {
        this.activeGroup = this.groups[0].id
      }
    } else {
      const createResponse = await watchlistApi.createGroup('我的自选')
      this.groups = [adaptGroupFromCloud(createResponse.data)]
      this.activeGroup = this.groups[0].id
    }
    this.cloudError = ''
  } catch (error) {
    restoreCloudState(this, snapshot)
    this.cloudError = '云端自选股暂时不可用，请重试'
    console.error('加载云端自选股失败:', error)
    ElMessage.error('加载自选股失败，请稍后重试')
  } finally {
    this.loading = false
  }
}

export async function syncLocalToCloudAndEnter() {
  this.loading = true
  const snapshot = beginCloudRequest(this)

  try {
    const localData = loadWatchlistLocal()
    const cloudGroups = adaptGroupsToCloud(localData.groups)
    await watchlistApi.sync(cloudGroups, false)

    const response = await watchlistApi.getGroups()
    const groups = response.data || []
    this.groups = groups.map(adaptGroupFromCloud)

    if (this.groups.length > 0) {
      this.activeGroup = this.groups[0].id
    }
    this.cloudError = ''
  } catch (error) {
    restoreCloudState(this, snapshot)
    this.cloudError = '同步云端自选股失败，请重试'
    console.error('同步自选股失败:', error)
    ElMessage.error('同步失败，请稍后重试')
    throw error
  } finally {
    this.loading = false
  }
}
