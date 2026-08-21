<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="search-overlay" @click.self="close">
        <div class="search-modal" @click.stop>
          <div class="search-input-wrap">
            <el-icon class="search-icon" :size="20" color="#9ca3af">
              <Search />
            </el-icon>
            <input
              ref="inputRef"
              v-model="keyword"
              type="text"
              class="search-input"
              placeholder="输入股票代码或名称搜索，如 600519 或 贵州茅台"
              @input="handleInput"
              @keydown.esc="close"
              @keydown.down="handleArrowDown"
              @keydown.up="handleArrowUp"
              @keydown.enter="handleEnter"
            />
            <div v-if="loading" class="loading-spinner"></div>
            <kbd v-else class="shortcut-hint">ESC</kbd>
          </div>

          <div v-if="keyword && options.length === 0 && !loading" class="empty-state">
            <el-icon :size="32" color="#d1d5db"><Search /></el-icon>
            <p>未找到匹配「{{ keyword }}」的股票</p>
          </div>

          <div v-else-if="options.length > 0" class="search-results">
            <div class="results-label">搜索结果</div>
            <div class="results-list">
              <div
                v-for="(item, index) in options"
                :key="item.code"
                class="result-item"
                :class="{ active: activeIndex === index }"
                @click="selectStock(item)"
                @mouseenter="activeIndex = index"
              >
                <el-icon class="result-icon" :size="16" color="#8b5cf6">
                  <TrendCharts />
                </el-icon>
                <div class="result-info">
                  <span class="result-name">{{ item.name }}</span>
                  <span class="result-code">{{ item.code }}</span>
                </div>
                <span class="result-action">回车查看 →</span>
              </div>
            </div>
          </div>

          <div v-else-if="!keyword" class="search-tips">
            <div class="tips-title">快捷操作</div>
            <div class="tips-list">
              <div class="tip-item">
                <kbd>↑</kbd><kbd>↓</kbd>
                <span>选择结果</span>
              </div>
              <div class="tip-item">
                <kbd>↵</kbd>
                <span>查看详情</span>
              </div>
              <div class="tip-item">
                <kbd>ESC</kbd>
                <span>关闭搜索</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, TrendCharts } from '@element-plus/icons-vue'
import { searchStock } from '../api/stock'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const router = useRouter()
const visible = ref(props.modelValue)
const keyword = ref('')
const options = ref([])
const loading = ref(false)
const activeIndex = ref(0)
const inputRef = ref(null)

let searchTimer = null

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    nextTick(() => {
      inputRef.value?.focus()
      document.body.style.overflow = 'hidden'
    })
  } else {
    document.body.style.overflow = ''
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
  if (!val) {
    // 关闭时清空
    keyword.value = ''
    options.value = []
    activeIndex.value = 0
  }
})

function open() {
  visible.value = true
}

function close() {
  visible.value = false
}

function handleInput() {
  activeIndex.value = 0
  const query = keyword.value.trim()
  if (!query) {
    options.value = []
    return
  }

  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    loading.value = true
    try {
      const res = await searchStock(query)
      options.value = res || []
      activeIndex.value = 0
    } catch (e) {
      options.value = []
    } finally {
      loading.value = false
    }
  }, 250)
}

function handleArrowDown(e) {
  e.preventDefault()
  if (options.value.length === 0) return
  activeIndex.value = (activeIndex.value + 1) % options.value.length
}

function handleArrowUp(e) {
  e.preventDefault()
  if (options.value.length === 0) return
  activeIndex.value = (activeIndex.value - 1 + options.value.length) % options.value.length
}

function handleEnter() {
  if (options.value.length > 0 && activeIndex.value >= 0) {
    selectStock(options.value[activeIndex.value])
  }
}

function selectStock(item) {
  close()
  router.push(`/stock/${item.code}`)
}

// 全局快捷键
function handleKeydown(e) {
  // Cmd/Ctrl + K 打开
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    open()
    return
  }
  // '/' 键在非输入状态下打开
  if (e.key === '/' && !visible.value) {
    const tag = document.activeElement?.tagName
    if (tag !== 'INPUT' && tag !== 'TEXTAREA') {
      e.preventDefault()
      open()
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
  if (searchTimer) clearTimeout(searchTimer)
})

defineExpose({ open, close })
</script>

<style scoped>
.search-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 9999;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
}

.search-modal {
  width: 640px;
  max-width: calc(100vw - 32px);
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

/* 搜索输入区 */
.search-input-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1px solid #f3f4f6;
  position: relative;
}

.search-icon {
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 17px;
  color: #1f2937;
  background: transparent;
  font-family: inherit;
}

.search-input::placeholder {
  color: #9ca3af;
}

.shortcut-hint {
  padding: 3px 8px;
  background: #f3f4f6;
  border-radius: 6px;
  font-size: 12px;
  color: #6b7280;
  font-family: ui-monospace, monospace;
  flex-shrink: 0;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid #e5e7eb;
  border-top-color: #8b5cf6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 搜索结果 */
.search-results {
  max-height: 400px;
  overflow-y: auto;
  padding: 8px 0;
}

.results-label {
  padding: 8px 20px 4px;
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.results-list {
  padding: 4px 8px;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.result-item:hover,
.result-item.active {
  background: #f5f3ff;
}

.result-icon {
  flex-shrink: 0;
}

.result-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.result-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.result-code {
  font-size: 13px;
  color: #9ca3af;
  font-family: ui-monospace, monospace;
}

.result-action {
  font-size: 12px;
  color: #8b5cf6;
  opacity: 0;
  transition: opacity 0.15s;
  flex-shrink: 0;
}

.result-item:hover .result-action,
.result-item.active .result-action {
  opacity: 1;
}

/* 空状态 */
.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: #9ca3af;
}

.empty-state p {
  margin: 12px 0 0;
  font-size: 14px;
}

/* 快捷提示 */
.search-tips {
  padding: 20px;
}

.tips-title {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.tips-list {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #6b7280;
}

.tip-item kbd {
  padding: 2px 7px;
  background: #f3f4f6;
  border-radius: 5px;
  font-family: ui-monospace, monospace;
  font-size: 12px;
  border: 1px solid #e5e7eb;
  border-bottom-width: 2px;
  color: #374151;
}

/* 过渡动画 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-active .search-modal,
.modal-leave-active .search-modal {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .search-modal,
.modal-leave-to .search-modal {
  transform: translateY(-12px) scale(0.98);
  opacity: 0;
}

@media (max-width: 600px) {
  .search-overlay {
    padding-top: 8vh;
  }
  .search-modal {
    border-radius: 12px;
  }
  .search-input {
    font-size: 15px;
  }
  .tips-list {
    gap: 14px;
  }
}
</style>
