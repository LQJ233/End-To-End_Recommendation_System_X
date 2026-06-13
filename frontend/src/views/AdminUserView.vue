<template>
  <div class="admin-users">
    <el-card>
      <div class="toolbar">
        <el-input v-model="query.keyword" placeholder="用户名/昵称/手机号" clearable style="width:240px" />
        <el-select v-model="query.status" placeholder="状态" clearable style="width:120px">
          <el-option label="正常" :value="1" />
          <el-option label="禁用" :value="0" />
        </el-select>
        <el-select v-model="query.roleCode" placeholder="角色" clearable style="width:120px">
          <el-option label="USER" value="USER" />
          <el-option label="ADMIN" value="ADMIN" />
        </el-select>
        <el-button type="primary" @click="load">查询</el-button>
      </div>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="userId" label="userId" width="160" />
        <el-table-column prop="username" label="username" width="140" />
        <el-table-column prop="nickname" label="nickname" />
        <el-table-column prop="phone" label="phone" width="140" />
        <el-table-column label="角色" width="160">
          <template #default="{ row }">{{ row.roles?.join(', ') }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '正常' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button size="small" @click="toggleStatus(row)">{{ row.status === 1 ? '禁用' : '启用' }}</el-button>
            <el-button size="small" @click="resetPassword(row)">重置密码</el-button>
            <el-button size="small" @click="setRoles(row)">编辑角色</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination
          v-model:current-page="query.page"
          :page-size="query.size"
          :total="total"
          @current-change="load"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminListUsers, adminResetPassword, adminSetRoles, adminSetStatus } from '../api/auth'

const query = reactive({ keyword: '', status: null, roleCode: '', page: 1, size: 20 })
const list = ref([])
const total = ref(0)
const loading = ref(false)

async function load () {
  loading.value = true
  try {
    const r = await adminListUsers(query)
    if (r.code === 0) {
      list.value = r.data.records || []
      total.value = r.data.total || 0
    }
  } finally {
    loading.value = false
  }
}

async function toggleStatus (row) {
  await adminSetStatus(row.userId, row.status === 1 ? 0 : 1)
  ElMessage.success('已更新')
  load()
}

async function resetPassword (row) {
  try {
    const { value } = await ElMessageBox.prompt('请输入新密码', '重置密码', { inputType: 'password' })
    if (value) {
      await adminResetPassword(row.userId, value)
      ElMessage.success('已重置')
    }
  } catch {}
}

async function setRoles (row) {
  try {
    const { value } = await ElMessageBox.prompt('多角色逗号分隔，可选 USER / ADMIN', '编辑角色', {
      inputValue: (row.roles || ['USER']).join(',')
    })
    if (value) {
      const roles = value.split(',').map((s) => s.trim()).filter(Boolean)
      await adminSetRoles(row.userId, roles)
      ElMessage.success('已更新')
      load()
    }
  } catch {}
}

onMounted(load)
</script>

<style scoped>
.admin-users { max-width: 1200px; margin: 0 auto; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
.pager { display: flex; justify-content: flex-end; margin-top: 12px; }
</style>
