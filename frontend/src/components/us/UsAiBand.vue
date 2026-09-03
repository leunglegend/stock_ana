<template>
  <MarketAiSummary
    :text="text"
    :loading="loading"
    :error="error"
    label="今日主线"
    @refresh="$emit('refresh')"
  />
</template>

<script setup>
// 美股复盘「今日主线」AI 一句话通栏：仅透传 MarketAiSummary 并固定 label
import MarketAiSummary from '../dashboard/MarketAiSummary.vue'

defineProps({
  text: {
    type: String,
    default: '',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['refresh'])
</script>
