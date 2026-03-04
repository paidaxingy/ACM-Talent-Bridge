<template>
  <el-card>
    <template #header>
      <div style="display:flex; align-items:center; justify-content:space-between">
        <div>用户管理</div>
        <div>
          <el-select v-model="filterRole" placeholder="角色" clearable style="width: 140px; margin-right: 8px" size="small">
            <el-option label="管理员" value="admin" />
            <el-option label="学生" value="student" />
          </el-select>
          <el-select v-model="filterActive" placeholder="状态" clearable style="width: 140px; margin-right: 8px" size="small">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
          <el-button size="small" @click="load">刷新</el-button>
        </div>
      </div>
    </template>

    <el-table :data="users" size="small" style="width:100%">
      <el-table-column prop="user_id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="role" label="角色" width="110">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'success'" size="small">
            {{ row.role === 'admin' ? '管理员' : '学生' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="200">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="360">
        <template #default="{ row }">
          <el-button size="small" type="primary" plain @click="setRole(row, 'admin')" :disabled="row.role === 'admin'">设为管理员</el-button>
          <el-button size="small" plain @click="setRole(row, 'student')" :disabled="row.role === 'student'">设为学生</el-button>
          <el-button size="small" type="warning" plain @click="toggleActive(row)">
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
          <el-button
            size="small"
            type="success"
            plain
            :loading="regenLoading[row.user_id] === true"
            @click="regenerateProfile(row)"
          >
            重算画像
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import dayjs from 'dayjs'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api/client'

interface User {
  user_id: number
  username: string
  role: 'admin' | 'student'
  is_active: boolean
  created_at: string
}

const users = ref<User[]>([])
const filterRole = ref<string | null>(null)
const filterActive = ref<boolean | null>(null)
const regenLoading = ref<Record<number, boolean>>({})
const memberIdMap = ref<Record<string, number>>({})

function formatTime(t: string) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : ''
}

async function load() {
  const params: Record<string, any> = {}
  if (filterRole.value) params.role = filterRole.value
  if (filterActive.value !== null) params.is_active = filterActive.value
  try {
    const [usersRes, membersRes] = await Promise.all([
      api.get<User[]>('/users', { params }),
      // /members 的 limit 最大 200，这里取一个足够大的上限
      api.get<any[]>('/members', { params: { limit: 200 } }),
    ])
    users.value = usersRes.data
    const map: Record<string, number> = {}
    for (const m of membersRes.data) {
      if (m && typeof m.handle === 'string' && typeof m.id === 'number') {
        map[m.handle] = m.id
      }
    }
    memberIdMap.value = map
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载用户/成员信息失败')
  }
}

async function setRole(row: User, role: 'admin' | 'student') {
  if (row.role === role) return
  try {
    await ElMessageBox.confirm(`确认将 ${row.username} 设置为 ${role === 'admin' ? '管理员' : '学生'} 吗？`, '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await api.patch(`/users/${row.user_id}`, { role })
  ElMessage.success('更新成功')
  await load()
}

async function toggleActive(row: User) {
  const next = !row.is_active
  try {
    await ElMessageBox.confirm(`确认将 ${row.username} ${next ? '启用' : '禁用'} 吗？`, '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await api.patch(`/users/${row.user_id}`, { is_active: next })
  ElMessage.success('更新成功')
  await load()
}

async function regenerateProfile(row: User) {
  const memberId = memberIdMap.value[row.username]
  if (!memberId) {
    ElMessage.error('未找到同名成员（handle 与用户名不匹配）')
    return
  }
  regenLoading.value[row.user_id] = true
  try {
    await ElMessageBox.confirm(
      `将使用 DeepSeek 为 ${row.username} 重新生成能力画像，覆盖当前 AI 缓存。确定继续吗？`,
      '重算能力画像',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消',
      },
    )
  } catch {
    regenLoading.value[row.user_id] = false
    return
  }

  try {
    await api.post(`/members/${memberId}/profile/ai/regenerate`)
    ElMessage.success('已触发 AI 画像重算')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '重算失败')
  } finally {
    regenLoading.value[row.user_id] = false
  }
}

load()
</script>
