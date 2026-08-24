<template>
  <el-dialog
    v-model="visible"
    :title="activeTab === 'login' ? '登录' : '注册'"
    width="400px"
    :close-on-click-modal="false"
    @closed="handleClosed"
  >
    <el-tabs v-model="activeTab" class="login-tabs">
      <el-tab-pane label="登录" name="login">
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          label-width="70px"
          @keyup.enter="handleLogin"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              clearable
            />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              show-password
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              style="width: 100%"
              :loading="loginLoading"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="注册" name="register">
        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          label-width="80px"
          @keyup.enter="handleRegister"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="3-50 个字符"
              clearable
            />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="至少 6 位"
              show-password
            />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="再次输入密码"
              show-password
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              style="width: 100%"
              :loading="registerLoading"
              @click="handleRegister"
            >
              注册
            </el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'

const emit = defineEmits(['success'])

const userStore = useUserStore()

const visible = ref(false)
const activeTab = ref('login')
const loginLoading = ref(false)
const registerLoading = ref(false)

const loginFormRef = ref(null)
const registerFormRef = ref(null)

const loginForm = ref({
  username: '',
  password: '',
})

const registerForm = ref({
  username: '',
  password: '',
  confirmPassword: '',
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== registerForm.value.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为 3-50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为 3-50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

function open() {
  visible.value = true
}

function handleClosed() {
  loginForm.value = { username: '', password: '' }
  registerForm.value = { username: '', password: '', confirmPassword: '' }
  loginFormRef.value?.resetFields()
  registerFormRef.value?.resetFields()
}

async function handleLogin() {
  if (!loginFormRef.value) return
  try {
    await loginFormRef.value.validate()
  } catch (e) {
    return
  }

  loginLoading.value = true
  try {
    await userStore.login(loginForm.value.username, loginForm.value.password)
    ElMessage.success('登录成功')
    visible.value = false
    emit('success')
  } catch (e) {
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
    return
  }

  registerLoading.value = true
  try {
    await userStore.register(registerForm.value.username, registerForm.value.password)
    ElMessage.success('注册成功，请登录')
    // 切换到登录 tab，并填充用户名
    activeTab.value = 'login'
    loginForm.value.username = registerForm.value.username
  } catch (e) {
    const msg = e.response?.data?.detail || '注册失败，请稍后重试'
    ElMessage.error(msg)
  } finally {
    registerLoading.value = false
  }
}

function handleShowLogin() {
  activeTab.value = 'login'
  open()
}

onMounted(() => {
  window.addEventListener('show-login', handleShowLogin)
})

onUnmounted(() => {
  window.removeEventListener('show-login', handleShowLogin)
})

defineExpose({ open })
</script>

<style scoped>
.login-tabs {
  margin-top: 8px;
}
</style>
