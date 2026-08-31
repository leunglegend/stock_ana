<template>
  <section class="radar-toolbar" aria-label="机会雷达筛选工具">
    <div class="radar-toolbar__main">
      <label class="radar-toolbar__field radar-toolbar__field--type">
        <span class="radar-toolbar__label">板块类型</span>
        <el-segmented
          v-model="typeValue"
          class="radar-toolbar__segmented"
          :options="typeOptions"
          aria-label="切换行业板块或概念板块"
          :disabled="disabled"
        />
      </label>

      <label class="radar-toolbar__field radar-toolbar__field--search">
        <span class="radar-toolbar__label">按板块名称筛选</span>
        <el-input
          v-model="keywordValue"
          clearable
          placeholder="按板块名称筛选"
          aria-label="按板块名称筛选"
          :disabled="disabled"
        />
      </label>

      <label class="radar-toolbar__field radar-toolbar__field--switch">
        <span class="radar-toolbar__label">仅看上涨</span>
        <el-switch
          v-model="onlyRisingValue"
          aria-label="仅看上涨"
          :disabled="disabled"
        />
      </label>
    </div>

    <div class="radar-toolbar__actions">
      <el-tooltip content="刷新当前榜单和成分股" placement="top">
        <el-button
          plain
          :loading="refreshing"
          :disabled="disabled"
          aria-label="刷新机会雷达"
          @click="$emit('refresh')"
        >
          <el-icon><RefreshRight /></el-icon>
          刷新
        </el-button>
      </el-tooltip>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { RefreshRight } from '@element-plus/icons-vue'

const props = defineProps({
  type: {
    type: String,
    default: 'industry',
  },
  keyword: {
    type: String,
    default: '',
  },
  onlyRising: {
    type: Boolean,
    default: false,
  },
  refreshing: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:type', 'update:keyword', 'update:only-rising', 'refresh'])

const typeOptions = [
  { label: '行业板块', value: 'industry' },
  { label: '概念板块', value: 'concept' },
]

const typeValue = computed({
  get: () => props.type,
  set: (value) => emit('update:type', value),
})

const keywordValue = computed({
  get: () => props.keyword,
  set: (value) => emit('update:keyword', value),
})

const onlyRisingValue = computed({
  get: () => props.onlyRising,
  set: (value) => emit('update:only-rising', value),
})

</script>

<style scoped>
.radar-toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--spacing-2);
  padding: var(--spacing-1) 0 var(--spacing-2);
  border-bottom: 1px solid var(--border-subtle);
}

.radar-toolbar__main,
.radar-toolbar__actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  min-width: 0;
}

.radar-toolbar__main {
  flex-wrap: wrap;
}

.radar-toolbar__actions {
  justify-content: flex-end;
}

.radar-toolbar__field {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 0;
}

.radar-toolbar__field--type {
  min-width: 224px;
}

.radar-toolbar__field--search {
  flex: 1 1 280px;
}

.radar-toolbar__field--switch {
  min-width: 104px;
}

.radar-toolbar__label {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.radar-toolbar__segmented {
  min-height: var(--control-height);
}

@media (max-width: 1023px) {
  .radar-toolbar {
    grid-template-columns: minmax(0, 1fr);
  }

  .radar-toolbar__actions {
    justify-content: flex-end;
  }
}

@media (max-width: 767px) {
  .radar-toolbar {
    padding-block: var(--spacing-1) var(--spacing-2);
  }

  .radar-toolbar__main,
  .radar-toolbar__actions {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    align-items: stretch;
  }

  .radar-toolbar__field--type,
  .radar-toolbar__field--switch {
    min-width: 0;
  }

  .radar-toolbar__segmented,
  .radar-toolbar :deep(.el-input__wrapper),
  .radar-toolbar :deep(.el-switch) {
    min-height: var(--mobile-control-height);
    touch-action: manipulation;
  }

  .radar-toolbar__actions {
    gap: var(--spacing-2);
  }

  .radar-toolbar__actions :deep(.el-button) {
    width: 100%;
    min-height: var(--mobile-control-height);
  }
}
</style>
