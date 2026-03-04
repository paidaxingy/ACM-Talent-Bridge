<template>
  <el-container style="min-height: 100vh">
    <el-aside width="240px" class="aside">
      <div class="brand">
        <div class="title">ACM Talent Bridge</div>
        <div class="subtitle">训练 · 对抗 · 评测 · 面试</div>
      </div>
      <el-menu :default-active="route.path" router>
        <el-menu-item index="/">我的主页</el-menu-item>
        <el-menu-item index="/contests">竞赛列表</el-menu-item>
        <el-menu-item index="/submissions">我的提交</el-menu-item>
        <el-menu-item index="/teams">我的队伍</el-menu-item>
        <el-menu-item index="/pk">PK 挑战</el-menu-item>
        <el-menu-item index="/external">赛历聚合</el-menu-item>

        <el-menu-item-group v-if="isAdmin">
          <template #title>管理后台</template>
          <el-menu-item index="/admin/users">用户管理</el-menu-item>
          <el-menu-item index="/admin/problems">题库管理</el-menu-item>
          <el-menu-item index="/admin/contests">竞赛管理</el-menu-item>
          <el-menu-item index="/admin/submissions">提交管理</el-menu-item>
          <el-menu-item index="/admin/pk">PK 对抗</el-menu-item>
          <el-menu-item index="/admin/ai">AI 面试</el-menu-item>
        </el-menu-item-group>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-tag type="info" effect="dark">API: {{ apiBase }}</el-tag>
        </div>
        <div class="header-right">
          <span class="user" v-if="user">
            <el-tag :type="user.role === 'admin' ? 'danger' : 'success'" size="small">
              {{ user.role === 'admin' ? '管理员' : '学生' }}
            </el-tag>
            <span class="username">{{ user.username }}</span>
          </span>
          <el-button v-if="user" size="small" @click="onLogout">退出登录</el-button>
        </div>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { apiBaseUrl } from '../api/client'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const apiBase = computed(() => apiBaseUrl())
const auth = useAuthStore()

const user = computed(() => auth.user)
const isAdmin = computed(() => auth.user?.role === 'admin')

function onLogout() {
  auth.logout()
  window.location.href = '/login'
}
</script>

<style scoped>
.aside {
  border-right: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
}
.brand {
  padding: 16px 16px 8px 16px;
}
.title {
  font-weight: 700;
  font-size: 16px;
}
.subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.header {
  border-bottom: 1px solid var(--el-border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(90deg, #0f172a, #020617);
  color: #e5e7eb;
}
.main {
  padding: 18px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.username {
  font-weight: 500;
}
</style>
