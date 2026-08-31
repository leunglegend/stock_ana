const RSI_OVERHEATED = 75
const RSI_OVERSOLD = 25
const DRAWDOWN_ATTENTION = -0.1
const COST_GAIN = 0.15
const COST_LOSS = -0.1

export function analyzeStockSignals(klineData, context = {}) {
  const rows = (klineData?.kline || []).filter((row) => isFiniteNumber(row?.close))
  if (!rows.length) return emptyAnalysis()

  const latest = rows.at(-1)
  const previous = rows.at(-2)
  const priorWindow = rows.slice(-21, -1)
  const signals = [
    trendSignal(latest),
    momentumSignal(previous, latest),
    rsiSignal(latest),
    positionSignal(latest, priorWindow),
    costSignal(context.costReturn),
  ].filter(Boolean)

  return {
    status: resolveStatus(signals),
    signals,
    note: signals.length ? '' : '暂无显著规则信号',
    asOf: latest.date || null,
  }
}

export function summarizeSignalResults(results = []) {
  return results.reduce((summary, result) => {
    if (result.status === 'error') summary.error += 1
    else if (result.analysis?.status in summary) summary[result.analysis.status] += 1
    return summary
  }, { total: results.length, strong: 0, neutral: 0, attention: 0, error: 0 })
}

function trendSignal(latest) {
  if (!isFiniteNumber(latest.ma20)) return null
  if (latest.close < latest.ma20) {
    return signal('trend-below-ma20', 'attention', '收盘价低于 MA20', `收盘 ${format(latest.close)} / MA20 ${format(latest.ma20)}`)
  }
  if (latest.close > latest.ma20 && isFiniteNumber(latest.ma5) && latest.ma5 > latest.ma20) {
    return signal('trend-above-ma20', 'positive', '价格位于 MA20 上方', `MA5 ${format(latest.ma5)} / MA20 ${format(latest.ma20)}`)
  }
  return null
}

function momentumSignal(previous, latest) {
  if (!previous || !hasFiniteValues(previous, 'dif', 'dea') || !hasFiniteValues(latest, 'dif', 'dea')) return null
  if (previous.dif <= previous.dea && latest.dif > latest.dea) {
    return signal('macd-golden-cross', 'positive', 'MACD 上穿', `DIF ${format(latest.dif)} / DEA ${format(latest.dea)}`)
  }
  if (previous.dif >= previous.dea && latest.dif < latest.dea) {
    return signal('macd-death-cross', 'attention', 'MACD 下穿', `DIF ${format(latest.dif)} / DEA ${format(latest.dea)}`)
  }
  return null
}

function rsiSignal(latest) {
  if (!isFiniteNumber(latest.rsi6)) return null
  if (latest.rsi6 >= RSI_OVERHEATED) return signal('rsi-overheated', 'attention', 'RSI6 进入过热区间', `RSI6 ${format(latest.rsi6)}`)
  if (latest.rsi6 <= RSI_OVERSOLD) return signal('rsi-oversold', 'info', 'RSI6 进入超卖区间', `RSI6 ${format(latest.rsi6)}`)
  return null
}

function positionSignal(latest, priorWindow) {
  const highs = priorWindow.map((row) => row.high).filter(isFiniteNumber)
  if (!highs.length) return null
  const priorHigh = Math.max(...highs)
  const distance = latest.close / priorHigh - 1
  if (latest.close >= priorHigh) return signal('breakout-20d', 'positive', '突破近 20 日高位', `高于前高 ${formatPercent(distance)}`)
  if (distance <= DRAWDOWN_ATTENTION) return signal('drawdown-20d', 'attention', '距近 20 日高位回撤较大', `距前高 ${formatPercent(distance)}`)
  return null
}

function costSignal(costReturn) {
  if (!isFiniteNumber(costReturn)) return null
  if (costReturn <= COST_LOSS) return signal('cost-loss', 'attention', '低于记录成本超过 10%', `成本收益 ${formatPercent(costReturn)}`)
  if (costReturn >= COST_GAIN) return signal('cost-gain', 'positive', '高于记录成本超过 15%', `成本收益 ${formatPercent(costReturn)}`)
  return null
}

function resolveStatus(signals) {
  if (signals.some(({ kind }) => kind === 'attention')) return 'attention'
  return signals.filter(({ kind }) => kind === 'positive').length >= 2 ? 'strong' : 'neutral'
}

function signal(code, kind, label, detail) {
  return { code, kind, label, detail }
}

function emptyAnalysis() {
  return { status: 'neutral', signals: [], note: '有效 K 线数据不足', asOf: null }
}

function hasFiniteValues(target, ...keys) {
  return keys.every((key) => isFiniteNumber(target[key]))
}

function isFiniteNumber(value) {
  return typeof value === 'number' && Number.isFinite(value)
}

function format(value) {
  return Number(value).toFixed(2)
}

function formatPercent(value) {
  return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(1)}%`
}
