<template>
  <el-container style="min-height: 100vh" class="layout-container">
    <el-header class="top-nav">
      <div class="nav-content">
        <div class="brand">
          <div class="title">ACM Talent Bridge</div>
        </div>
        
        <el-menu :default-active="route.path" router mode="horizontal" class="nav-menu" :ellipsis="false">
          <el-menu-item index="/">我的主页</el-menu-item>
          <el-menu-item index="/contests">竞赛列表</el-menu-item>
          <el-menu-item index="/submissions">我的提交</el-menu-item>
          <el-menu-item index="/teams">我的队伍</el-menu-item>
          <el-menu-item index="/pk">PK 挑战</el-menu-item>
          <el-menu-item index="/external">赛历聚合</el-menu-item>
          <el-menu-item index="/ai/interview">AI 面试</el-menu-item>

          <el-sub-menu index="admin" v-if="isAdmin">
            <template #title>管理后台</template>
            <el-menu-item index="/admin/users">用户管理</el-menu-item>
            <el-menu-item index="/admin/problems">题库管理</el-menu-item>
            <el-menu-item index="/admin/contests">竞赛管理</el-menu-item>
            <el-menu-item index="/admin/submissions">提交管理</el-menu-item>
          </el-sub-menu>
        </el-menu>

        <div class="header-right">
          <span class="user" v-if="user">
            <el-tag :type="user.role === 'admin' ? 'danger' : 'success'" size="small" effect="light" round>
              {{ user.role === 'admin' ? '管理员' : '学生' }}
            </el-tag>
            <span class="username">{{ user.username }}</span>
          </span>
          <el-button v-if="user" size="small" type="primary" text bg round @click="onLogout">退出</el-button>
        </div>
      </div>
    </el-header>

    <el-main class="main-content">
      <router-view v-slot="{ Component, route }">
        <transition name="fade" mode="out-in" appear>
          <component :is="Component" :key="route.path" />
        </transition>
      </router-view>
    </el-main>
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
.layout-container {
  background: var(--el-bg-color-page);
}

.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 0;
  background: rgba(255, 255, 255, 0.75); /* 高透白底毛玻璃 */
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
}

.nav-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  padding: 0 20px;
}

.brand {
  display: flex;
  flex-direction: column;
  justify-content: center;
  margin-right: 40px;
}

.title {
  font-weight: 800;
  font-size: 19px;
  letter-spacing: 0.5px;
  background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-menu {
  flex: 1;
  border-bottom: none !important;
  background: transparent;
}

/* 调整菜单项高度和背景，适应 Header */
:deep(.el-menu--horizontal > .el-menu-item) {
  height: 60px;
  line-height: 60px;
  color: var(--el-text-color-regular) !important;
  font-weight: 500;
}
:deep(.el-menu--horizontal > .el-sub-menu .el-sub-menu__title) {
  height: 60px;
  line-height: 60px;
  color: var(--el-text-color-regular) !important;
  font-weight: 500;
}
:deep(.el-menu--horizontal > .el-menu-item:not(.is-disabled):hover) {
  background: rgba(129, 140, 248, 0.08) !important;
  color: var(--el-color-primary) !important;
}
:deep(.el-menu--horizontal > .el-sub-menu:not(.is-disabled):hover .el-sub-menu__title) {
  background: rgba(129, 140, 248, 0.08) !important;
  color: var(--el-color-primary) !important;
}
:deep(.el-menu--horizontal > .el-menu-item.is-active) {
  color: var(--el-color-primary) !important;
  border-bottom: 3px solid var(--el-color-primary) !important;
  background: transparent !important;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: 20px;
}

.user {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-primary);
}

.username {
  font-weight: 600;
  font-size: 14px;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 24px 20px;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1), transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}
</style>
