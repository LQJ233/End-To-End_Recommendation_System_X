<template>
  <el-container class="app-root">
    <el-header height="56px" class="app-header">
      <div class="brand" @click="$router.push('/')">单机版电商推荐</div>
      <div class="spacer" />
      <div class="actions">
        <el-button v-if="!user.isLogin" text @click="$router.push('/login')">登录</el-button>
        <el-button v-if="!user.isLogin" type="primary" text @click="$router.push('/register')">注册</el-button>
        <el-dropdown v-else>
          <span class="user-chip">{{ user.profile?.nickname || user.profile?.username || user.userId }}</span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-if="isAdmin" @click="$router.push('/admin/users')">用户管理</el-dropdown-item>
              <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useUserStore } from './stores/user'
import { useRouter } from 'vue-router'

const user = useUserStore()
const router = useRouter()

const isAdmin = computed(() => (user.profile?.roles || []).includes('ADMIN'))

onMounted(() => {
  user.bootstrap()
})

async function logout () {
  await user.logout()
  router.push('/login')
}
</script>

<style>
.app-root { min-height: 100vh; background: #f5f6f8; }
.app-header { display: flex; align-items: center; background: #fff; box-shadow: 0 1px 2px rgba(0,0,0,0.04); padding: 0 24px; }
.brand { font-weight: 600; font-size: 18px; cursor: pointer; }
.spacer { flex: 1; }
.actions { display: flex; gap: 8px; align-items: center; }
.user-chip { cursor: pointer; color: #303133; }
.app-main { padding: 16px; }
</style>
