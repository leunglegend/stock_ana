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
      <p class="tip-dialog__eyebrow">{{ SUPPORT_COPY.dialogEyebrow }}</p>
      <h3 class="tip-dialog__headline">{{ SUPPORT_COPY.dialogHead }}</h3>
      <p class="tip-dialog__sub">{{ SUPPORT_COPY.dialogSub }}</p>

      <p class="tip-dialog__amount">{{ SUPPORT_COPY.amountNote }}</p>
      <p class="tip-dialog__hint">{{ SUPPORT_COPY.scanHint }}</p>

      <div class="qr-grid">
        <figure v-for="side in qrSides" :key="side.key" class="qr-card">
          <figcaption class="qr-card__label">{{ side.label }}</figcaption>
          <img
            v-if="QR_IMAGES[side.key]"
            :src="QR_IMAGES[side.key]"
            :alt="`${side.label}收款二维码(析股台)`"
            class="qr-card__img"
          />
          <div v-else class="qr-card__placeholder" role="img" aria-label="收款码待作者上传">
            <span>{{ side.label }}收款码</span>
            <small>{{ SUPPORT_COPY.qrPlaceholder }}</small>
          </div>
        </figure>
      </div>

      <p class="tip-dialog__trust">{{ SUPPORT_COPY.payeeMask }}</p>
      <p class="tip-dialog__collective">{{ SUPPORT_COPY.thanksCollective }}</p>

      <ol class="tip-dialog__compliance">
        <li>{{ SUPPORT_COPY.compliance1 }}</li>
        <li>{{ SUPPORT_COPY.compliance2 }}</li>
        <li>{{ SUPPORT_COPY.compliance3 }}</li>
      </ol>

      <p v-if="snoozedNotice" class="tip-dialog__snoozed" role="status">
        {{ SUPPORT_COPY.snoozedTip }}
      </p>
    </div>

    <template #footer>
      <el-button text @click="handleLater">{{ SUPPORT_COPY.actionLater }}</el-button>
      <el-button text @click="handleSnooze">{{ SUPPORT_COPY.snoozeAction }}</el-button>
      <el-button type="primary" @click="handleDone">{{ SUPPORT_COPY.actionPrimary }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useResponsive } from '@/composables/useResponsive'
import { useSupportStore } from '@/store/support'
import { QR_IMAGES } from './qrImages'
import { SUPPORT_COPY } from './supportCopy'
import { useSupportUi } from './useSupportUi'

defineProps({ visible: { type: Boolean, default: false } })
const emit = defineEmits(['update:visible'])

const ui = useSupportUi()
const supportStore = useSupportStore()
const { isMobile } = useResponsive()
const snoozedNotice = ref(false)

const dialogWidth = computed(() => (isMobile.value ? 'calc(100vw - 20px)' : '540px'))
const dialogVisible = computed({
  get: () => ui.visible.value,
  set: (value) => emit('update:visible', value),
})

const qrSides = [
  { key: 'wechat', label: SUPPORT_COPY.qrWechatLabel },
  { key: 'alipay', label: SUPPORT_COPY.qrAlipayLabel },
]

function handleDone() { ui.close() }
function handleLater() { ui.close() }
function handleSnooze() {
  supportStore.snoozeDays(30)
  snoozedNotice.value = true
  window.setTimeout(() => {
    snoozedNotice.value = false
    ui.close()
  }, 1400)
}
</script>

<style scoped>
.tip-dialog__body {
  display: grid;
  gap: var(--spacing-3);
}

.tip-dialog__eyebrow {
  margin: 0;
  font-size: var(--font-size-xs);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-support);
}

.tip-dialog__headline {
  margin: 0;
  font-size: var(--font-size-xl);
  line-height: var(--line-height-tight);
  color: var(--text-primary);
}

.tip-dialog__sub,
.tip-dialog__amount,
.tip-dialog__hint,
.tip-dialog__collective,
.tip-dialog__trust,
.tip-dialog__snoozed {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: var(--line-height-relaxed);
}

.tip-dialog__amount {
  color: var(--text-primary);
  font-weight: 500;
}

.tip-dialog__trust {
  font-size: var(--font-size-xs);
  color: var(--text-warning);
}

.tip-dialog__hint { font-size: var(--font-size-xs); }

.qr-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-3);
}

.qr-card {
  margin: 0;
  display: grid;
  justify-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-canvas);
}

.qr-card__label { font-size: var(--font-size-sm); color: var(--text-primary); font-weight: 500; }

.qr-card__img {
  width: 168px;
  height: 168px;
  object-fit: contain;
}

.qr-card__placeholder {
  width: 168px;
  height: 168px;
  display: grid;
  place-content: center;
  gap: var(--spacing-2);
  text-align: center;
  border-radius: var(--radius-sm);
  background: var(--surface-panel-muted);
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}

.qr-card__placeholder small {
  display: block;
  line-height: var(--line-height-normal);
  white-space: pre-line;
}

.tip-dialog__compliance {
  margin: 0;
  padding-left: var(--spacing-4);
  display: grid;
  gap: var(--spacing-1);
  font-size: var(--font-size-xs);
  line-height: var(--line-height-normal);
  color: var(--text-tertiary);
}

.tip-dialog__snoozed { color: var(--color-support); }

@media (max-width: 420px) {
  .qr-grid { grid-template-columns: 1fr; }
  .qr-card__img,
  .qr-card__placeholder { width: 152px; height: 152px; }
}
</style>
