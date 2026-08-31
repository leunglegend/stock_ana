import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

import {
  DEFAULT_THEME,
  THEME_CHANGE_EVENT,
  THEME_STORAGE_KEY,
  THEMES,
  applyTheme,
  initializeTheme,
  loadTheme,
  resolveTheme,
} from '../src/theme.js'

const tokensSource = await readFile(new URL('../src/styles/tokens.css', import.meta.url), 'utf8')
const mainSource = await readFile(new URL('../src/main.js', import.meta.url), 'utf8')
const commandBarSource = await readFile(new URL('../src/components/app/CommandBar.vue', import.meta.url), 'utf8')
const commandBarUtilitiesSource = await readFile(new URL('../src/components/app/CommandBarUtilities.vue', import.meta.url), 'utf8')
const elementPlusSource = await readFile(new URL('../src/plugins/elementPlus.js', import.meta.url), 'utf8')
const sidebarSource = await readFile(new URL('../src/components/app/DesktopSidebar.vue', import.meta.url), 'utf8')
const klineSource = await readFile(new URL('../src/components/KLineChart.vue', import.meta.url), 'utf8')

function createStorage(initialValue = null, { throwOnGet = false, throwOnSet = false } = {}) {
  let value = initialValue
  return {
    getItem(key) {
      assert.equal(key, THEME_STORAGE_KEY)
      if (throwOnGet) throw new Error('storage read failed')
      return value
    },
    setItem(key, nextValue) {
      assert.equal(key, THEME_STORAGE_KEY)
      if (throwOnSet) throw new Error('storage write failed')
      value = nextValue
    },
    value() {
      return value
    },
  }
}

function createEnvironment() {
  const events = []
  return {
    root: { dataset: {} },
    events,
    dispatch(event) {
      events.push(event)
    },
    createEvent(type, detail) {
      return { type, detail }
    },
  }
}

test('主题元数据包含唯一的三套已批准主题', () => {
  assert.equal(DEFAULT_THEME, 'ocean')
  assert.deepEqual(THEMES.map(({ key }) => key), ['ocean', 'jade', 'charcoal'])
  assert.equal(new Set(THEMES.map(({ key }) => key)).size, THEMES.length)
  THEMES.forEach((theme) => assert.equal(theme.colors.length, 3))
})

test('主题解析接受白名单值并将其他输入回退为默认主题', () => {
  assert.equal(resolveTheme('jade'), 'jade')
  assert.equal(resolveTheme('charcoal'), 'charcoal')
  assert.equal(resolveTheme('unknown'), DEFAULT_THEME)
  assert.equal(resolveTheme(null), DEFAULT_THEME)
})

test('读取主题时恢复合法值并处理非法值或存储异常', () => {
  assert.equal(loadTheme(createStorage('charcoal')), 'charcoal')
  assert.equal(loadTheme(createStorage('sepia')), DEFAULT_THEME)
  assert.equal(loadTheme(createStorage(null, { throwOnGet: true })), DEFAULT_THEME)
})

test('应用主题会更新根元素、持久化并派发变更事件', () => {
  const storage = createStorage()
  const environment = createEnvironment()

  const applied = applyTheme('jade', { storage, ...environment })

  assert.equal(applied, 'jade')
  assert.equal(environment.root.dataset.theme, 'jade')
  assert.equal(storage.value(), 'jade')
  assert.deepEqual(environment.events, [{
    type: THEME_CHANGE_EVENT,
    detail: { theme: 'jade' },
  }])
})

test('存储写入失败不会阻止当前页面应用主题', () => {
  const environment = createEnvironment()

  const applied = applyTheme('charcoal', {
    storage: createStorage(null, { throwOnSet: true }),
    ...environment,
  })

  assert.equal(applied, 'charcoal')
  assert.equal(environment.root.dataset.theme, 'charcoal')
  assert.equal(environment.events.length, 1)
})

test('初始化主题读取已有选择并应用到根元素', () => {
  const environment = createEnvironment()

  const initialized = initializeTheme({
    storage: createStorage('jade'),
    ...environment,
  })

  assert.equal(initialized, 'jade')
  assert.equal(environment.root.dataset.theme, 'jade')
})

test('样式 Token 定义三套主题与侧栏语义表面', () => {
  assert.match(tokensSource, /:root\s*\{[\s\S]*--surface-sidebar:/)
  assert.match(tokensSource, /:root\[data-theme=['"]jade['"]\]/)
  assert.match(tokensSource, /:root\[data-theme=['"]charcoal['"]\]/)
  assert.match(tokensSource, /--color-accent-500:/)
  assert.match(tokensSource, /--text-sidebar:/)
  assert.match(tokensSource, /--el-color-primary:\s*var\(--color-primary-500\)/)
  assert.match(tokensSource, /--el-color-primary-light-9:\s*var\(--color-primary-50\)/)
})

test('三套主题都覆盖页面、边框和侧栏语义 Token', () => {
  for (const theme of ['ocean', 'jade', 'charcoal']) {
    const block = theme === 'ocean'
      ? tokensSource.match(/:root\s*\{[\s\S]*?\n\}/)?.[0] || ''
      : tokensSource.match(new RegExp(`:root\\[data-theme=['"]${theme}['"]\\]\\s*\\{[\\s\\S]*?\\n\\}`))?.[0] || ''
    assert.match(block, /--surface-page:\s*[^;]+;/, `${theme} 缺少页面背景`)
    assert.match(block, /--border-default:\s*[^;]+;/, `${theme} 缺少默认边框`)
    assert.match(block, /--border-strong:\s*[^;]+;/, `${theme} 缺少强调边框`)
    assert.match(block, /--surface-sidebar:\s*[^;]+;/, `${theme} 缺少侧栏表面`)
  }
})

test('应用入口在创建 Vue 应用前恢复主题', () => {
  assert.match(mainSource, /import\s+\{\s*initializeTheme\s*\}\s+from\s+['"]\.\/theme['"]/) 
  assert.ok(mainSource.indexOf('initializeTheme()') < mainSource.indexOf('createApp(App)'))
})

test('顶部命令栏提供可访问的主题选择器与色板预览', () => {
  assert.match(commandBarSource, /<CommandBarUtilities\s*\/>/)
  assert.match(commandBarUtilitiesSource, /THEMES/)
  assert.match(commandBarUtilitiesSource, /applyTheme/)
  assert.match(commandBarUtilitiesSource, /Brush/)
  assert.match(commandBarUtilitiesSource, /Check/)
  assert.match(commandBarUtilitiesSource, /aria-label="切换界面主题"/)
  assert.match(commandBarUtilitiesSource, /theme-swatch/)
  assert.match(commandBarUtilitiesSource, /currentTheme/)
  assert.match(elementPlusSource, /ElTooltip/)
  assert.match(elementPlusSource, /components\/tooltip\/style\/css/)
  assert.match(elementPlusSource, /ElProgress/)
  assert.match(elementPlusSource, /components\/progress\/style\/css/)
})

test('主题入口在桌面可见且移动端提供三套皮肤菜单项', () => {
  assert.match(commandBarUtilitiesSource, /\.command-utilities__theme\s*\{\s*display:\s*(?:inline-flex|flex)/)
  assert.match(commandBarUtilitiesSource, /:command="`theme:\$\{theme\.key\}`"/)
  assert.match(commandBarUtilitiesSource, /v-for="theme in THEMES"/)
})

test('桌面侧栏消费主题专用表面与文字 Token', () => {
  assert.match(sidebarSource, /background:\s*var\(--surface-sidebar\)/)
  assert.match(sidebarSource, /color:\s*var\(--text-sidebar\)/)
  assert.match(sidebarSource, /var\(--surface-sidebar-hover\)/)
  assert.match(sidebarSource, /var\(--surface-sidebar-active\)/)
})

test('K 线图监听主题事件并在卸载时清理监听器', () => {
  assert.match(klineSource, /THEME_CHANGE_EVENT/)
  assert.match(klineSource, /addEventListener\(THEME_CHANGE_EVENT,\s*refreshTheme\)/)
  assert.match(klineSource, /removeEventListener\(THEME_CHANGE_EVENT,\s*refreshTheme\)/)
  assert.match(klineSource, /themeVersion\.value/)
})
