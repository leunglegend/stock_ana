/**
 * 股票 API 封装
 */
import axios from 'axios'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 搜索股票
export function searchStock(keyword) {
  return request.get('/stock/search', { params: { q: keyword } })
    .then(res => res.data)
}

// 获取股票基本信息
export function getStockInfo(code) {
  return request.get(`/stock/${code}`)
    .then(res => res.data)
}

// 获取K线数据
export function getKlineData(code, period = 'daily', days = 250) {
  return request.get(`/stock/${code}/kline`, { params: { period, days } })
    .then(res => res.data)
}

// 获取财务数据
export function getFinancialData(code) {
  return request.get(`/stock/${code}/financial`)
    .then(res => res.data)
}

// 行业板块列表
export function getBoardIndustry() {
  return request.get('/board/industry')
    .then(res => res.data)
}

// 概念板块列表
export function getBoardConcept() {
  return request.get('/board/concept')
    .then(res => res.data)
}

// 板块成分股
export function getBoardStocks(boardType, boardName) {
  return request.get(`/board/${boardType}/${encodeURIComponent(boardName)}/stocks`)
    .then(res => res.data)
}

// 市场概览
export function getMarketSummary() {
  return request.get('/board/market/summary')
    .then(res => res.data)
}

// AI 市场点评（SSE 流式）
export function getMarketAiSummary(onMessage, onDone, onError) {
  const eventSource = new EventSource('/api/board/market/ai-summary')

  eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
      eventSource.close()
      onDone && onDone()
    } else {
      onMessage && onMessage(event.data)
    }
  }

  eventSource.onerror = (err) => {
    eventSource.close()
    onError && onError(err)
  }

  return eventSource
}

// AI 分析（SSE 流式）
export function analyzeStock(code, onMessage, onDone, onError) {
  const eventSource = new EventSource(`/api/stock/${code}/analyze`)

  eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
      eventSource.close()
      onDone && onDone()
    } else {
      onMessage && onMessage(event.data)
    }
  }

  eventSource.onerror = (err) => {
    eventSource.close()
    onError && onError(err)
  }

  return eventSource
}

export default request
