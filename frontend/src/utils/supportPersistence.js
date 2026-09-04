import { DEFAULT_SUPPORT } from './supportState.js'

const STORAGE_KEY = 'stock_support_v1'

export function loadSupportLocal() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { ...DEFAULT_SUPPORT }
    const parsed = JSON.parse(raw)
    return { ...DEFAULT_SUPPORT, ...parsed }
  } catch (error) {
    console.error('加载点赞/增资数据失败:', error)
    return { ...DEFAULT_SUPPORT }
  }
}

export function saveSupportLocal(state) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (error) {
    console.error('保存点赞/增资数据失败:', error)
  }
}
