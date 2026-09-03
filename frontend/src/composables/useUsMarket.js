// 美股复盘页数据编排：摘要 + 板块榜（useAsyncSection）+ AI 一句话（SSE）
import { ref } from 'vue'
import { useAsyncSection } from './useAsyncSection'
import { getUsAiSummary, getUsSectors, getUsSummary } from '../api/us'

export function useUsMarket() {
  const summarySection = useAsyncSection(getUsSummary, { initialData: null })
  const sectorsSection = useAsyncSection(getUsSectors, { initialData: [] })

  const aiText = ref('')
  const aiLoading = ref(false)
  const aiError = ref(false)
  let aiSource = null
  let aiRequestId = 0

  async function generateAiSummary() {
    const requestId = ++aiRequestId
    if (aiSource) { aiSource.close(); aiSource = null }
    aiLoading.value = true
    aiError.value = false
    aiText.value = ''
    try {
      aiSource = getUsAiSummary(
        (chunk) => { if (requestId === aiRequestId) aiText.value += chunk },
        () => { if (requestId === aiRequestId) aiLoading.value = false },
        () => { if (requestId === aiRequestId) { aiLoading.value = false; aiError.value = true } },
      )
    } catch (e) {
      aiLoading.value = false
      aiError.value = true
    }
  }

  function closeAiSource() {
    aiRequestId += 1
    if (aiSource) { aiSource.close(); aiSource = null }
    aiLoading.value = false
  }

  return {
    summarySection, sectorsSection,
    aiText, aiLoading, aiError,
    loadSummary: summarySection.run,
    loadSectors: sectorsSection.run,
    generateAiSummary, closeAiSource,
  }
}
