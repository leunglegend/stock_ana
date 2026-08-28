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
      size="large"
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
import { ref, onMounted } from 'vue'
import { searchStock } from '../api/stock'

const emit = defineEmits(['select'])

const selectedCode = ref('')
const options = ref([])
const loading = ref(false)
const keyword = ref('')

let searchTimer = null

function handleSearch(query) {
  keyword.value = query
  if (!query || query.length < 1) {
    options.value = []
    return
  }

  // 防抖
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    loading.value = true
    try {
      const res = await searchStock(query)
      options.value = res || []
    } catch (e) {
      options.value = []
    } finally {
      loading.value = false
    }
  }, 300)
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
</script>

<style scoped>
.stock-search {
  width: 100%;
}

.search-select {
  width: 100%;
}

/* 覆盖 Element Plus 样式，让搜索框在深色背景上更明显 */
:deep(.el-select .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-select .el-input__wrapper:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.empty-tip {
  padding: 12px;
  text-align: center;
  color: #9ca3af;
  font-size: 14px;
}
</style>
