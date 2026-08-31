<template>
  <el-dialog
    :model-value="visible"
    :fullscreen="isCompact"
    :width="isCompact ? '100%' : '420px'"
    class="group-picker-dialog"
    title="选择分组"
    @close="$emit('close')"
    @update:model-value="handleDialogChange"
  >
    <div class="group-picker">
      <label v-for="group in groups" :key="group.id" class="group-picker__option">
        <input :checked="modelValue === group.id" type="radio" name="watchlist-group" @change="$emit('update:modelValue', group.id)">
        <span>{{ group.name }}</span>
      </label>
    </div>

    <template #footer>
      <el-button @click="$emit('close')">取消</el-button>
      <el-button type="primary" :disabled="!modelValue" @click="$emit('confirm', modelValue)">加入分组</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

defineProps({
  visible: { type: Boolean, default: false },
  modelValue: { type: [String, Number], default: '' },
  groups: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'confirm', 'update:modelValue'])
const isCompact = ref(typeof window !== 'undefined' && window.innerWidth <= 600)

function updateViewportMode() { isCompact.value = window.innerWidth <= 600 }
function handleDialogChange(value) { if (!value) emit('close') }

onMounted(() => window.addEventListener('resize', updateViewportMode, { passive: true }))
onUnmounted(() => window.removeEventListener('resize', updateViewportMode))
</script>

<style scoped>
.group-picker { display: grid; gap: var(--spacing-3); }
.group-picker__option {
  display: flex; align-items: center; gap: var(--spacing-3); min-height: 44px; padding: 0 var(--spacing-4);
  border: 1px solid var(--border-subtle); border-radius: var(--radius-md); background: var(--surface-panel-muted); cursor: pointer;
}
:deep(.group-picker-dialog) { max-width: calc(100vw - 24px); }
:deep(.group-picker-dialog .el-dialog__body) { padding-top: 0; overflow: auto; }

@media (max-width: 600px) {
  :deep(.group-picker-dialog) { margin: 0; max-width: none; }
  :deep(.group-picker-dialog .el-dialog__body) { max-height: calc(100dvh - 128px); }
}
</style>
