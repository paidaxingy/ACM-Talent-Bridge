<template>
  <div class="page">
    <el-card class="home-card">
      <template #header>
        <div class="header">
          <div>
            <div class="eyebrow">System Snapshot</div>
            <div class="title">系统概览</div>
            <div class="subtitle">快速确认当前服务状态，作为进入训练、比赛与面试模块前的统一入口。</div>
          </div>
          <el-button size="small" :loading="loading" @click="refresh">刷新健康检查</el-button>
        </div>
      </template>

      <div class="hero-strip">
        <div class="hero-copy">
          <div class="hero-title">今天也适合练题、打榜和复盘</div>
          <div class="hero-text">平台健康时，你可以直接继续训练、查看画像或开始 AI 面试。</div>
        </div>
        <el-tag :type="health?.status === 'ok' ? 'success' : 'warning'" size="large">
          {{ health?.status || 'unknown' }}
        </el-tag>
      </div>

      <el-descriptions :column="2" border class="status-board">
        <el-descriptions-item label="状态">{{ health?.status || '-' }}</el-descriptions-item>
        <el-descriptions-item label="应用">{{ health?.app || '-' }}</el-descriptions-item>
        <el-descriptions-item label="环境">{{ health?.env || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { api } from '../api/client'

type Health = { status: string; app: string; env: string }
const health = ref<Health | null>(null)
const loading = ref(false)

async function refresh() {
  loading.value = true
  try {
    const { data } = await api.get('/health')
    health.value = data
  } finally {
    loading.value = false
  }
}

refresh()
</script>

<style scoped>
.page {
  width: 100%;
}

.home-card :deep(.el-card__header) {
  padding-bottom: 20px;
}

.header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #8a97aa;
}

.title {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 800;
  color: #314154;
}

.subtitle {
  margin-top: 8px;
  max-width: 560px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--el-text-color-secondary);
}

.hero-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
  padding: 20px 22px;
  border-radius: 20px;
  background: linear-gradient(135deg, rgba(111, 134, 214, 0.1), rgba(99, 183, 157, 0.12), rgba(215, 174, 106, 0.08));
  border: 1px solid rgba(220, 227, 233, 0.82);
}

.hero-title {
  font-size: 20px;
  font-weight: 800;
  color: #324255;
}

.hero-text {
  margin-top: 6px;
  font-size: 14px;
  color: #6f7f94;
}

.status-board {
  overflow: hidden;
  border-radius: 16px;
}

@media (max-width: 720px) {
  .header,
  .hero-strip {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
