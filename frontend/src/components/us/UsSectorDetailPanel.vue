<template>
  <BoardDetailPanel
    class="us-sector-detail"
    market="us"
    :visible="visible"
    :loading="loading"
    :error="error"
    :mobile="mobile"
    :board="adaptedBoard"
    :stocks="adaptedStocks"
    @close="$emit('close')"
    @retry="$emit('retry')"
    @open-stock="$emit('open-symbol', $event)"
  />
</template>

<script setup>
import { computed } from 'vue'
import BoardDetailPanel from '../board/BoardDetailPanel.vue'
import { toUsBoard, toUsStock } from '../../utils/usBoardPresentation'

const props = defineProps({
  visible: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  error: { type: Boolean, default: false },
  mobile: { type: Boolean, default: false },
  board: { type: Object, default: null },
  stocks: { type: Array, default: () => [] },
})
defineEmits(['close', 'retry', 'open-symbol'])
const adaptedBoard = computed(() => props.board ? toUsBoard(props.board) : null)
const adaptedStocks = computed(() => props.stocks.map(toUsStock))
</script>
