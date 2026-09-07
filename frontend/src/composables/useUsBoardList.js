import { computed, ref, watch } from 'vue'

export function useUsBoardList(sectors) {
  const keyword = ref('')
  const sortKey = ref('change_pct')
  const page = ref(1)
  const pageSize = 10
  const filteredSectors = computed(() => {
    const query = keyword.value.trim().toLowerCase()
    return [...(sectors.value || [])]
      .filter((sector) => !query || [sector.name, sector.name_en].some((name) => String(name || '').toLowerCase().includes(query)))
      .sort((left, right) => (right[sortKey.value] ?? -Infinity) - (left[sortKey.value] ?? -Infinity))
  })
  const paginatedSectors = computed(() => filteredSectors.value.slice((page.value - 1) * pageSize, page.value * pageSize))
  watch([keyword, sortKey, sectors], () => { page.value = 1 })
  return { keyword, sortKey, page, pageSize, filteredSectors, paginatedSectors }
}
