// 美股复盘 API（收盘口径；对应后端 /api/us）
import http from './http'

// GET /api/us/summary —— Dashboard 卡与页面摘要区共用
export function getUsSummary() {
  return http.get('/us/summary').then(res => res.data)
}

// GET /api/us/sectors —— 11 个 GICS 板块涨跌榜（后端已按涨幅降序）
export function getUsSectors() {
  return http.get('/us/sectors').then(res => res.data)
}

// GET /api/us/sectors/{name}/constituents —— 板块成分按涨跌幅降序
export function getUsSectorStocks(name) {
  return http.get(`/us/sectors/${encodeURIComponent(name)}/constituents`).then(res => res.data)
}

// GET /api/us/ai-summary —— AI 一句话复盘（SSE），[DONE] 收尾
export function getUsAiSummary(onMessage, onDone, onError) {
  const eventSource = new EventSource('/api/us/ai-summary')
  eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
      eventSource.close()
      onDone && onDone()
      return
    }
    onMessage && onMessage(event.data)
  }
  eventSource.onerror = () => {
    eventSource.close()
    onError && onError(new Error('美股 AI 摘要连接中断'))
  }
  return eventSource
}
