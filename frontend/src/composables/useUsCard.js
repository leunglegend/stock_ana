// Dashboard「美股收盘」卡片数据：只消费 /api/us/summary，无轮询（收盘复盘）
import { useAsyncSection } from './useAsyncSection'
import { getUsSummary } from '../api/us'

export function useUsCard() {
  const card = useAsyncSection(getUsSummary, { initialData: null })
  return {
    cardData: card.data,
    cardLoading: card.isLoading,
    cardError: card.isError,
    loadCard: card.run,
    retryCard: card.retry,
  }
}
