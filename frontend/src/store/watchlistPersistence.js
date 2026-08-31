const STORAGE_KEY = 'stock_watchlist'

function createDefaultWatchlistData() {
  return {
    groups: [
      { id: 'default', name: '我的自选', stocks: [] },
    ],
    activeGroup: 'default',
  }
}

export function loadWatchlistLocal() {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    if (data) return JSON.parse(data)
  } catch (error) {
    console.error('加载自选股失败:', error)
  }

  return createDefaultWatchlistData()
}

export function saveWatchlistLocal(data) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (error) {
    console.error('保存自选股失败:', error)
  }
}

export function hasLocalData() {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    if (!data) return false

    const parsed = JSON.parse(data)
    return parsed.groups?.some((group) => group.stocks && group.stocks.length > 0)
  } catch {
    return false
  }
}
