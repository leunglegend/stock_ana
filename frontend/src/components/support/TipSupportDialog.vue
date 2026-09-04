<template>
  <el-dialog
    v-model="dialogVisible"
    class="tip-dialog"
    :title="null"
    :width="dialogWidth"
    align-center
    append-to-body
  >
    <div class="tip-dialog__body">
      <p class="tip-dialog__headline">股东增资卡(骨架先行,文案与码图随 Task 5 落地)</p>
      <p class="tip-dialog__sub">打赏支持 · 微信 / 支付宝个人收款码</p>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { useResponsive } from '@/composables/useResponsive'
import { useSupportUi } from './useSupportUi'

defineProps({ visible: { type: Boolean, default: false } })
const emit = defineEmits(['update:visible'])

const ui = useSupportUi()
const { isMobile } = useResponsive()
const dialogWidth = computed(() => (isMobile.value ? 'calc(100vw - 20px)' : '540px'))

const dialogVisible = computed({
  get: () => ui.visible.value,
  set: (value) => emit('update:visible', value),
})
</script>
