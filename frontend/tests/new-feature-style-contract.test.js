import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const appSource = await readFile(new URL('../src/App.vue', import.meta.url), 'utf8')
const signalSource = await readFile(new URL('../src/components/watchlist/WatchlistSignalCenter.vue', import.meta.url), 'utf8')
const commandBarSource = await readFile(new URL('../src/components/app/CommandBar.vue', import.meta.url), 'utf8')
const panelSource = await readFile(new URL('../src/components/base/SectionPanel.vue', import.meta.url), 'utf8')
const boardTableSource = await readFile(new URL('../src/components/board/BoardTable.vue', import.meta.url), 'utf8')
const tokenSource = await readFile(new URL('../src/styles/tokens.css', import.meta.url), 'utf8')
const elementPlusSource = await readFile(new URL('../src/styles/element-plus.css', import.meta.url), 'utf8')
const mainStyleSource = await readFile(new URL('../src/style.css', import.meta.url), 'utf8')
const metricSource = await readFile(new URL('../src/components/base/MetricCell.vue', import.meta.url), 'utf8')
const priceSource = await readFile(new URL('../src/components/base/PriceDisplay.vue', import.meta.url), 'utf8')
const percentageSource = await readFile(new URL('../src/components/base/PercentageDisplay.vue', import.meta.url), 'utf8')

test('认证状态使用工作台语义 Token 与紧凑圆角', () => {
  assert.doesNotMatch(appSource, /border-radius:\s*20px/)
  assert.doesNotMatch(appSource, /color:\s*#[0-9a-f]{3,8}/i)
  assert.match(appSource, /border-radius:\s*var\(--radius-sm\)/)
  assert.match(appSource, /background:\s*var\(--surface-primary\)/)
})

test('信号结果保持待处理摘要并限制前三条', () => {
  assert.match(signalSource, /visibleResults\s*=\s*computed\([\s\S]*slice\(0,\s*3\)/)
  assert.match(signalSource, /class="signal-center__todos"/)
  assert.match(signalSource, /class="signal-center__todo"/)
  assert.match(signalSource, /\.signal-center__todo\s*\{[\s\S]*min-height:\s*66px/)
  assert.match(signalSource, /@media\s*\(max-width:\s*767px\)[\s\S]*\.signal-center__todo\s*\{[\s\S]*min-height:\s*68px/)
})

test('桌面工作台使用机构研究盘密度', () => {
  assert.match(commandBarSource, /min-height:\s*var\(--command-bar-height\)/)
  assert.match(commandBarSource, /padding:\s*var\(--spacing-1\)\s+var\(--spacing-3\)/)
  assert.match(commandBarSource, /@media\s*\(max-width:\s*767px\)[\s\S]*\.command-bar__search\s*\{[\s\S]*min-height:\s*44px/)
  assert.match(panelSource, /\.section-panel__body\s*\{[\s\S]*padding:\s*var\(--panel-padding-block\)\s+var\(--panel-padding-inline\)/)
  assert.match(boardTableSource, /\.board-table__row\s*\{[\s\S]*min-height:\s*var\(--data-row-height\)/)
})

test('共享 Token 定义高密度投资工作台尺寸与低装饰表面', () => {
  assert.match(tokenSource, /--radius-pill:\s*999px/)
  assert.match(tokenSource, /--control-height:\s*32px/)
  assert.match(tokenSource, /--table-head-height:\s*32px/)
  assert.match(tokenSource, /--data-row-height:\s*40px/)
  assert.match(tokenSource, /--mobile-control-height:\s*44px/)
  assert.match(tokenSource, /--shadow-card:\s*none/)
})

function extractHex(block, token) {
  return block.match(new RegExp(`${token}:\\s*(#[0-9a-f]{6});`, 'i'))?.[1].toLowerCase()
}

function relativeLuminance(hex) {
  const channels = [1, 3, 5].map((index) => parseInt(hex.slice(index, index + 2), 16) / 255)
  const linear = channels.map((channel) => (
    channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4
  ))
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
}

test('三套主题使用平衡增强边框层级', () => {
  const expected = {
    ocean: { subtle: '#d2dce4', default: '#aebdca', strong: '#7f95a8' },
    jade: { subtle: '#cadbd3', default: '#a9bfb4', strong: '#789486' },
    charcoal: { subtle: '#d8d1c7', default: '#b8aea1', strong: '#918477' },
  }

  for (const [theme, colors] of Object.entries(expected)) {
    const block = theme === 'ocean'
      ? tokenSource.match(/:root\s*\{[\s\S]*?\n\}/)?.[0] || ''
      : tokenSource.match(new RegExp(`:root\\[data-theme=['"]${theme}['"]\\]\\s*\\{[\\s\\S]*?\\n\\}`))?.[0] || ''
    const subtle = extractHex(block, '--border-subtle')
    const normal = extractHex(block, '--border-default')
    const strong = extractHex(block, '--border-strong')
    assert.deepEqual({ subtle, default: normal, strong }, colors, `${theme} 边框 Token 不符合 B 方案`)
    assert.ok(relativeLuminance(normal) < relativeLuminance(subtle), `${theme} 默认边框应比内部线更深`)
    assert.ok(relativeLuminance(strong) < relativeLuminance(normal), `${theme} 强边框应比默认边框更深`)
  }
})

test('共享重点数字采用科技终端层级', () => {
  assert.match(metricSource, /font-family:\s*var\(--font-family-mono\)/)
  assert.match(metricSource, /font-size:\s*var\(--font-size-3xl\)/)
  assert.match(metricSource, /font-weight:\s*700/)
  assert.match(metricSource, /color:\s*var\(--text-positive\)/)
  assert.match(metricSource, /color:\s*var\(--text-negative\)/)
  assert.match(priceSource, /font-family:\s*var\(--font-family-mono\)/)
  assert.match(priceSource, /\.price-display--md \.price-display__price[\s\S]*font-size:\s*var\(--font-size-2xl\)/)
  assert.match(percentageSource, /\.percentage-display--md[\s\S]*font-size:\s*var\(--font-size-2xl\)/)
  assert.doesNotMatch(metricSource + priceSource + percentageSource, /color:\s*#[0-9a-f]{3,8}/i)
})

test('Element Plus 使用单一全局适配层', () => {
  assert.match(mainStyleSource, /@import\s+['"]\.\/styles\/element-plus\.css['"]/)
  assert.match(elementPlusSource, /\.el-table\s+\.el-table__cell/)
  assert.match(elementPlusSource, /height:\s*var\(--data-row-height\)/)
  assert.match(elementPlusSource, /\.el-input__wrapper/)
  assert.match(elementPlusSource, /min-height:\s*var\(--control-height\)/)
})

test('基础面板提供标准、无内边距和浮层三种表面', () => {
  assert.match(panelSource, /variant/)
  assert.match(panelSource, /section-panel--flush/)
  assert.match(panelSource, /section-panel--overlay/)
  assert.match(panelSource, /box-shadow:\s*none/)
})

test('基础面板使用清晰默认边框并保留浮层阴影例外', () => {
  assert.match(panelSource, /border:\s*1px solid var\(--border-default\)/)
  assert.match(panelSource, /section-panel--overlay[\s\S]*box-shadow:\s*var\(--shadow-overlay\)/)
})
