import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

async function readSource(relativePath) {
  try {
    return await readFile(new URL(relativePath, import.meta.url), 'utf8')
  } catch (error) {
    if (error?.code === 'ENOENT') return null
    throw error
  }
}

function requireSource(source, label, relativePath) {
  assert.notEqual(source, null, `${label} 缺失：${relativePath}`)
  return source
}

const [
  routerSource,
  layoutSource,
  mobileNavSource,
  radarViewSource,
  toolbarSource,
  rankingSource,
  snapshotSource,
  stockTableSource,
  elementPlusPluginSource,
  elementPlusStyleSource,
] = await Promise.all([
  readSource('../src/router/index.js'),
  readSource('../src/components/Layout.vue'),
  readSource('../src/components/app/MobileNav.vue'),
  readSource('../src/views/OpportunityRadar.vue'),
  readSource('../src/components/radar/RadarToolbar.vue'),
  readSource('../src/components/radar/BoardRanking.vue'),
  readSource('../src/components/radar/BoardSnapshot.vue'),
  readSource('../src/components/radar/BoardStockTable.vue'),
  readSource('../src/plugins/elementPlus.js'),
  readSource('../src/styles/element-plus.css'),
])

test('机会雷达注册为无需登录的懒加载一级路由', () => {
  const router = requireSource(routerSource, '路由配置', '../src/router/index.js')

  assert.match(router, /path:\s*['"]\/radar['"]/)
  assert.match(router, /component:\s*\(\)\s*=>\s*import\(['"]\.\.\/views\/OpportunityRadar\.vue['"]\)/)

  const radarRoute = router.match(/(?:^|\n)\s*\{\s*\n\s*path:\s*['"]\/radar['"][\s\S]*?\n\s*\},?/m)?.[0] || ''
  assert.notEqual(radarRoute, '', '未找到 /radar 路由定义')
  assert.match(radarRoute, /title:\s*['"](?:雷达|机会雷达)['"]/)
  assert.doesNotMatch(radarRoute, /requiresAuth:\s*true/)
})

test('Layout 导航提供雷达一级入口', () => {
  const layout = requireSource(layoutSource, 'Layout', '../src/components/Layout.vue')

  assert.match(
    layout,
    /path:\s*['"]\/radar['"][\s\S]*?title:\s*['"]雷达['"][\s\S]*?icon:\s*['"][A-Za-z]+['"]/,
  )
})

test('MobileNav 列数跟随菜单数量变化而不是写死四列', () => {
  const mobileNav = requireSource(mobileNavSource, 'MobileNav', '../src/components/app/MobileNav.vue')

  assert.match(mobileNav, /items\.length/)
  assert.match(mobileNav, /--mobile-nav-columns|gridTemplateColumns/)
  assert.doesNotMatch(mobileNav, /grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*1fr\)\)/)
})

test('雷达按规格拆分为页面加四个专用子组件', () => {
  requireSource(radarViewSource, '机会雷达页面', '../src/views/OpportunityRadar.vue')
  requireSource(toolbarSource, '雷达工具栏', '../src/components/radar/RadarToolbar.vue')
  requireSource(rankingSource, '板块榜组件', '../src/components/radar/BoardRanking.vue')
  requireSource(snapshotSource, '板块摘要组件', '../src/components/radar/BoardSnapshot.vue')
  requireSource(stockTableSource, '成分股表格组件', '../src/components/radar/BoardStockTable.vue')
})

test('机会雷达页面组合专用组件并把请求逻辑留给组合式函数', () => {
  const view = requireSource(radarViewSource, '机会雷达页面', '../src/views/OpportunityRadar.vue')

  assert.match(view, /class="[^"]*radar-page[^"]*workbench-page/)
  assert.match(view, /class="[^"]*workbench-page__header/)
  assert.match(view, /data-page-title[^>]*>机会雷达</)
  assert.match(view, /import\s+RadarToolbar\s+from\s+['"][^'"]*RadarToolbar\.vue['"]/)
  assert.match(view, /import\s+BoardRanking\s+from\s+['"][^'"]*BoardRanking\.vue['"]/)
  assert.match(view, /import\s+BoardSnapshot\s+from\s+['"][^'"]*BoardSnapshot\.vue['"]/)
  assert.match(view, /import\s+BoardStockTable\s+from\s+['"][^'"]*BoardStockTable\.vue['"]/)
  assert.match(view, /import\s+\{\s*useOpportunityRadar\s*\}\s+from\s+['"][^'"]*useOpportunityRadar(?:\.js)?['"]/)
  assert.match(view, /<RadarToolbar/)
  assert.match(view, /<BoardRanking/)
  assert.match(view, /<BoardSnapshot/)
  assert.match(view, /<BoardStockTable/)
  assert.doesNotMatch(view, /from\s+['"][^'"]*api\/board[^'"]*['"]/)
  assert.doesNotMatch(view, /\bgetBoardIndustry\b|\bgetBoardConcept\b|\bgetBoardStocks\b/)
})

test('雷达工具栏和板块榜提供可访问控件契约', () => {
  const toolbar = requireSource(toolbarSource, '雷达工具栏', '../src/components/radar/RadarToolbar.vue')
  const ranking = requireSource(rankingSource, '板块榜组件', '../src/components/radar/BoardRanking.vue')

  assert.match(toolbar, /行业板块/)
  assert.match(toolbar, /概念板块/)
  assert.match(toolbar, /仅看上涨/)
  assert.match(toolbar, /aria-label="按板块名称筛选"|<label[^>]*>[^<]*按板块名称筛选/)
  assert.match(toolbar, /aria-label="刷新机会雷达"|>刷新</)
  assert.match(ranking, /<button[\s\S]*aria-pressed=/)
  assert.match(ranking, /\$emit\('retry'\)|emit\('retry'\)/)
})

test('成分股组件暴露详情和自选操作而不是自己接管登录流程', () => {
  const stockTable = requireSource(stockTableSource, '成分股表格组件', '../src/components/radar/BoardStockTable.vue')

  assert.match(stockTable, /查看[^<]*详情|>详情</)
  assert.match(stockTable, /加入自选/)
  assert.match(stockTable, /\$emit\('open-stock'|emit\('open-stock'/)
  assert.match(stockTable, /\$emit\('add-watchlist'|emit\('add-watchlist'/)
  assert.doesNotMatch(stockTable, /useUserStore|requestLogin|useWatchlistStore|addStockToGroup|GroupPicker/)
})

test('雷达指标格式化保留真实零值并仅隐藏缺失值', () => {
  const ranking = requireSource(rankingSource, '板块榜组件', '../src/components/radar/BoardRanking.vue')
  const snapshot = requireSource(snapshotSource, '板块摘要组件', '../src/components/radar/BoardSnapshot.vue')
  const stockTable = requireSource(stockTableSource, '成分股表格组件', '../src/components/radar/BoardStockTable.vue')

  assert.doesNotMatch(ranking, /safeNumber\(value\)\s*\?\s*format/)
  assert.doesNotMatch(snapshot, /safeNumber\([^)]*\)\s*\?\s*format/)
  assert.doesNotMatch(stockTable, /return number\s*\?\s*format/)
  assert.match(ranking, /number == null \? '--' : format/)
  assert.match(snapshot, /number == null \? '--' : format/)
  assert.match(stockTable, /number == null \? '--' : format/)
})

test('机会雷达页面复用 GroupPicker 与现有登录、自选调用链', () => {
  const view = requireSource(radarViewSource, '机会雷达页面', '../src/views/OpportunityRadar.vue')

  assert.match(view, /import\s+GroupPicker\s+from\s+['"][^'"]*GroupPicker\.vue['"]/)
  assert.match(view, /useUserStore/)
  assert.match(view, /useWatchlistStore/)
  assert.match(view, /useRoute/)
  assert.match(view, /<GroupPicker/)
  assert.match(view, /:groups="watchlistStore\.groupNames"|:groups="watchlistGroups"/)
  assert.match(view, /watchlistStore\.groupNames/)
  assert.match(view, /userStore\.requestLogin\(route\.fullPath\)/)
  assert.match(
    view,
    /selectedGroupId\.value\s*=\s*(?:watchlistStore\.activeGroup\s*\|\|\s*watchlistStore\.groupNames\[0\]\?\.id\s*\|\|\s*''|resolveDefaultGroupId\(\))/,
  )
  assert.match(
    view,
    /function\s+resolveDefaultGroupId\(\)\s*\{[\s\S]*watchlistStore\.activeGroup[\s\S]*(watchlistGroups\.value|watchlistStore\.groupNames)\[0\]\?\.id[\s\S]*\}/,
  )
  assert.match(view, /watchlistStore\.addStockToGroup\(groupId,\s*pendingStock\.value\)/)
  assert.match(view, /import\s*\{[\s\S]*readPendingRadarStock[\s\S]*writePendingRadarStock[\s\S]*clearPendingRadarStock[\s\S]*\}\s*from\s*['"][^'"]*opportunityRadar['"]/)
  assert.match(view, /const pendingStock = ref\(readPendingRadarStock\(\)\)/)
  assert.match(view, /function\s+clearPendingStock\(\)\s*\{[\s\S]*clearPendingRadarStock\(\)/)
  assert.match(view, /function\s+requestAdd\(stock\)\s*\{[\s\S]*writePendingRadarStock\(undefined,\s*nextStock\)/)
  assert.match(view, /watch\([\s\S]*userStore\.isLoggedIn[\s\S]*watchlistStore\.loading[\s\S]*watchlistStore\.cloudMode[\s\S]*watchlistStore\.cloudError[\s\S]*openPendingPicker/)
  assert.match(
    view,
    /function\s+openPendingPicker\(\)\s*\{[\s\S]*if\s*\(!userStore\.isLoggedIn\s*\|\|\s*watchlistStore\.loading\s*\|\|\s*!watchlistStore\.cloudMode\s*\|\|\s*watchlistStore\.cloudError\)\s*return[\s\S]*selectedGroupId\.value\s*=\s*resolveDefaultGroupId\(\)/,
  )
  assert.match(view, /watch\([\s\S]*openPendingPicker\(\)[\s\S]*immediate:\s*true/)
})

test('平板和移动端都使用紧凑成分股列表', () => {
  const view = requireSource(radarViewSource, '机会雷达页面', '../src/views/OpportunityRadar.vue')
  const stockTable = requireSource(stockTableSource, '成分股组件', '../src/components/radar/BoardStockTable.vue')

  assert.match(view, /const \{[^}]*isDesktop[^}]*\} = useResponsive\(\)/)
  assert.match(view, /const isCompact = computed\(\(\) => !isDesktop\.value\)/)
  assert.match(view, /:mobile="isCompact"/)
  assert.match(stockTable, /\.board-stock-table__mobile-identity\{[^}]*min-height:44px/)
})

test('紧凑布局优先展示候选详情，板块榜随后呈现', () => {
  const view = requireSource(radarViewSource, '机会雷达页面', '../src/views/OpportunityRadar.vue')

  assert.match(view, /<div class="radar-page__index"[\s\S]*<div ref="stocksPanelRef" class="radar-page__detail"/)
  assert.match(view, /@media \(max-width:\s*1023px\)\s*\{[\s\S]*\.radar-page__detail\s*\{[\s\S]*grid-row:\s*1/)
  assert.match(view, /@media \(max-width:\s*1023px\)\s*\{[\s\S]*\.radar-page__index\s*\{[\s\S]*border-top:\s*1px solid var\(--border-default\)/)
})

test('机会雷达接入高密度研究台而不是独立卡片主题', () => {
  const view = requireSource(radarViewSource, '机会雷达页面', '../src/views/OpportunityRadar.vue')
  const toolbar = requireSource(toolbarSource, '雷达工具栏', '../src/components/radar/RadarToolbar.vue')
  const ranking = requireSource(rankingSource, '板块榜组件', '../src/components/radar/BoardRanking.vue')
  const snapshot = requireSource(snapshotSource, '板块摘要组件', '../src/components/radar/BoardSnapshot.vue')
  const stockTable = requireSource(stockTableSource, '成分股表格组件', '../src/components/radar/BoardStockTable.vue')

  for (const source of [view, ranking, snapshot, stockTable]) {
    assert.doesNotMatch(source, /__eyebrow|Opportunity Radar/)
  }
  assert.doesNotMatch(toolbar, /border-radius:\s*var\(--radius-panel\)/)
  assert.doesNotMatch(snapshot, /\.board-snapshot__hero\s*\{[\s\S]*border-radius:/)
  assert.match(stockTable, /\.board-stock-table__mobile-row\s*\{[\s\S]*border-bottom:/)
  assert.doesNotMatch(stockTable, /\.board-stock-table__mobile-row\s*\{[\s\S]*border-radius:/)
})

test('机会雷达使用的 Element Plus 控件已全局注册并统一适配', () => {
  const plugin = requireSource(elementPlusPluginSource, 'Element Plus 注册', '../src/plugins/elementPlus.js')
  const styles = requireSource(elementPlusStyleSource, 'Element Plus 样式', '../src/styles/element-plus.css')

  assert.match(plugin, /ElSegmented/)
  assert.match(plugin, /ElSwitch/)
  assert.match(plugin, /segmented\/style\/css/)
  assert.match(plugin, /switch\/style\/css/)
  assert.match(styles, /\.el-segmented/)
  assert.match(styles, /\.el-switch/)
})
