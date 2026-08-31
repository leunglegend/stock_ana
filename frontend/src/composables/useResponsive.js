import { computed, onMounted, onUnmounted, ref } from 'vue'

const DESKTOP_MIN = 1024
const TABLET_MIN = 768

export function useResponsive() {
  const width = ref(typeof window === 'undefined' ? DESKTOP_MIN : window.innerWidth)

  const updateWidth = () => {
    width.value = window.innerWidth
  }

  onMounted(() => {
    updateWidth()
    window.addEventListener('resize', updateWidth, { passive: true })
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateWidth)
  })

  return {
    width,
    isMobile: computed(() => width.value < TABLET_MIN),
    isTablet: computed(() => width.value >= TABLET_MIN && width.value < DESKTOP_MIN),
    isDesktop: computed(() => width.value >= DESKTOP_MIN),
  }
}
