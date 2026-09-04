import { ref } from 'vue'

// 全站唯一的打赏卡可见性:顶栏 SupportButton 与页脚 SiteFooter 共用同一实例,
// 因此无论从哪个入口点开,都只会有一张打赏卡。
const visible = ref(false)

export function useSupportUi() {
  function open() { visible.value = true }
  function close() { visible.value = false }
  return { visible, open, close }
}
