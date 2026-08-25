/**
 * 复盘报告相关 API
 */
import http from './http'

export const reportApi = {
  // 报告列表
  getList(params = {}) {
    return http.get('/reports', { params }).then(res => res.data)
  },
  // 报告详情
  getDetail(id) {
    return http.get(`/reports/${id}`).then(res => res.data)
  },
  // 手动生成今日报告
  generateToday() {
    return http.post('/reports/generate').then(res => res.data)
  },
}
