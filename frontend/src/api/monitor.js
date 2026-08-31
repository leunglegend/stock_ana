/**
 * 盘中监控聚合 API
 */
import http from './http'

export function getMonitorOverview(params = {}) {
  return http.get('/monitor/overview', { params }).then((res) => res.data)
}

