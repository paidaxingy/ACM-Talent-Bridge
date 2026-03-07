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
          </el-sub-menu>
        </el-menu>

        <div class="header-right">
          <el-select
            v-if="memberOptions.length"
            v-model="selectedMemberId"
            class="member-search"
            size="small"
            filterable
            clearable
            :filter-method="filterMembers"
            placeholder="搜索成员主页"
            @change="goMemberProfile"
          >
            <el-option
              v-for="m in memberOptions"
              :key="m.id"
              :label="`${m.handle}（Rating ${m.rating}）`"
              :value="m.id"
            />
          </el-select>

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
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, apiBaseUrl } from '../api/client'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const apiBase = computed(() => apiBaseUrl())
const auth = useAuthStore()

const user = computed(() => auth.user)
const isAdmin = computed(() => auth.user?.role === 'admin')

interface MemberOption {
  id: number
  handle: string
  rating: number
}

const allMembers = ref<MemberOption[]>([])
const memberOptions = ref<MemberOption[]>([])
const selectedMemberId = ref<number | null>(null)

async function loadMembers() {
  try {
    const { data } = await api.get<any[]>('/members', { params: { limit: 200 } })
    const mapped: MemberOption[] = (data || [])
      .filter((m: any) => m && typeof m.id === 'number' && typeof m.handle === 'string')
      .map((m: any) => ({
        id: m.id,
        handle: m.handle,
        rating: m.rating ?? 0,
      }))
    allMembers.value = mapped
    memberOptions.value = mapped
  } catch (e) {
    // 静默失败：搜索功能不可用但不影响主流程
    console.error('加载成员列表失败', e)
  }
}

function filterMembers(query: string) {
  if (!query) {
    memberOptions.value = allMembers.value
    return
  }
  const q = query.toLowerCase()
  memberOptions.value = allMembers.value.filter(
    (m) => m.handle.toLowerCase().includes(q) || String(m.rating).includes(q),
  )
}

function goMemberProfile(memberId: number | null) {
  if (!memberId) return
  router.push(`/profile/${memberId}`)
}

onMounted(() => {
  loadMembers()
})

function onLogout() {
  auth.logout()
  window.location.href = '/login'
}
</script>

<style scoped>
.layout-container {
  position: relative;
  background: transparent;
}

.layout-container::before,
.layout-container::after {
  content: '';
  position: fixed;
  inset: auto;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  pointer-events: none;
  filter: blur(10px);
  z-index: 0;
}

.layout-container::before {
  top: -140px;
  left: -120px;
  background: radial-gradient(circle, rgba(181, 210, 225, 0.26) 0%, rgba(181, 210, 225, 0) 70%);
}

.layout-container::after {
  right: -110px;
  top: 180px;
  background: radial-gradient(circle, rgba(216, 226, 198, 0.24) 0%, rgba(216, 226, 198, 0) 70%);
}

.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 0;
  background: rgba(250, 250, 248, 0.68);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 12px 36px -32px rgba(86, 103, 130, 0.52);
  border-bottom: 1px solid rgba(220, 227, 233, 0.7);
}

.nav-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  min-height: 72px;
  padding: 0 20px;
}

.brand {
  display: flex;
  flex-direction: column;
  justify-content: center;
  margin-right: 24px;
  padding: 10px 14px 10px 0;
}

.title {
  font-weight: 800;
  font-size: 20px;
  letter-spacing: 0.6px;
  white-space: nowrap;
  background: linear-gradient(135deg, #6178cb 0%, #79a6b1 52%, #7dbda3 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 10px 24px rgba(111, 134, 214, 0.16);
}

.nav-menu {
  flex: 1;
  border-bottom: none !important;
  background: transparent;
}

:deep(.el-menu--horizontal > .el-menu-item) {
  height: 72px;
  line-height: 72px;
  color: var(--el-text-color-regular) !important;
  font-weight: 500;
  border-radius: 14px 14px 0 0;
  margin: 0 2px;
}

:deep(.el-menu--horizontal > .el-sub-menu .el-sub-menu__title) {
  height: 72px;
  line-height: 72px;
  color: var(--el-text-color-regular) !important;
  font-weight: 500;
  border-radius: 14px 14px 0 0;
}

:deep(.el-menu--horizontal > .el-menu-item:not(.is-disabled):hover) {
  background: rgba(111, 134, 214, 0.08) !important;
  color: var(--el-color-primary) !important;
}

:deep(.el-menu--horizontal > .el-sub-menu:not(.is-disabled):hover .el-sub-menu__title) {
  background: rgba(111, 134, 214, 0.08) !important;
  color: var(--el-color-primary) !important;
}

:deep(.el-menu--horizontal > .el-menu-item.is-active) {
  color: var(--el-color-primary) !important;
  border-bottom: 3px solid var(--el-color-primary) !important;
  background: linear-gradient(180deg, rgba(111, 134, 214, 0.08), rgba(111, 134, 214, 0.01)) !important;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: 20px;
  padding: 8px 0;
}

.member-search {
  width: 220px;
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
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 28px 20px 36px;
}

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

@media (max-width: 960px) {
  .nav-content {
    flex-wrap: wrap;
    align-items: stretch;
    padding: 10px 16px 12px;
  }

  .brand {
    width: 100%;
    margin-right: 0;
    padding: 6px 0 2px;
  }

  .nav-menu {
    order: 3;
    width: 100%;
  }

  .header-right {
    margin-left: auto;
  }

  .member-search {
    width: 180px;
  }

  :deep(.el-menu--horizontal > .el-menu-item),
  :deep(.el-menu--horizontal > .el-sub-menu .el-sub-menu__title) {
    height: 56px;
    line-height: 56px;
  }
}

@media (max-width: 640px) {
  .header-right {
    width: 100%;
    justify-content: space-between;
    flex-wrap: wrap;
    margin-left: 0;
    gap: 10px;
  }

  .member-search {
    width: 100%;
  }

  .main-content {
    padding: 20px 14px 30px;
  }
}
</style>
