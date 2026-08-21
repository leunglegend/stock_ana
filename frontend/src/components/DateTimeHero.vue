<template>
  <div class="datetime-hero">
    <div class="greeting">{{ greeting }}，投资者</div>
    <div class="time-display">
      {{ hourMin }}<span class="sec">:{{ second }}</span>
    </div>
    <div class="date-row">
      <span class="date-text">{{ dateStr }}</span>
      <span class="divider">·</span>
      <span class="weekday-text">{{ weekdayStr }}</span>
      <span class="divider">·</span>
      <span class="market-tag" :class="{ open: isTradingHours }">
        {{ isTradingHours ? '交易中' : '休市' }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const now = ref(new Date())
let timer = null

const hourMin = computed(() => {
  const d = now.value
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
})

const second = computed(() => {
  return String(now.value.getSeconds()).padStart(2, '0')
})

const dateStr = computed(() => {
  const d = now.value
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
})

const weekdayStr = computed(() => {
  const days = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  return days[now.value.getDay()]
})

const greeting = computed(() => {
  const h = now.value.getHours()
  if (h < 6) return '夜深了'
  if (h < 9) return '早上好'
  if (h < 12) return '上午好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  if (h < 22) return '晚上好'
  return '夜深了'
})

// 判断是否在交易时段（工作日 9:30-11:30, 13:00-15:00）
const isTradingHours = computed(() => {
  const d = now.value
  const day = d.getDay()
  if (day === 0 || day === 6) return false
  const h = d.getHours()
  const m = d.getMinutes()
  const t = h * 60 + m
  // 9:30 - 11:30 或 13:00 - 15:00
  return (t >= 570 && t <= 690) || (t >= 780 && t <= 900)
})

onMounted(() => {
  timer = setInterval(() => {
    now.value = new Date()
  }, 1000)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
})
</script>

<style scoped>
.datetime-hero {
  text-align: center;
  padding: 36px 20px 28px;
  margin-bottom: 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: #fff;
  position: relative;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

.datetime-hero::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

.datetime-hero::after {
  content: '';
  position: absolute;
  bottom: -30%;
  left: -10%;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

.greeting {
  font-size: 15px;
  opacity: 0.85;
  margin-bottom: 8px;
  letter-spacing: 1px;
  position: relative;
  z-index: 1;
}

.time-display {
  font-size: 64px;
  font-weight: 700;
  letter-spacing: 2px;
  line-height: 1.1;
  margin-bottom: 10px;
  font-variant-numeric: tabular-nums;
  position: relative;
  z-index: 1;
  text-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.time-display .sec {
  font-size: 32px;
  opacity: 0.7;
  font-weight: 500;
  margin-left: 2px;
}

.date-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 15px;
  opacity: 0.9;
  position: relative;
  z-index: 1;
}

.divider {
  opacity: 0.5;
}

.market-tag {
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(255,255,255,0.2);
  letter-spacing: 0.5px;
}

.market-tag.open {
  background: rgba(16, 185, 129, 0.35);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

@media (max-width: 600px) {
  .datetime-hero {
    padding: 24px 16px 20px;
  }
  .time-display {
    font-size: 42px;
  }
  .time-display .sec {
    font-size: 22px;
  }
  .date-row {
    font-size: 13px;
    flex-wrap: wrap;
  }
}
</style>
