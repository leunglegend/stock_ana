<template>
  <el-dialog v-model="visible" class="auth-dialog" :title="activeTab === 'login' ? '登录' : '注册'" width="min(760px, calc(100vw - 32px))" :close-on-click-modal="false" @closed="handleClosed">
    <div class="auth-dialog__shell">
      <aside class="auth-dialog__signal">
        <div class="auth-brand"><span class="auth-brand__mark">研</span><span>股票研究台</span></div>
        <div class="auth-signal__content">
          <p class="auth-signal__eyebrow">MARKET INTELLIGENCE DESK</p>
          <h2>把每一次登录，变成研究开始</h2>
          <p class="auth-signal__summary">聚合行情、研报与 AI 洞察，继续你的市场研究。</p>
          <div class="auth-signal__tags" aria-label="研究能力"><span>指数</span><span>板块</span><span>个股</span><span>AI 观察</span></div>
        </div>
        <p class="auth-signal__disclaimer">数据仅供研究参考，不构成任何投资建议。</p>
      </aside>
      <section class="auth-dialog__panel">
        <div class="auth-panel__heading"><h1>{{ activeTab === 'login' ? '继续你的市场研究' : '创建研究账户' }}</h1><p>{{ activeTab === 'login' ? '登录后查看你的自选、报告与洞察' : '注册后即可保存自选与研究偏好' }}</p></div>
        <el-tabs v-model="activeTab" class="auth-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form ref="loginFormRef" class="auth-form" :model="loginForm" :rules="loginRules" label-position="top" @keyup.enter="handleLogin">
              <el-form-item label="用户名" prop="username"><el-input ref="loginUsernameRef" v-model="loginForm.username" placeholder="请输入用户名" clearable /></el-form-item>
              <el-form-item label="密码" prop="password"><el-input ref="loginPasswordRef" v-model="loginForm.password" type="password" placeholder="请输入密码" show-password /></el-form-item>
              <el-form-item class="auth-form__action"><el-button type="primary" class="auth-submit" :loading="loginLoading" @click="handleLogin">进入研究工作台</el-button></el-form-item>
            </el-form>
          </el-tab-pane>
          <el-tab-pane label="注册" name="register">
            <el-form ref="registerFormRef" class="auth-form" :model="registerForm" :rules="registerRules" label-position="top" @keyup.enter="handleRegister">
              <el-form-item label="用户名" prop="username"><el-input ref="registerUsernameRef" v-model="registerForm.username" placeholder="3-50 个字符" clearable /></el-form-item>
              <el-form-item label="密码" prop="password"><el-input v-model="registerForm.password" type="password" placeholder="至少 6 位" show-password /></el-form-item>
              <el-form-item label="确认密码" prop="confirmPassword"><el-input v-model="registerForm.confirmPassword" type="password" placeholder="再次输入密码" show-password /></el-form-item>
              <p class="auth-form__note">注册后即可同步保存你的自选与研究报告。</p>
              <el-form-item class="auth-form__action"><el-button type="primary" class="auth-submit" :loading="registerLoading" @click="handleRegister">创建研究账户</el-button></el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </section>
    </div>
  </el-dialog>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { useUserStore } from '@/store/user'
import { createRegisterRules, focusFirstInvalid, focusInput, focusLoginRecoveryField, loginRules } from '@/utils/authValidation'

const emit = defineEmits(['success'])

const LOGIN_PROMPT_RESET_EVENT = 'auth-login-prompt-reset'

const router = useRouter()
const userStore = useUserStore()

const visible = ref(false)
const activeTab = ref('login')
const loginLoading = ref(false)
const registerLoading = ref(false)

const loginFormRef = ref(null)
const registerFormRef = ref(null)
const loginUsernameRef = ref(null)
const loginPasswordRef = ref(null)
const registerUsernameRef = ref(null)
const lastActiveElement = ref(null)

const loginForm = ref({
  username: '',
  password: '',
})

const registerForm = ref({
  username: '',
  password: '',
  confirmPassword: '',
})

const registerRules = createRegisterRules(registerForm)

function resetLoginPromptState() {
  window.dispatchEvent(new CustomEvent(LOGIN_PROMPT_RESET_EVENT))
}

function open() {
  if (!visible.value) {
    const activeElement = document.activeElement
    lastActiveElement.value = activeElement instanceof HTMLElement ? activeElement : null
  }

  visible.value = true
  nextTick(() => {
    focusInput(loginUsernameRef)
  })
}

function handleClosed() {
  loginForm.value = { username: '', password: '' }
  registerForm.value = { username: '', password: '', confirmPassword: '' }
  loginFormRef.value?.resetFields()
  registerFormRef.value?.resetFields()
  userStore.clearPendingRoute()
  lastActiveElement.value?.focus?.()
  lastActiveElement.value = null
  resetLoginPromptState()
}

async function handleLogin() {
  if (!loginFormRef.value) return
  try {
    await loginFormRef.value.validate()
  } catch (e) {
    focusFirstInvalid(loginFormRef)
    return
  }

  loginLoading.value = true
  try {
    await userStore.login(loginForm.value.username, loginForm.value.password)
    const targetPath = userStore.consumePendingRoute()
    ElMessage.success('登录成功')
    visible.value = false
    emit('success', { targetPath })

    if (targetPath && targetPath !== router.currentRoute.value.fullPath) {
      await router.push(targetPath)
    }
  } catch (e) {
    focusLoginRecoveryField(loginForm, { usernameRef: loginUsernameRef, passwordRef: loginPasswordRef })
    const msg = e.response?.data?.detail || '登录失败，请检查用户名和密码'
    ElMessage.error(msg)
  } finally {
    loginLoading.value = false
  }
}

async function handleRegister() {
  if (!registerFormRef.value) return
  try {
    await registerFormRef.value.validate()
  } catch (e) {
    focusFirstInvalid(registerFormRef)
    return
  }

  registerLoading.value = true
  try {
    await userStore.register(registerForm.value.username, registerForm.value.password)
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    loginForm.value.username = registerForm.value.username
    nextTick(() => {
      focusInput(loginUsernameRef)
    })
  } catch (e) {
    focusInput(registerUsernameRef)
    const msg = e.response?.data?.detail || '注册失败，请稍后重试'
    ElMessage.error(msg)
  } finally {
    registerLoading.value = false
  }
}

function handleShowLogin(event) {
  const targetPath = event.detail?.targetPath

  if (targetPath) {
    userStore.setPendingRoute(targetPath)
  }

  activeTab.value = 'login'
  open()
}

onMounted(() => {
  window.addEventListener('show-login', handleShowLogin)

  if (userStore.pendingRoute) {
    activeTab.value = 'login'
    open()
  }
})

onUnmounted(() => {
  window.removeEventListener('show-login', handleShowLogin)
})

defineExpose({ open })
</script>

<style scoped>
.auth-dialog.el-dialog { padding: 0; overflow: hidden; border-radius: 14px; }
:global(.auth-dialog .el-dialog__header) { display: block; height: 0; padding: 0; margin: 0; overflow: visible; }
:global(.auth-dialog .el-dialog__title) { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
:global(.auth-dialog .el-dialog__headerbtn) { z-index: 2; top: 12px; right: 14px; color: var(--text-secondary, #8290a3); }
:global(.auth-dialog .el-dialog__body) { padding: 0; }
.auth-dialog__shell { display: grid; grid-template-columns: 44% 56%; min-height: 430px; }
.auth-dialog__signal { display: flex; flex-direction: column; justify-content: space-between; padding: 34px 30px 24px; color: var(--color-primary-100, #d5e5ef); background: var(--surface-sidebar, #172839); }
.auth-brand { display: flex; align-items: center; gap: 10px; color: #fff; font-size: 15px; font-weight: 600; letter-spacing: .08em; }
.auth-brand__mark { display: grid; place-items: center; width: 34px; height: 34px; border: 1px solid var(--color-warning-500, #a66c13); border-radius: 10px; color: var(--color-warning-500, #a66c13); font-size: 18px; }
.auth-signal__content { margin: auto 0; }
.auth-signal__eyebrow { margin-bottom: 18px; color: var(--color-warning-500, #a66c13); font-size: 10px; letter-spacing: .16em; }
.auth-signal__content h2 { max-width: 240px; margin: 0 0 14px; color: #fff; font-size: 28px; line-height: 1.3; font-weight: 600; }
.auth-signal__summary { max-width: 245px; color: #a8c3df; font-size: 13px; line-height: 1.7; }
.auth-signal__tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 22px; }
.auth-signal__tags span { padding: 5px 9px; border: 1px solid var(--color-primary-400, #5790b1); border-radius: 999px; color: var(--color-primary-100, #d5e5ef); font-size: 11px; }
.auth-signal__disclaimer { color: #7f9bb8; font-size: 10px; line-height: 1.5; }
.auth-dialog__panel { padding: 36px 40px 28px; background: var(--surface-primary, #fff); }
.auth-panel__heading h1 { margin: 0; color: #15243a; font-size: 24px; font-weight: 600; }
.auth-panel__heading p { margin: 8px 0 24px; color: #8290a3; font-size: 13px; }
.auth-tabs :deep(.el-tabs__header) { margin-bottom: 24px; }
.auth-tabs :deep(.el-tabs__nav-wrap::after) { height: 1px; background-color: #e9eef5; }
.auth-tabs :deep(.el-tabs__active-bar) { height: 2px; background-color: #246b9f; }
.auth-tabs :deep(.el-tabs__item) { height: 38px; padding: 0 18px; color: #8b98aa; font-size: 14px; }
.auth-tabs :deep(.el-tabs__item.is-active) { color: #1f5f8f; font-weight: 600; }
.auth-form :deep(.el-form-item) { margin-bottom: 18px; }
.auth-form :deep(.el-form-item__label) { padding-bottom: 7px; color: #46566c; font-size: 12px; line-height: 1.2; }
.auth-form :deep(.el-input__wrapper) { min-height: 44px; border: 1px solid #dfe6ef; border-radius: 8px; box-shadow: none; transition: border-color .2s, box-shadow .2s; }
.auth-form :deep(.el-input__wrapper:hover) { border-color: #9ab6ce; }
.auth-form :deep(.el-input__wrapper.is-focus) { border-color: #3f83b3; box-shadow: 0 0 0 3px rgba(63,131,179,.13); }
.auth-form :deep(.el-form-item.is-error .el-input__wrapper) { border-color: #e07171; box-shadow: 0 0 0 3px rgba(224,113,113,.1); }
.auth-form :deep(.el-input__inner) { color: #26364c; }
.auth-form__action { margin-top: 26px; }
.auth-submit { width: 100%; min-height: 44px; border: 0; border-radius: 8px; background: var(--color-primary-500, #2b6e99); font-size: 14px; font-weight: 600; }
.auth-submit:hover { background: var(--color-primary-600, #225c82); }
.auth-form__note { margin: -4px 0 0; color: #98a4b4; font-size: 11px; line-height: 1.5; }
.auth-dialog :deep(button:focus-visible), .auth-dialog :deep(input:focus-visible) { outline: 3px solid rgba(63,131,179,.45); outline-offset: 2px; }
@media (max-width: 640px) { .auth-dialog__shell { display: block; min-height: 0; } .auth-dialog__signal { min-height: 176px; padding: 24px 22px 20px; } .auth-signal__content { margin: 22px 0 0; } .auth-signal__eyebrow, .auth-signal__summary, .auth-signal__tags, .auth-signal__disclaimer { display: none; } .auth-signal__content h2 { max-width: none; margin: 0; font-size: 22px; } .auth-dialog__panel { padding: 28px 22px 24px; } }
@media (prefers-reduced-motion: reduce) { .auth-dialog, .auth-dialog *, .auth-dialog :deep(*) { transition: none !important; animation: none !important; scroll-behavior: auto !important; } }
</style>
