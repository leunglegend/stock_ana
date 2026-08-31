<template>
  <header class="monitor-header">
    <div>
      <h1 data-page-title>盘中监控</h1>
      <p aria-live="polite">
        <template v-if="refreshError">刷新失败，显示上次成功数据 · 更新于 {{ updatedLabel }}</template>
        <template v-else-if="stale">部分数据已延迟 · 更新于 {{ updatedLabel }}</template>
        <template v-else>更新于 {{ updatedLabel }}</template>
      </p>
    </div>
    <div class="monitor-header__actions">
      <el-select :model-value="activeGroupId" aria-label="选择监控分组" style="width: 150px" @update:model-value="$emit('update:groupId', $event)">
        <el-option label="全部自选" value="all" />
        <el-option v-for="group in groups" :key="group.id" :label="group.name" :value="String(group.id)" />
      </el-select>
      <el-button :loading="loading" plain aria-label="刷新盘中监控" @click="$emit('refresh')">刷新</el-button>
    </div>
  </header>
</template>
<script setup>
import { computed } from 'vue'
import { formatFetchTime } from '@/utils/format'
const props = defineProps({ groups: { type: Array, default: () => [] }, activeGroupId: { type: String, default: 'all' }, loading: { type: Boolean, default: false }, asOf: { type: [String, Date, Number], default: null }, stale: { type: Boolean, default: false }, refreshError: { type: Boolean, default: false } })
defineEmits(['update:groupId', 'refresh'])
const updatedLabel = computed(() => formatFetchTime(props.asOf))
</script>
<style scoped>
.monitor-header { display: flex; align-items: center; justify-content: space-between; gap: var(--spacing-3); min-height: 52px; padding: 0 var(--spacing-3); border-bottom: 1px solid var(--border-subtle); }
.monitor-header h1 { margin: 0; color: var(--text-primary); font-size: var(--font-size-2xl); }
.monitor-header p { margin: 4px 0 0; color: var(--text-tertiary); font-size: var(--font-size-xs); }
.monitor-header__actions { display: flex; align-items: center; gap: var(--spacing-2); }
@media (max-width: 767px) { .monitor-header { align-items: flex-start; flex-direction: column; padding-block: var(--spacing-3); } .monitor-header__actions { width: 100%; } .monitor-header__actions :deep(.el-select) { flex: 1; } }
</style>
