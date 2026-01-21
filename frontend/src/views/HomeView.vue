<template>
  <el-card>
    <template #header>
      <div style="display:flex; align-items:center; justify-content:space-between">
        <div>系统概览</div>
        <el-button size="small" @click="refresh">刷新健康检查</el-button>
      </div>
    </template>

    <el-descriptions :column="2" border>
      <el-descriptions-item label="状态">{{ health?.status || '-' }}</el-descriptions-item>
      <el-descriptions-item label="应用">{{ health?.app || '-' }}</el-descriptions-item>
      <el-descriptions-item label="环境">{{ health?.env || '-' }}</el-descriptions-item>
    </el-descriptions>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { api } from '../api/client'

type Health = { status: string; app: string; env: string }
const health = ref<Health | null>(null)

async function refresh() {
  const { data } = await api.get('/health')
  health.value = data
}

refresh()
</script>
