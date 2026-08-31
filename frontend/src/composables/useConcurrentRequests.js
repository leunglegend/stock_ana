export async function runWithConcurrency(items, worker, limit = 4, onSettled) {
  if (!Array.isArray(items)) throw new TypeError('items must be an array')
  if (typeof worker !== 'function') throw new TypeError('worker must be a function')

  const normalizedLimit = Number(limit)
  if (!Number.isInteger(normalizedLimit) || normalizedLimit < 1) {
    throw new RangeError('limit must be an integer greater than 0')
  }
  if (items.length === 0) return []

  const results = new Array(items.length)
  let nextIndex = 0
  const workerCount = Math.min(normalizedLimit, items.length)

  const runNext = async () => {
    while (nextIndex < items.length) {
      const index = nextIndex++
      const settled = await settleItem(items, worker, index)
      results[index] = settled
      notifySettled(onSettled, settled, index, items[index])
    }
  }

  await Promise.all(Array.from({ length: workerCount }, runNext))
  return results
}

async function settleItem(items, worker, index) {
  try {
    const value = await worker(items[index], index, items)
    return { status: 'fulfilled', value }
  } catch (reason) {
    return { status: 'rejected', reason }
  }
}

function notifySettled(onSettled, settled, index, item) {
  if (typeof onSettled !== 'function') return
  try {
    onSettled(settled, index, item)
  } catch (error) {
    console.error('runWithConcurrency onSettled error:', error)
  }
}
