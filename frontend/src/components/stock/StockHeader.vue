<template>
  <section class="stock-header stock-header--identity">
    <div class="stock-header__main">
      <el-button text @click="$emit('back')">返回</el-button>
      <div data-page-title tabindex="-1" role="heading" aria-level="1">
        <StockName :name="name" :code="code" size="lg" />
      </div>
    </div>

    <div class="stock-header__side">
      <PriceDisplay
        :price="price"
        :change="changeAmount"
        :change-percent="changePercent"
        size="lg"
      />
      <el-button :type="watched ? 'warning' : 'primary'" plain @click="$emit('toggle-watch')">
        {{ watched ? '移出自选' : '加入自选' }}
      </el-button>
    </div>
  </section>
</template>

<script setup>
import PriceDisplay from '../base/PriceDisplay.vue'
import StockName from '../base/StockName.vue'

defineProps({
  name: {
    type: String,
    default: '--',
  },
  code: {
    type: String,
    default: '',
  },
  price: {
    type: Number,
    default: null,
  },
  changeAmount: {
    type: Number,
    default: null,
  },
  changePercent: {
    type: Number,
    default: null,
  },
  watched: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['back', 'toggle-watch'])
</script>

<style scoped>
.stock-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  background: var(--surface-canvas);
}

.stock-header__main,
.stock-header__side {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  min-width: 0;
}

@media (max-width: 767px) {
  .stock-header {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .stock-header__main { grid-column: 1 / -1; }
  .stock-header__side {
    justify-content: space-between;
  }
}
</style>
