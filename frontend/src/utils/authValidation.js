import { nextTick } from 'vue'

const INPUT_SELECTOR = 'input, button, [tabindex]'

export const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为 3-50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
}

export function createRegisterRules(registerForm) {
  return {
    username: loginRules.username,
    password: loginRules.password,
    confirmPassword: [
      { required: true, message: '请再次输入密码', trigger: 'blur' },
      {
        validator: (_rule, value, callback) => {
          if (value !== registerForm.value.password) callback(new Error('两次输入的密码不一致'))
          else callback()
        },
        trigger: 'blur',
      },
    ],
  }
}

export function focusInput(inputRef) {
  const input = inputRef?.value
  if (typeof input?.focus === 'function') return input.focus()
  input?.input?.focus?.()
}

export function focusFirstInvalid(formRef) {
  nextTick(() => {
    const field = formRef.value?.fields?.find((item) => item.validateState === 'error')
    field?.$el?.querySelector(INPUT_SELECTOR)?.focus()
  })
}

export function focusLoginRecoveryField(loginForm, refs) {
  if (!loginForm.value.username) return focusInput(refs.usernameRef)
  if (!loginForm.value.password) return focusInput(refs.passwordRef)
  focusInput(refs.passwordRef)
}
