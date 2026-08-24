/**
 * 自选股相关 API
 */
import http from './http'

export const watchlistApi = {
  // 获取所有分组（含股票）
  getGroups() {
    return http.get('/watchlist/groups')
  },
  // 新建分组
  createGroup(name) {
    return http.post('/watchlist/groups', { name })
  },
  // 重命名分组
  updateGroup(id, name) {
    return http.put(`/watchlist/groups/${id}`, { name })
  },
  // 删除分组
  deleteGroup(id) {
    return http.delete(`/watchlist/groups/${id}`)
  },
  // 添加股票
  addItem(groupId, stockCode, stockName, cost = 0, remark = '') {
    return http.post('/watchlist/items', {
      group_id: groupId,
      stock_code: stockCode,
      stock_name: stockName,
      cost,
      remark,
    })
  },
  // 更新股票
  updateItem(id, data) {
    return http.put(`/watchlist/items/${id}`, data)
  },
  // 删除股票
  deleteItem(id) {
    return http.delete(`/watchlist/items/${id}`)
  },
  // 批量同步
  sync(groups, replace = false) {
    return http.post('/watchlist/sync', { groups, replace })
  },
}
