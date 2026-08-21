<template>
  <el-card class="kline-card card-shadow" v-loading="loading">
    <template #header>
      <div class="card-header">
        <el-icon><TrendCharts /></el-icon>
        <span>K线走势</span>
        <div class="chart-actions">
          <el-radio-group v-model="period" size="small" @change="handlePeriodChange">
            <el-radio-button value="daily">日K</el-radio-button>
            <el-radio-button value="weekly">周K</el-radio-button>
            <el-radio-button value="monthly">月K</el-radio-button>
          </el-radio-group>
          <el-select v-model="indicator" size="small" class="indicator-select" @change="handleIndicatorChange">
            <el-option label="成交量" value="volume" />
            <el-option label="MACD" value="macd" />
            <el-option label="KDJ" value="kdj" />
            <el-option label="RSI" value="rsi" />
          </el-select>
        </div>
      </div>
    </template>

    <div v-if="klineData && klineData.kline && klineData.kline.length > 0" class="chart-container">
      <v-chart class="kline-chart" :option="chartOption" autoresize />
    </div>

    <div v-else class="empty-state">
      <el-empty description="暂无K线数据" :image-size="80" />
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { TrendCharts } from '@element-plus/icons-vue'

const props = defineProps({
  klineData: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const period = ref('daily')
const indicator = ref('volume') // volume / macd / kdj / rsi

const chartOption = computed(() => {
  if (!props.klineData || !props.klineData.kline || props.klineData.kline.length === 0) {
    return {}
  }

  const data = props.klineData.kline
  const dates = data.map(item => item.date)
  const klineData = data.map(item => [item.open, item.close, item.low, item.high])
  const volumes = data.map(item => item.volume)
  const ma5Data = data.map(item => item.ma5)
  const ma10Data = data.map(item => item.ma10)
  const ma20Data = data.map(item => item.ma20)

  // 计算成交量颜色：涨红跌绿
  const volumeColors = data.map(item => item.close >= item.open ? '#ef4444' : '#10b981')

  // ===== 副图指标数据 =====
  let subSeries = []
  let subLegend = []
  let subFormatter = null

  if (indicator.value === 'volume') {
    subLegend = ['成交量']
    subSeries = [
      {
        name: '成交量',
        type: 'bar',
        data: volumes.map((v, i) => ({
          value: v,
          itemStyle: { color: volumeColors[i] },
        })),
        xAxisIndex: 1,
        yAxisIndex: 1,
        barWidth: '60%',
      },
    ]
  } else if (indicator.value === 'macd') {
    subLegend = ['DIF', 'DEA', 'MACD']
    const difData = data.map(item => item.dif)
    const deaData = data.map(item => item.dea)
    const macdData = data.map(item => item.macd)
    subSeries = [
      {
        name: 'DIF',
        type: 'line',
        data: difData,
        xAxisIndex: 1,
        yAxisIndex: 1,
        showSymbol: false,
        lineStyle: { width: 1, color: '#f59e0b' },
      },
      {
        name: 'DEA',
        type: 'line',
        data: deaData,
        xAxisIndex: 1,
        yAxisIndex: 1,
        showSymbol: false,
        lineStyle: { width: 1, color: '#8b5cf6' },
      },
      {
        name: 'MACD',
        type: 'bar',
        data: macdData.map((v, i) => ({
          value: v,
          itemStyle: { color: v >= 0 ? '#ef4444' : '#10b981' },
        })),
        xAxisIndex: 1,
        yAxisIndex: 1,
        barWidth: '40%',
      },
    ]
  } else if (indicator.value === 'kdj') {
    subLegend = ['K', 'D', 'J']
    const kData = data.map(item => item.kdj_k)
    const dData = data.map(item => item.kdj_d)
    const jData = data.map(item => item.kdj_j)
    subSeries = [
      {
        name: 'K',
        type: 'line',
        data: kData,
        xAxisIndex: 1,
        yAxisIndex: 1,
        showSymbol: false,
        lineStyle: { width: 1, color: '#f59e0b' },
      },
      {
        name: 'D',
        type: 'line',
        data: dData,
        xAxisIndex: 1,
        yAxisIndex: 1,
        showSymbol: false,
        lineStyle: { width: 1, color: '#3b82f6' },
      },
      {
        name: 'J',
        type: 'line',
        data: jData,
        xAxisIndex: 1,
        yAxisIndex: 1,
        showSymbol: false,
        lineStyle: { width: 1, color: '#ec4899' },
      },
    ]
  } else if (indicator.value === 'rsi') {
    subLegend = ['RSI6', 'RSI12', 'RSI24']
    const rsi6Data = data.map(item => item.rsi6)
    const rsi12Data = data.map(item => item.rsi12)
    const rsi24Data = data.map(item => item.rsi24)
    subSeries = [
      {
        name: 'RSI6',
        type: 'line',
        data: rsi6Data,
        xAxisIndex: 1,
        yAxisIndex: 1,
        showSymbol: false,
        lineStyle: { width: 1, color: '#f59e0b' },
      },
      {
        name: 'RSI12',
        type: 'line',
        data: rsi12Data,
        xAxisIndex: 1,
        yAxisIndex: 1,
        showSymbol: false,
        lineStyle: { width: 1, color: '#3b82f6' },
      },
      {
        name: 'RSI24',
        type: 'line',
        data: rsi24Data,
        xAxisIndex: 1,
        yAxisIndex: 1,
        showSymbol: false,
        lineStyle: { width: 1, color: '#10b981' },
      },
    ]
  }

  // 副图 tooltip 格式化
  function buildSubTooltip(params) {
    let html = ''
    for (const p of params) {
      if (p.data === undefined || p.data === null) continue
      const val = typeof p.data === 'object' ? p.data.value : p.data
      if (val === null || val === undefined || isNaN(val)) continue
      html += `<div style="font-size:12px;"><span style="color:${p.color};">${p.seriesName}:</span> <b>${Number(val).toFixed(2)}</b></div>`
    }
    return html
  }

  return {
    animation: false,
    backgroundColor: '#fff',
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#1f2937',
        fontSize: 12,
      },
      formatter: function(params) {
        const date = params[0]?.axisValue || ''
        let html = `<div style="font-weight:600;margin-bottom:6px;">${date}</div>`

        // K线数据
        const kline = params.find(p => p.seriesName === 'K线')
        if (kline && kline.data) {
          const [open, close, low, high] = kline.data
          const change = close - open
          const changePct = open ? (change / open * 100).toFixed(2) : 0
          const color = change >= 0 ? '#ef4444' : '#10b981'
          html += `
            <div style="display:grid;grid-template-columns:auto auto;gap:4px 16px;font-size:12px;">
              <span style="color:#6b7280;">开盘</span><span style="text-align:right;font-weight:600;">${open.toFixed(2)}</span>
              <span style="color:#6b7280;">收盘</span><span style="text-align:right;font-weight:600;color:${color};">${close.toFixed(2)}</span>
              <span style="color:#6b7280;">最高</span><span style="text-align:right;font-weight:600;color:#ef4444;">${high.toFixed(2)}</span>
              <span style="color:#6b7280;">最低</span><span style="text-align:right;font-weight:600;color:#10b981;">${low.toFixed(2)}</span>
              <span style="color:#6b7280;">涨跌</span><span style="text-align:right;font-weight:600;color:${color};">${change >= 0 ? '+' : ''}${change.toFixed(2)} (${change >= 0 ? '+' : ''}${changePct}%)</span>
            </div>
          `
        }

        // 均线
        const ma5 = params.find(p => p.seriesName === 'MA5')
        const ma10 = params.find(p => p.seriesName === 'MA10')
        const ma20 = params.find(p => p.seriesName === 'MA20')
        if (ma5?.data !== undefined || ma10?.data !== undefined || ma20?.data !== undefined) {
          html += '<div style="margin-top:6px;border-top:1px solid #e5e7eb;padding-top:6px;">'
          if (ma5?.data !== undefined && ma5.data !== null) html += `<span style="color:#f59e0b;margin-right:12px;">MA5: ${Number(ma5.data).toFixed(2)}</span>`
          if (ma10?.data !== undefined && ma10.data !== null) html += `<span style="color:#8b5cf6;margin-right:12px;">MA10: ${Number(ma10.data).toFixed(2)}</span>`
          if (ma20?.data !== undefined && ma20.data !== null) html += `<span style="color:#3b82f6;">MA20: ${Number(ma20.data).toFixed(2)}</span>`
          html += '</div>'
        }

        // 副图指标
        const subParams = params.filter(p => subLegend.includes(p.seriesName))
        if (subParams.length > 0) {
          const subHtml = buildSubTooltip(subParams)
          if (subHtml) {
            html += `<div style="margin-top:6px;border-top:1px solid #e5e7eb;padding-top:6px;">${subHtml}</div>`
          }
        }

        return html
      },
    },
    legend: {
      data: ['K线', 'MA5', 'MA10', 'MA20', ...subLegend],
      top: 0,
      left: 'center',
      textStyle: { fontSize: 12 },
    },
    grid: [
      {
        left: '60px',
        right: '20px',
        top: '40px',
        height: '55%',
      },
      {
        left: '60px',
        right: '20px',
        top: '72%',
        height: '18%',
      },
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        axisLine: { lineStyle: { color: '#e5e7eb' } },
        axisLabel: { show: false },
        axisTick: { show: false },
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 1,
        axisLine: { lineStyle: { color: '#e5e7eb' } },
        axisLabel: {
          color: '#6b7280',
          fontSize: 11,
        },
        axisTick: { show: false },
      },
    ],
    yAxis: [
      {
        type: 'value',
        gridIndex: 0,
        scale: true,
        splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
        axisLabel: {
          color: '#6b7280',
          fontSize: 11,
          formatter: '{value}',
        },
      },
      {
        type: 'value',
        gridIndex: 1,
        scale: true,
        splitLine: { show: false },
        axisLabel: {
          color: '#6b7280',
          fontSize: 11,
          formatter: function(val) {
            if (indicator.value === 'volume') {
              if (val >= 10000) return (val / 10000).toFixed(0) + '万'
              return val
            }
            return val.toFixed(1)
          },
        },
      },
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 60,
        end: 100,
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        start: 60,
        end: 100,
        bottom: 0,
        height: 20,
        borderColor: 'transparent',
        backgroundColor: '#f3f4f6',
        fillerColor: 'rgba(59, 130, 246, 0.2)',
        handleStyle: { color: '#3b82f6' },
        textStyle: { color: '#6b7280', fontSize: 10 },
      },
    ],
    series: [
      // K线
      {
        name: 'K线',
        type: 'candlestick',
        data: klineData,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: '#ef4444',
          color0: '#10b981',
          borderColor: '#ef4444',
          borderColor0: '#10b981',
        },
      },
      // MA5
      {
        name: 'MA5',
        type: 'line',
        data: ma5Data,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: false,
        showSymbol: false,
        lineStyle: { width: 1, color: '#f59e0b' },
      },
      // MA10
      {
        name: 'MA10',
        type: 'line',
        data: ma10Data,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: false,
        showSymbol: false,
        lineStyle: { width: 1, color: '#8b5cf6' },
      },
      // MA20
      {
        name: 'MA20',
        type: 'line',
        data: ma20Data,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: false,
        showSymbol: false,
        lineStyle: { width: 1, color: '#3b82f6' },
      },
      // 副图指标
      ...subSeries,
    ],
  }
})

const emit = defineEmits(['period-change'])

function handlePeriodChange(val) {
  emit('period-change', val)
}

function handleIndicatorChange() {
  // 指标切换直接重新计算（computed 自动响应）
}
</script>

<style scoped>
.kline-card {
  width: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
  color: #1f2937;
}

.chart-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.indicator-select {
  width: 110px;
}

.chart-container {
  width: 100%;
  height: 480px;
}

.kline-chart {
  width: 100%;
  height: 100%;
}

.empty-state {
  padding: 60px 0;
}
</style>
