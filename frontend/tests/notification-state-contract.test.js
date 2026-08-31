import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const [bell, notifications] = await Promise.all([
  readFile(new URL('../src/components/NotificationBell.vue', import.meta.url), 'utf8'),
  readFile(new URL('../src/composables/useNotifications.js', import.meta.url), 'utf8'),
])

test('通知列表请求失败展示独立错误状态并提供重试', () => {
  assert.match(notifications, /const notificationError = ref\(''\)/)
  assert.match(notifications, /notificationError\.value = '通知加载失败，请重试'/)
  assert.match(notifications, /function retryNotifications\(\)\s*\{\s*return fetchNotifications\(\)/)
  assert.match(bell, /v-if="!loading && notificationError"/)
  assert.match(bell, /@click\.stop="retryNotifications"/)
  assert.match(bell, /\{\{ notificationError \}\}/)
})

test('通知菜单不将查看全部跳转到无关报告页', () => {
  assert.doesNotMatch(bell, /查看全部/)
  assert.doesNotMatch(notifications, /goToReports/)
  assert.doesNotMatch(notifications, /router\.push\('\/reports'\)/)
})

test('登出或切换账号后，过期通知响应不能回写当前会话', () => {
  assert.match(notifications, /function createNotificationSessionGuard\(\)/)
  assert.match(notifications, /generation \+= 1/)
  assert.match(notifications, /userStore\.token === session\.token/)
  assert.match(notifications, /userStore\.userInfo\?\.id === session\.userId/)
  assert.match(notifications, /if \(!sessionGuard\.isCurrent\(session, userStore\) \|\| requestId !== listRequestId\) return/)
  assert.match(notifications, /listRequestId \+= 1/)
  assert.match(notifications, /loading\.value = false/)
})

test('过期的标记已读和全部已读响应不会改写新会话状态', () => {
  assert.match(notifications, /async function markNotificationRead\(item\)\s*\{[\s\S]*const session = sessionGuard\.capture\(userStore\)/)
  assert.match(notifications, /await notificationApi\.markAsRead\(item\.id\)[\s\S]*if \(!sessionGuard\.isCurrent\(session, userStore\) \|\| !currentItem\) return/)
  assert.match(notifications, /async function handleMarkAllRead\(\)\s*\{[\s\S]*const session = sessionGuard\.capture\(userStore\)/)
  assert.match(notifications, /await notificationApi\.markAllRead\(\)[\s\S]*if \(!sessionGuard\.isCurrent\(session, userStore\)\) return/)
  assert.match(notifications, /catch \(error\) \{[\s\S]*if \(!sessionGuard\.isCurrent\(session, userStore\) \|\| !currentItem\) return/)
  assert.match(notifications, /catch \{[\s\S]*if \(!sessionGuard\.isCurrent\(session, userStore\)\) return[\s\S]*ElMessage\.error/)
})

test('过期会话或脱离当前列表的通知点击不会触发报告导航', () => {
  assert.match(notifications, /async function handleNotificationClick\(item\)\s*\{[\s\S]*const session = sessionGuard\.capture\(userStore\)/)
  assert.match(notifications, /const currentItem = notifications\.value\.find\(\(\{ id \}\) => id === item\.id\)/)
  assert.match(notifications, /if \(!sessionGuard\.isCurrent\(session, userStore\) \|\| !currentItem\) return/)
  assert.match(notifications, /await markNotificationRead\(currentItem, session\)[\s\S]*if \(!sessionGuard\.isCurrent\(session, userStore\) \|\| !notifications\.value\.includes\(currentItem\)\) return/)
  assert.match(notifications, /if \(currentItem\.type === REPORT_TYPE && currentItem\.ref_id\) await router\.push/)
})
