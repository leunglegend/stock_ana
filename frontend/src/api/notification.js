/**
 * 通知相关 API
 */
import http from './http'

export const notificationApi = {
  // 获取通知列表
  getList(params = {}) {
    return http.get('/notifications', { params }).then(res => res.data)
  },
  // 未读数量
  getUnreadCount() {
    return http.get('/notifications/unread-count').then(res => res.data)
  },
  // 标记已读
  markAsRead(id) {
    return http.put(`/notifications/${id}/read`).then(res => res.data)
  },
  // 全部已读
  markAllRead() {
    return http.put('/notifications/read-all').then(res => res.data)
  },
}
