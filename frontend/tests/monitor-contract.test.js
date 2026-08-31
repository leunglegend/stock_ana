import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

async function read(relativePath) {
  return readFile(new URL(relativePath, import.meta.url), 'utf8')
}

const [routerSource, layoutSource, apiSource] = await Promise.all([
  read('../src/router/index.js'),
  read('../src/components/Layout.vue'),
  read('../src/api/monitor.js'),
])

test('注册需登录的盘中监控路由', () => {
  assert.match(routerSource, /path:\s*['"]\/monitor['"]/) 
  const route = routerSource.match(/path:\s*['"]\/monitor['"][\s\S]*?\n\s*\},?/m)?.[0] || ''
  assert.match(route, /component:\s*\(\)\s*=>\s*import\(['"]\.\.\/views\/Monitor\.vue['"]\)/)
  assert.match(route, /title:\s*['"]盘中监控['"]/)
  assert.match(route, /requiresAuth:\s*true/)
})

test('桌面和移动菜单提供盘中监控一级入口', () => {
  assert.match(layoutSource, /path:\s*['"]\/monitor['"][\s\S]*?title:\s*['"]盘中监控['"]/)
  assert.match(layoutSource, /compactTitle:\s*['"]监控['"]/) 
  assert.match(layoutSource, /return ['"]monitor['"]/)
})

test('监控 API 指向聚合总览接口', () => {
  assert.match(apiSource, /getMonitorOverview/)
  assert.match(apiSource, /http\.get\(['"]\/monitor\/overview['"]/) 
})
