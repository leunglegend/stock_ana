<template>
  <div class="stock-search">
    <el-select
      v-model="selectedCode"
      filterable
      remote
      reserve-keyword
      placeholder="输入股票代码或名称，如 600519 或 贵州茅台"
      :remote-method="handleSearch"
      :loading="loading"
      @change="handleChange"
      class="search-select"
    >
      <el-option
        v-for="item in options"
        :key="item.code"
        :label="`${item.name} (${item.code})`"
        :value="item.code"
      />
      <template #empty>
        <div v-if="!loading && keyword" class="empty-tip">
          未找到匹配的股票
        </div>
      </template>
    </el-select>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { searchStock } from '../api/stock'

const emit = defineEmits(['select'])

const selectedCode = ref('')
const options = ref([])
const loading = ref(false)
const keyword = ref('')

let searchTimer = null
let searchRequestId = 0

function handleSearch(query) {
  const requestId = ++searchRequestId
  keyword.value = query
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = null

  if (!query || query.length < 1) {
    options.value = []
    loading.value = false
    return
  }

  searchTimer = setTimeout(() => runSearch(requestId, query), 300)
}

function isCurrentSearch(requestId, query) {
  return requestId === searchRequestId && query === keyword.value
}

async function runSearch(requestId, query) {
  if (!isCurrentSearch(requestId, query)) return
  searchTimer = null
  loading.value = true
  try {
    const res = await searchStock(query)
    if (!isCurrentSearch(requestId, query)) return
    options.value = res || []
  } catch {
    if (!isCurrentSearch(requestId, query)) return
    options.value = []
  } finally {
    if (isCurrentSearch(requestId, query)) loading.value = false
  }
}

function handleChange(value) {
  if (value) {
    // 从 options 中找到完整的 stock 对象再 emit
    const item = options.value.find(o => o.code === value)
    if (item) {
      emit('select', item)
    }
  }
}

onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = null
  searchRequestId += 1
})
</script>

<style scoped>
.stock-search {
  width: 100%;
}

.search-select {
  width: 100%;
}

.empty-tip {
  padding: 12px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}
</style>
