<template>
  <Teleport to="body">
    <Transition name="search-fade">
      <div
        v-if="visible"
        class="search-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="global-search-title"
        @click.self="close"
        @keydown="handleDialogKeydown"
      >
        <section ref="dialogRef" class="search-dialog__panel">
          <header class="search-dialog__header">
            <p id="global-search-title" class="search-dialog__title">全局搜索</p>
            <button class="search-dialog__close" type="button" aria-label="关闭搜索" @click="close">ESC</button>
          </header>

          <div class="search-dialog__input-row">
            <el-icon class="search-dialog__icon"><Search /></el-icon>
            <input
              ref="inputRef"
              v-model="keyword"
              class="search-dialog__input"
              type="text"
              autocomplete="off"
              aria-label="全局搜索股票代码或名称"
              placeholder="例如 600519 / 贵州茅台"
              @input="handleInput"
            />
            <span v-if="loading" class="search-dialog__hint">搜索中</span>
          </div>

          <div v-if="keyword && !loading && options.length === 0" class="search-dialog__empty" aria-live="polite">
            未找到匹配结果
          </div>

          <ul v-else-if="options.length > 0" class="search-dialog__results" role="listbox" :aria-activedescendant="activeOptionId">
            <li v-for="(item, index) in options" :id="optionId(index)" :key="item.code" role="option" :aria-selected="activeIndex === index">
              <button class="search-dialog__result" :class="{ 'is-active': activeIndex === index }" type="button" @mouseenter="activeIndex = index" @click="selectStock(item)">
                <span class="search-dialog__result-name">{{ item.name }}</span>
                <span class="search-dialog__result-code">{{ item.code }}</span>
                <span class="search-dialog__result-action">查看详情</span>
              </button>
            </li>
          </ul>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { searchStock } from '../api/stock'

const props = defineProps({ modelValue: { type: Boolean, default: false } })
const emit = defineEmits(['update:modelValue'])
const router = useRouter()
const visible = ref(props.modelValue)
const keyword = ref('')
const options = ref([])
const loading = ref(false)
const activeIndex = ref(-1)
const dialogRef = ref(null)
const inputRef = ref(null)
const lastFocusedElement = ref(null)
const activeOptionId = computed(() => activeIndex.value >= 0 ? optionId(activeIndex.value) : undefined)
let searchTimer = null
let searchRequestId = 0

watch(() => props.modelValue, (value) => { visible.value = value })
watch(visible, (value) => {
  emit('update:modelValue', value)
  if (value) openDialog()
  else closeDialog()
})

function optionId(index) { return `global-search-option-${index}` }
function open() { visible.value = true }
function close() { visible.value = false }

function clearSearchTimer() {
  if (!searchTimer) return
  window.clearTimeout(searchTimer)
  searchTimer = null
}

function invalidateSearch() {
  searchRequestId += 1
  clearSearchTimer()
  loading.value = false
  options.value = []
  activeIndex.value = -1
}

function openDialog() {
  lastFocusedElement.value = document.activeElement instanceof HTMLElement ? document.activeElement : null
  document.body.style.overflow = 'hidden'
  nextTick(() => inputRef.value?.focus({ preventScroll: true }))
}

function closeDialog() {
  keyword.value = ''
  invalidateSearch()
  document.body.style.overflow = ''
  if (lastFocusedElement.value instanceof HTMLElement && document.contains(lastFocusedElement.value)) {
    lastFocusedElement.value.focus()
  }
  lastFocusedElement.value = null
}

function scheduleSearch(query) {
  clearSearchTimer()
  searchTimer = window.setTimeout(async () => {
    const requestId = ++searchRequestId
    loading.value = true
    try {
      const result = await searchStock(query)
      if (requestId !== searchRequestId || !visible.value || query !== keyword.value.trim()) return
      options.value = result || []
      activeIndex.value = options.value.length > 0 ? 0 : -1
    } catch {
      if (requestId !== searchRequestId || !visible.value) return
      options.value = []
      activeIndex.value = -1
    } finally {
      if (requestId === searchRequestId) loading.value = false
    }
  }, 220)
}

function handleInput() {
  const query = keyword.value.trim()
  if (!query) return invalidateSearch()
  scheduleSearch(query)
}

function goToSearchPage() {
  const query = keyword.value.trim()
  close()
  router.push({ path: '/search', query: query ? { q: query } : undefined })
}

function selectStock(item) {
  close()
  router.push(`/stock/${item.code}`)
}

function trapFocus(event) {
  const root = dialogRef.value
  if (!(root instanceof HTMLElement)) return
  const selector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  const nodes = Array.from(root.querySelectorAll(selector)).filter((node) => !node.hasAttribute('disabled'))
  if (nodes.length === 0) return
  const first = nodes[0]
  const last = nodes[nodes.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

function handleDialogKeydown(event) {
  if (event.key === 'Escape') return void (event.preventDefault(), close())
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    if (options.value.length > 0) activeIndex.value = (activeIndex.value + 1 + options.value.length) % options.value.length
    return
  }
  if (event.key === 'ArrowUp') {
    event.preventDefault()
    if (options.value.length > 0) activeIndex.value = (activeIndex.value - 1 + options.value.length) % options.value.length
    return
  }
  if (event.key === 'Enter') {
    event.preventDefault()
    if (options.value[activeIndex.value]) selectStock(options.value[activeIndex.value])
    else goToSearchPage()
    return
  }
  if (event.key === 'Tab') trapFocus(event)
}

function handleWindowKeydown(event) {
  const tag = document.activeElement?.tagName
  const isTyping = tag === 'INPUT' || tag === 'TEXTAREA' || document.activeElement?.isContentEditable
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') return void (event.preventDefault(), open())
  if (event.key === '/' && !visible.value && !isTyping) return void (event.preventDefault(), open())
}

onMounted(() => window.addEventListener('keydown', handleWindowKeydown))
onUnmounted(() => {
  invalidateSearch()
  window.removeEventListener('keydown', handleWindowKeydown)
  document.body.style.overflow = ''
})

defineExpose({ open, close })
</script>

<style scoped>
.search-dialog {
  position: fixed; inset: 0; z-index: var(--z-dialog); display: grid; place-items: start center; padding: 9vh 20px 20px;
  background: var(--surface-overlay); backdrop-filter: blur(10px);
}
.search-dialog__panel {
  width: min(760px, 100%); background: var(--surface-canvas); border: 1px solid var(--border-subtle); border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg); overflow: hidden;
}
.search-dialog__header, .search-dialog__input-row { padding-inline: var(--spacing-5); }
.search-dialog__header {
  display: flex; align-items: flex-start; justify-content: space-between; gap: var(--spacing-4); padding-top: var(--spacing-5);
}
.search-dialog__title { margin: 0; color: var(--text-primary); font-size: var(--font-size-lg); font-weight: 700; }
.search-dialog__hint { color: var(--text-tertiary); font-size: var(--font-size-sm); }
.search-dialog__close {
  min-height: 36px; padding: 0 12px; border: 1px solid var(--border); border-radius: var(--radius-md);
  background: var(--surface-panel-muted); color: var(--text-secondary); cursor: pointer;
}
.search-dialog__input-row {
  display: flex; align-items: center; gap: var(--spacing-3); padding-top: var(--spacing-4); padding-bottom: var(--spacing-4); border-bottom: 1px solid var(--border-subtle);
}
.search-dialog__icon { color: var(--text-tertiary); }
.search-dialog__input {
  flex: 1; min-height: 44px; border: 0; background: transparent; color: var(--text-primary); font-size: var(--font-size-xl);
}
.search-dialog__close:focus-visible, .search-dialog__input:focus-visible, .search-dialog__result:focus-visible {
  outline: 2px solid var(--focus-ring); outline-offset: 2px;
}
.search-dialog__empty { padding: var(--spacing-5); color: var(--text-secondary); }
.search-dialog__results { margin: 0; padding: var(--spacing-3); list-style: none; max-height: 420px; overflow: auto; }
.search-dialog__result {
  display: grid; grid-template-columns: minmax(0, 1fr) auto auto; align-items: center; gap: var(--spacing-3); width: 100%; min-height: 48px;
  padding: 0 var(--spacing-4); border: 0; border-radius: var(--radius-md); background: transparent; color: var(--text-primary); cursor: pointer; text-align: left;
}
.search-dialog__result:hover, .search-dialog__result.is-active { background: var(--surface-panel-muted); }
.search-dialog__result-name { font-weight: 600; }
.search-dialog__result-code { color: var(--text-tertiary); font-family: var(--font-family-mono); font-size: var(--font-size-sm); }
.search-dialog__result-action { color: var(--color-primary-600); font-size: var(--font-size-sm); }
.search-fade-enter-active, .search-fade-leave-active { transition: opacity var(--transition-fast); }
.search-fade-enter-from, .search-fade-leave-to { opacity: 0; }

@media (max-width: 767px) {
  .search-dialog { padding: 0; }
  .search-dialog__panel { min-height: 100vh; min-height: 100dvh; border-radius: 0; }
  .search-dialog__result { grid-template-columns: 1fr; gap: 6px; padding-block: 12px; }
  .search-dialog__result-action { font-size: var(--font-size-xs); }
}
</style>
