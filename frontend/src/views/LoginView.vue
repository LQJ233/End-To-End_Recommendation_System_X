<template>
  <div class="auth-wrap">
    <el-card class="auth-card">
      <h2>登录</h2>
      <el-form :model="form" label-width="80px" @submit.prevent>
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onLogin">登录</el-button>
          <el-button @click="$router.push('/register')">注册</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const router = useRouter()
const user = useUserStore()

async function onLogin () {
  if (!form.username || !form.password) {
    ElMessage.warning('请填写完整')
    return
  }
  loading.value = true
  try {
    await user.login(form)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    // axios reject 的可能是后端业务 body (含 code/message) 或 Error
    const msg = e?.message || e?.toString?.() || '登录失败'
    if (e?.code === 423001) ElMessage.error('账号已锁定，请稍后再试')
    else if (e?.code === 429001) ElMessage.error('登录次数过多，请稍后再试')
    else ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-wrap { display: flex; justify-content: center; padding-top: 48px; }
.auth-card { width: 420px; }
</style>
