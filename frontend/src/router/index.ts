import { createRouter, createWebHistory } from 'vue-router'
import type { NavigationGuardNext, RouteLocationNormalized, RouteRecordRaw } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import MyProfileView from '../views/MyProfileView.vue'
import MembersView from '../views/MembersView.vue'
import PKView from '../views/PKView.vue'
import PKChallengeView from '../views/PKChallengeView.vue'
import PKProblemView from '../views/PKProblemView.vue'
import ProblemsView from '../views/ProblemsView.vue'
import ContestsView from '../views/ContestsView.vue'
import SubmissionsView from '../views/SubmissionsView.vue'
import ExternalContestsView from '../views/ExternalContestsView.vue'
import AIInterviewView from '../views/AIInterviewView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import MySubmissionsView from '../views/MySubmissionsView.vue'
import UserContestsView from '../views/UserContestsView.vue'
import ContestDetailView from '../views/ContestDetailView.vue'
import ProblemDetailView from '../views/ProblemDetailView.vue'
import TeamsView from '../views/TeamsView.vue'
import UsersView from '../views/UsersView.vue'

const routes: RouteRecordRaw[] = [
  // 认证相关：独立的 AuthLayout
  {
    path: '/login',
    component: LoginView,
    meta: { public: true, layout: 'auth' },
  },
  {
    path: '/register',
    component: RegisterView,
    meta: { public: true, layout: 'auth' },
  },

  // 用户端（student 默认角色）
  {
    path: '/',
    component: MyProfileView,
    meta: { requiresAuth: true },
  },
  {
    path: '/profile/:memberId',
    component: MyProfileView,
    meta: { requiresAuth: true },
  },
  {
    path: '/contests',
    component: UserContestsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/contests/:id',
    component: ContestDetailView,
    meta: { requiresAuth: true },
  },
  {
    path: '/problems/:id',
    component: ProblemDetailView,
    meta: { requiresAuth: true },
  },
  {
    path: '/submissions',
    component: MySubmissionsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/teams',
    component: TeamsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/pk',
    component: PKChallengeView,
    meta: { requiresAuth: true },
  },
  {
    path: '/pk/problems/:id',
    component: PKProblemView,
    meta: { requiresAuth: true },
  },
  {
    path: '/external',
    component: ExternalContestsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/ai/interview',
    component: AIInterviewView,
    meta: { requiresAuth: true },
  },

  // 管理端：暂时保留原有 CRUD 路由，整体收纳到 /admin/*
  {
    path: '/admin/submissions',
    component: SubmissionsView,
    meta: { requiresAuth: true, adminOnly: true },
  },
  {
    path: '/admin/users',
    component: UsersView,
    meta: { requiresAuth: true, adminOnly: true },
  },
  {
    path: '/admin/contests',
    component: ContestsView,
    meta: { requiresAuth: true, adminOnly: true },
  },
  {
    path: '/admin/pk',
    component: PKView,
    meta: { requiresAuth: true, adminOnly: true },
  },
  {
    path: '/admin/problems',
    component: ProblemsView,
    meta: { requiresAuth: true, adminOnly: true },
  },
  {
    path: '/admin/external',
    component: ExternalContestsView,
    meta: { requiresAuth: true, adminOnly: true },
  },
  {
    path: '/admin/ai',
    component: AIInterviewView,
    meta: { requiresAuth: true, adminOnly: true },
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

function isLoggedIn() {
  return !!window.localStorage.getItem('acm_tb_access_token')
}

function isAdmin() {
  // 简化：根据本地缓存的 role 判断；实际以 /auth/me 为准
  const raw = window.localStorage.getItem('acm_tb_user_role')
  return raw === 'admin'
}

router.beforeEach((to: RouteLocationNormalized, _from: RouteLocationNormalized, next: NavigationGuardNext) => {
  const isPublic = to.meta.public

  if (!isPublic && !isLoggedIn()) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  if (to.meta.adminOnly && !isAdmin()) {
    return next({ path: '/' })
  }

  if (to.path === '/login' && isLoggedIn()) {
    return next({ path: '/' })
  }

  return next()
})


