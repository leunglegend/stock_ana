<template>
  <div class="command-utilities">
    <div class="command-utilities__theme">
      <el-tooltip content="切换界面主题" placement="bottom">
        <el-dropdown trigger="click" @command="selectTheme">
          <button class="command-utilities__icon-button" type="button" aria-label="切换界面主题">
            <el-icon><Brush /></el-icon>
          </button>

          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="theme in THEMES"
                :key="theme.key"
                :command="theme.key"
                :class="{ 'is-current': currentTheme === theme.key }"
              >
                <span class="theme-option">
                  <span class="theme-option__swatches" aria-hidden="true">
                    <i v-for="color in theme.colors" :key="color" class="theme-swatch" :style="{ backgroundColor: color }"></i>
                  </span>
                  <span>{{ theme.name }}</span>
                  <el-icon v-if="currentTheme === theme.key"><Check /></el-icon>
                </span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-tooltip>
    </div>

    <el-button v-if="!userStore.isLoggedIn" type="primary" class="command-utilities__account command-utilities__login" @click="openLogin">
      登录
    </el-button>

    <el-dropdown v-else class="command-utilities__account" trigger="click" @command="handleCommand">
      <button class="command-utilities__user" type="button" aria-label="用户菜单">
        <span class="command-utilities__avatar">{{ userInitial }}</span>
        <span class="command-utilities__user-meta">
          <span>{{ userStore.username }}</span>
          <small>SQLite 账户</small>
        </span>
        <el-icon><ArrowDown /></el-icon>
      </button>

      <template #dropdown>
        <el-dropdown-menu><el-dropdown-item command="logout">退出登录</el-dropdown-item></el-dropdown-menu>
      </template>
    </el-dropdown>

    <el-dropdown class="command-utilities__more" trigger="click" @command="handleMoreCommand">
      <button class="command-utilities__icon-button" type="button" aria-label="更多操作">
        <el-icon><MoreFilled /></el-icon>
      </button>

      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item v-if="!userStore.isLoggedIn" command="login">登录</el-dropdown-item>
          <el-dropdown-item v-else disabled>{{ userStore.username }}</el-dropdown-item>
          <el-dropdown-item v-if="userStore.isLoggedIn" divided command="logout">退出登录</el-dropdown-item>
          <el-dropdown-item divided v-for="theme in THEMES" :key="`mobile-theme-${theme.key}`" :command="`theme:${theme.key}`">
            <span class="theme-option">
              <span class="theme-option__swatches" aria-hidden="true">
                <i v-for="color in theme.colors" :key="color" class="theme-swatch" :style="{ backgroundColor: color }"></i>
              </span>
              <span>{{ theme.name }}</span>
              <el-icon v-if="currentTheme === theme.key"><Check /></el-icon>
            </span>
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { ElMessageBox } from 'element-plus/es/components/message-box/index.mjs'
import { ArrowDown, Brush, Check, MoreFilled } from '@element-plus/icons-vue'

import { useUserStore } from '@/store/user'
import { applyTheme, DEFAULT_THEME, THEMES } from '@/theme'

const userStore = useUserStore()
const currentTheme = ref(document.documentElement.dataset.theme || DEFAULT_THEME)
const userInitial = computed(() => userStore.username?.slice(0, 1)?.toUpperCase() || 'U')

function openLogin() {
  window.dispatchEvent(new CustomEvent('show-login'))
}

function selectTheme(theme) {
  currentTheme.value = applyTheme(theme)
}

async function handleCommand(command) {
  if (command !== 'logout') return
  try {
    await ElMessageBox.confirm('确定退出当前账号吗？', '退出登录', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
    userStore.logout()
    ElMessage.success('已退出登录')
  } catch {}
}

function handleMoreCommand(command) {
  if (command === 'login') return openLogin()
  if (command.startsWith('theme:')) return selectTheme(command.slice(6))
  return handleCommand(command)
}
</script>

<style scoped>
.command-utilities {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.command-utilities__theme { display: inline-flex; }

.command-utilities__icon-button {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  padding: 0;
  border: 0;
  border-radius: var(--radius-xs);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}

.command-utilities__icon-button:hover {
  background: var(--surface-panel-muted);
  color: var(--text-primary);
}

.theme-option {
  display: grid;
  grid-template-columns: 54px minmax(120px, 1fr) 18px;
  align-items: center;
  gap: var(--spacing-3);
  width: 100%;
}

.theme-option .el-icon { justify-self: end; }

.theme-option__swatches {
  display: flex;
  overflow: hidden;
  height: 18px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xs);
}

.theme-swatch { flex: 1; }

.command-utilities__login {
  min-height: 32px;
  padding-inline: var(--spacing-3);
}

.command-utilities__user {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-3);
  min-width: 0;
  min-height: 32px;
  padding: 0 var(--spacing-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xs);
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
}

.command-utilities__avatar {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border-radius: var(--radius-full);
  background: var(--surface-panel-strong);
  font-size: var(--font-size-sm);
  font-weight: 700;
}

.command-utilities__user-meta {
  display: grid;
  min-width: 0;
  text-align: left;
  font-size: var(--font-size-sm);
  font-weight: 600;
}

.command-utilities__user-meta small {
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
  font-weight: 400;
}

.command-utilities__more { display: none; }

@media (max-width: 767px) {
  .command-utilities__theme { display: none; }

  .command-utilities__account { display: none; }

  .command-utilities__more { display: inline-flex; }

  .command-utilities__icon-button {
    width: 44px;
    height: 44px;
  }
}
</style>
