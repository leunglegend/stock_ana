<template>
  <section class="kline-card" v-loading="loading">
    <header class="kline-card__header">
      <h2 class="kline-card__title">K 线与指标</h2>
        <div class="kline-card__controls">
          <el-radio-group v-model="period" size="small" @change="emit('period-change', $event)">
            <el-radio-button value="daily">日K</el-radio-button>
            <el-radio-button value="weekly">周K</el-radio-button>
            <el-radio-button value="monthly">月K</el-radio-button>
          </el-radio-group>
          <el-select v-model="indicator" size="small" class="kline-card__select">
            <el-option label="成交量" value="volume" />
            <el-option label="MACD" value="macd" />
            <el-option label="KDJ" value="kdj" />
            <el-option label="RSI" value="rsi" />
          </el-select>
        </div>
    </header>

    <div v-if="hasData" class="kline-card__chart">
      <v-chart class="kline-card__view" :option="chartOption" autoresize />
    </div>
    <div v-else class="kline-card__empty">
      <el-empty description="暂无 K 线数据" :image-size="80" />
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, CandlestickChart, LineChart } from 'echarts/charts'
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
} from 'echarts/components'
import { THEME_CHANGE_EVENT } from '@/theme'

use([
  CanvasRenderer,
  BarChart,
  CandlestickChart,
  LineChart,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
])

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

const emit = defineEmits(['period-change'])
const period = ref('daily')
const indicator = ref('volume')
const themeVersion = ref(0)

const hasData = computed(() => Array.isArray(props.klineData?.kline) && props.klineData.kline.length > 0)

function token(name, fallback) {
  if (typeof window === 'undefined') return fallback
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

function readTheme() {
  return {
    surface: token('--surface-canvas', '#ffffff'),
    text: token('--text-primary', '#1f2735'),
    textMuted: token('--text-secondary', '#627085'),
    border: token('--border-default', '#d3dae4'),
    grid: token('--chart-grid', '#dde4ee'),
    up: token('--chart-up', '#d84a43'),
    down: token('--chart-down', '#1e8b57'),
    ma5: token('--chart-ma5', '#e28743'),
    ma10: token('--chart-ma10', '#5b8def'),
    ma20: token('--chart-ma20', '#6a4fb5'),
    dif: token('--chart-dif', '#d56b2d'),
    dea: token('--chart-dea', '#2d5fb1'),
    k: token('--chart-k', '#cf513e'),
    d: token('--chart-d', '#3c78d8'),
    j: token('--chart-j', '#7e5fae'),
    rsi6: token('--chart-rsi6', '#b95f2a'),
    rsi12: token('--chart-rsi12', '#3f78bb'),
    rsi24: token('--chart-rsi24', '#5b6f87'),
  }
}

function metricSeries(type, rows, theme) {
  const map = {
    volume: [{
      name: '成交量',
      type: 'bar',
      data: rows.map((row) => ({
        value: row.volume,
        itemStyle: { color: row.close >= row.open ? theme.up : theme.down },
      })),
      xAxisIndex: 1,
      yAxisIndex: 1,
      barWidth: '58%',
    }],
    macd: [
      lineSeries('DIF', rows.map((row) => row.dif), theme.dif),
      lineSeries('DEA', rows.map((row) => row.dea), theme.dea),
      {
        name: 'MACD',
        type: 'bar',
        data: rows.map((row) => ({
          value: row.macd,
          itemStyle: { color: Number(row.macd) >= 0 ? theme.up : theme.down },
        })),
        xAxisIndex: 1,
        yAxisIndex: 1,
        barWidth: '40%',
      },
    ],
    kdj: [
      lineSeries('K', rows.map((row) => row.kdj_k), theme.k),
      lineSeries('D', rows.map((row) => row.kdj_d), theme.d),
      lineSeries('J', rows.map((row) => row.kdj_j), theme.j),
    ],
    rsi: [
      lineSeries('RSI6', rows.map((row) => row.rsi6), theme.rsi6),
      lineSeries('RSI12', rows.map((row) => row.rsi12), theme.rsi12),
      lineSeries('RSI24', rows.map((row) => row.rsi24), theme.rsi24),
    ],
  }
  return map[type] || map.volume
}

function lineSeries(name, data, color) {
  return {
    name,
    type: 'line',
    data,
    xAxisIndex: 1,
    yAxisIndex: 1,
    showSymbol: false,
    lineStyle: { width: 1, color },
  }
}

function refreshTheme() {
  themeVersion.value += 1
}

onMounted(() => window.addEventListener(THEME_CHANGE_EVENT, refreshTheme))
onUnmounted(() => window.removeEventListener(THEME_CHANGE_EVENT, refreshTheme))

const chartOption = computed(() => {
  void themeVersion.value
  if (!hasData.value) return {}
  const theme = readTheme()
  const rows = props.klineData.kline
  const dates = rows.map((row) => row.date)
  const candles = rows.map((row) => [row.open, row.close, row.low, row.high])
  const metricRows = metricSeries(indicator.value, rows, theme)

  return {
    animation: false,
    backgroundColor: theme.surface,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: theme.surface,
      borderColor: theme.border,
      textStyle: { color: theme.text, fontSize: 12 },
    },
    legend: {
      top: 0,
      left: 'center',
      textStyle: { color: theme.textMuted, fontSize: 12 },
      data: ['K线', 'MA5', 'MA10', 'MA20', ...metricRows.map((item) => item.name)],
    },
    grid: [
      { left: 56, right: 18, top: 36, height: '56%' },
      { left: 56, right: 18, top: '73%', height: '17%' },
    ],
    xAxis: [0, 1].map((gridIndex) => ({
      type: 'category',
      data: dates,
      gridIndex,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: theme.border } },
      axisLabel: gridIndex === 0 ? { show: false } : { color: theme.textMuted, fontSize: 11 },
    })),
    yAxis: [0, 1].map((gridIndex) => ({
      type: 'value',
      gridIndex,
      scale: true,
      splitLine: gridIndex === 0 ? { lineStyle: { color: theme.grid, type: 'dashed' } } : { show: false },
      axisLabel: {
        color: theme.textMuted,
        fontSize: 11,
        formatter: (value) => gridIndex === 1 && indicator.value === 'volume' && value >= 10000
          ? `${(value / 10000).toFixed(0)}万`
          : Number(value).toFixed(gridIndex === 0 ? 2 : 1),
      },
    })),
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 60, end: 100 },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        start: 60,
        end: 100,
        bottom: 0,
        height: 18,
        borderColor: 'transparent',
        backgroundColor: theme.grid,
        fillerColor: `${theme.dea}33`,
        handleStyle: { color: theme.dea },
        textStyle: { color: theme.textMuted, fontSize: 10 },
      },
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: candles,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: theme.up,
          color0: theme.down,
          borderColor: theme.up,
          borderColor0: theme.down,
        },
      },
      {
        name: 'MA5',
        type: 'line',
        data: rows.map((row) => row.ma5),
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: false,
        showSymbol: false,
        lineStyle: { width: 1, color: theme.ma5 },
      },
      {
        name: 'MA10',
        type: 'line',
        data: rows.map((row) => row.ma10),
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: false,
        showSymbol: false,
        lineStyle: { width: 1, color: theme.ma10 },
      },
      {
        name: 'MA20',
        type: 'line',
        data: rows.map((row) => row.ma20),
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: false,
        showSymbol: false,
        lineStyle: { width: 1, color: theme.ma20 },
      },
      ...metricRows,
    ],
  }
})
</script>

<style scoped>
.kline-card,.kline-card__chart,.kline-card__view{width:100%}
.kline-card{height:100%;padding:var(--spacing-3);background:var(--surface-primary)}
.kline-card__header{display:flex;align-items:end;justify-content:space-between;gap:var(--spacing-4);padding-bottom:var(--spacing-3);border-bottom:1px solid var(--border-subtle)}
.kline-card__title{margin:0;color:var(--text-primary);font-size:var(--font-size-lg)}
.kline-card__controls{display:flex;align-items:center;gap:var(--spacing-3)}
.kline-card__select{width:112px}
.kline-card__chart{height:560px}
.kline-card__view{height:100%}
.kline-card__empty{padding:var(--spacing-6) 0}
@media (max-width:767px){.kline-card__header,.kline-card__controls{display:grid}.kline-card__chart{height:420px}}
</style>
