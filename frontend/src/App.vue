<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import Layout from './components/Layout.vue'
import LoginModal from './components/LoginModal.vue'
import { useUserStore } from './store/user'

const loginModalRef = ref(null)
const userStore = useUserStore()

// 应用启动时尝试恢复用户信息
onMounted(() => {
  if (userStore.token && !userStore.userInfo) {
    userStore.fetchUserInfo()
  }
})

onUnmounted(() => {})
</script>

<template>
  <Layout />
  <LoginModal ref="loginModalRef" />
</template>

<style scoped>
</style>
