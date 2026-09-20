<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { loginOrRegister } from '../services/api'
import { trackLogin } from '../services/tracking'

const router = useRouter()
const form = reactive({
  username: '',
  password: '',
})
const loggingIn = ref(false)

async function submit() {
  if (!form.username) {
    return
  }

  loggingIn.value = true
  let user = {
    userId: `local_user_${form.username}`,
    username: form.username,
    token: '',
  }
  try {
    user = await loginOrRegister(form.username, form.password || 'password123')
  } catch {
    // 后端不可用时保留本地体验
  } finally {
    loggingIn.value = false
  }

  localStorage.setItem('mock_user_id', String(user.userId ?? `local_user_${form.username}`))
  localStorage.setItem('user_token', user.token || '')
  localStorage.setItem('mock_session_id', `session-${Date.now()}`)
  trackLogin()
  router.push('/')
}
</script>

<template>
  <div class="login-page">
    <el-card class="login-card">
      <template #header>
        <div class="card-title">电商广告推荐系统登录</div>
      </template>
      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-button type="primary" class="login-button" :loading="loggingIn" @click="submit">登录</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eef2ff, #f8fafc);
}

.login-card {
  width: 380px;
}

.card-title {
  font-weight: 700;
}

.login-button {
  width: 100%;
}
</style>
