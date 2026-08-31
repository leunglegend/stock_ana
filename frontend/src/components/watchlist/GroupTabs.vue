<template>
  <section class="group-tabs">
    <div class="group-tabs__list" role="tablist" aria-label="自选分组" @keydown="handleKeydown">
      <button
        v-for="(group, index) in groups"
        :key="group.id"
        :ref="(el) => setTabRef(el, index)"
        class="group-tabs__tab"
        :class="{ 'is-active': group.id === activeId }"
        role="tab"
        :aria-selected="group.id === activeId"
        :tabindex="group.id === activeId ? 0 : -1"
        type="button"
        @click="$emit('change', group.id)"
      >
        <span class="group-tabs__name">{{ group.name }}</span>
        <span class="group-tabs__count">{{ group.stocks?.length || 0 }} 只</span>
      </button>
    </div>
    <el-dropdown trigger="click" @command="handleCommand">
      <el-button text circle aria-label="管理自选分组"><el-icon><MoreFilled /></el-icon></el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="create">新建分组</el-dropdown-item>
          <el-dropdown-item command="rename" :disabled="!activeId">重命名当前分组</el-dropdown-item>
          <el-dropdown-item command="remove" divided :disabled="groups.length <= 1 || !activeId">删除当前分组</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </section>
</template>

<script setup>
import { nextTick, onBeforeUpdate, ref } from 'vue'
import { MoreFilled } from '@element-plus/icons-vue'

const props = defineProps({
  groups: { type: Array, default: () => [] },
  activeId: { type: String, default: '' },
})

const emit = defineEmits(['change', 'create', 'rename', 'remove'])
const tabRefs = ref([])

onBeforeUpdate(() => { tabRefs.value = [] })

function setTabRef(element, index) {
  if (element) tabRefs.value[index] = element
}

function focusTab(index) {
  nextTick(() => {
    const target = tabRefs.value[index]
    target?.focus()
    target?.scrollIntoView({ inline: 'nearest', block: 'nearest' })
  })
}

function handleKeydown(event) {
  if (props.groups.length < 2) return
  const currentIndex = props.groups.findIndex((group) => group.id === props.activeId)
  if (currentIndex < 0) return
  const move = { ArrowRight: 1, ArrowLeft: -1, Home: 'start', End: 'end' }[event.key]
  if (move == null) return
  event.preventDefault()
  const nextIndex = move === 'start'
    ? 0
    : move === 'end'
      ? props.groups.length - 1
      : (currentIndex + move + props.groups.length) % props.groups.length
  emit('change', props.groups[nextIndex].id)
  focusTab(nextIndex)
}

function handleCommand(command) {
  emit(command, props.activeId)
}
</script>

<style scoped>
.group-tabs { display: flex; align-items: center; min-width: 0; gap: var(--spacing-1); }
.group-tabs__list { display: flex; min-width: 0; gap: var(--spacing-1); overflow-x: auto; scrollbar-width: thin; }
.group-tabs__tab {
  display: inline-flex; align-items: center; gap: var(--spacing-2); min-height: var(--control-height); padding: 0 var(--spacing-3);
  border: 1px solid transparent; border-radius: var(--radius-control); background: transparent;
  color: var(--text-secondary); font: inherit; white-space: nowrap; cursor: pointer; transition: all var(--transition-fast);
}
.group-tabs__tab:hover { background: var(--state-hover); color: var(--text-primary); }
.group-tabs__tab:focus-visible { outline: 2px solid var(--color-primary-500); outline-offset: 2px; }
.group-tabs__tab.is-active { border-color: var(--border-default); background: var(--state-selected); color: var(--color-primary-700); }
.group-tabs__name { font-weight: 600; }
.group-tabs__count { font-size: var(--font-size-xs); color: inherit; opacity: .8; }
@media (max-width: 767px) {
  .group-tabs__tab { min-height: 44px; }
}
</style>
