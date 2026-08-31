import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

const viteSource = await readFile(new URL('../vite.config.js', import.meta.url), 'utf8')
const readmeSource = await readFile(new URL('../../README.md', import.meta.url), 'utf8')

test('前端开发服务器使用 5173 并代理到同源服务端口 52764', () => {
  assert.match(viteSource, /port:\s*5173/)
  assert.match(viteSource, /strictPort:\s*true/)
  assert.match(viteSource, /target:\s*['"]http:\/\/localhost:52764['"]/)
})

test('README 使用统一应用端口并说明开发端口', () => {
  assert.match(readmeSource, /http:\/\/localhost:52764/)
  assert.match(readmeSource, /http:\/\/localhost:5173/)
})
