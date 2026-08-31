/**
 * 认证相关 API
 */
import http from './http'

export const authApi = {
  // 注册
  register(username, password) {
    return http.post('/auth/register', { username, password })
  },
  // 登录
  login(username, password) {
    return http.post('/auth/login', { username, password })
  },
  // 获取当前用户
  getMe() {
    return http.get('/auth/me', { skipAuthRedirect: true })
  },
}
