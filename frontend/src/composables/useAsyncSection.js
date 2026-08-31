import { computed, ref } from 'vue'

export const ASYNC_SECTION_STALE = Object.freeze({
  superseded: 'superseded',
  noPreviousRun: 'no-previous-run',
})

function isSectionEmpty(options, value) {
  if (typeof options.isEmpty === 'function') return options.isEmpty(value)
  if (Array.isArray(value)) return value.length === 0
  return value == null
}

function createStaleResult(reason, payload = {}) {
  return { stale: true, reason, ...payload }
}

function applySettledState(section, options, requestId, nextData, nextError) {
  if (requestId !== section.activeRequestId) return false
  section.data.value = nextData
  section.error.value = nextError
  section.hasLoaded.value = true
  section.state.value = nextError ? 'error' : isSectionEmpty(options, nextData) ? 'empty' : 'success'
  return true
}

function createState(initialData) {
  return {
    state: ref('idle'),
    data: ref(initialData),
    error: ref(null),
    hasLoaded: ref(false),
    hasRun: ref(false),
    activeRequestId: 0,
    lastArgs: [],
  }
}

function createStateFlags(state) {
  return {
    isIdle: computed(() => state.value === 'idle'),
    isLoading: computed(() => state.value === 'loading'),
    isSuccess: computed(() => state.value === 'success'),
    isEmpty: computed(() => state.value === 'empty'),
    isError: computed(() => state.value === 'error'),
  }
}

export function useAsyncSection(loader, options = {}) {
  if (typeof loader !== 'function') throw new TypeError('loader must be a function')
  const initialData = options.initialData ?? null
  const section = createState(initialData)
  const canRetry = computed(() => section.hasRun.value)

  const run = async (...args) => {
    const requestId = ++section.activeRequestId
    section.hasRun.value = true
    section.lastArgs = args
    section.state.value = 'loading'
    section.error.value = null

    try {
      const result = await loader(...args)
      return applySettledState(section, options, requestId, result, null)
        ? result
        : createStaleResult(ASYNC_SECTION_STALE.superseded, { data: result })
    } catch (caughtError) {
      if (applySettledState(section, options, requestId, section.data.value, caughtError)) {
        throw caughtError
      }
      return createStaleResult(ASYNC_SECTION_STALE.superseded, { error: caughtError })
    }
  }

  const retry = (...args) => {
    if (args.length > 0) return run(...args)
    if (!canRetry.value) {
      return Promise.resolve(createStaleResult(ASYNC_SECTION_STALE.noPreviousRun))
    }
    return run(...section.lastArgs)
  }

  const reset = () => {
    section.activeRequestId += 1
    section.lastArgs = []
    section.hasRun.value = false
    section.state.value = 'idle'
    section.data.value = initialData
    section.error.value = null
    section.hasLoaded.value = false
  }

  return {
    state: section.state,
    data: section.data,
    error: section.error,
    hasLoaded: section.hasLoaded,
    canRetry,
    ...createStateFlags(section.state),
    run,
    retry,
    reset,
  }
}
