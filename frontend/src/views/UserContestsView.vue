<template>
  <div class="page">
    <el-card class="page-card">
      <template #header>
        <div class="header">
          <div>
            <div class="eyebrow">Contest Square</div>
            <div class="title">竞赛广场</div>
            <div class="subtitle">按状态查看当前可参加的校内竞赛，快速进入详情、报名与做题。</div>
          </div>
          <div class="actions-panel">
            <div class="actions">
              <el-select v-model="statusFilter" size="small" class="filter-control" clearable placeholder="按状态筛选">
            <el-option label="全部" value="" />
            <el-option label="未开始" value="upcoming" />
            <el-option label="进行中" value="running" />
            <el-option label="已结束" value="ended" />
              </el-select>
              <el-input
                v-model="keyword"
                size="small"
                placeholder="搜索竞赛标题"
                clearable
                class="filter-control keyword-input"
              />
              <el-button size="small" type="primary" :loading="loading" @click="load">
                刷新
              </el-button>
            </div>
          </div>
        </div>
      </template>

      <el-table :data="filteredContests" size="small" style="width: 100%" @row-click="goDetail">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="比赛名称" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTagType(effectiveStatus(row))" effect="plain">
              {{ statusText(effectiveStatus(row)) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_at" label="开始时间" width="180" />
        <el-table-column prop="end_at" label="结束时间" width="180" />
      </el-table>

      <div v-if="!filteredContests.length && !loading" class="empty">
        当前没有符合条件的竞赛，可以稍后再来看看～
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'

interface Contest {
  id: number
  name: string
  // 后端可能返回 contest_status 或 status，这里都兼容
  contest_status?: 'draft' | 'published' | 'running' | 'ended'
  status?: 'draft' | 'published' | 'running' | 'ended'
  start_at?: string | null
  end_at?: string | null
}

const router = useRouter()

const contests = ref<Contest[]>([])
const loading = ref(false)
const keyword = ref('')
const statusFilter = ref<'' | 'upcoming' | 'running' | 'ended'>('')

const filteredContests = computed(() => {
  return contests.value.filter(c => {
    const s = effectiveStatus(c)
    if (s === 'draft') {
      // 学生侧不展示草稿
      return false
    }
    if (statusFilter.value === 'upcoming' && s !== 'published') return false
    if (statusFilter.value === 'running' && s !== 'running') return false
    if (statusFilter.value === 'ended' && s !== 'ended') return false
    if (keyword.value.trim()) {
      return c.name.toLowerCase().includes(keyword.value.trim().toLowerCase())
    }
    return true
  })
})

function effectiveStatus(c: Contest): Contest['contest_status'] | undefined {
  // 后端目前使用 draft / running / finished（以及早期的 registration），这里做一次映射到统一状态枚举
  const raw = (c.contest_status || c.status) as string | undefined
  if (raw === 'finished') return 'ended'
  if (raw === 'registration') return 'published'
  return raw as Contest['contest_status'] | undefined
}

function statusText(status: Contest['contest_status'] | undefined) {
  switch (status) {
    case 'published':
      return '未开始'
    case 'running':
      return '进行中'
    case 'ended':
      return '已结束'
    case 'draft':
      return '未发布'
    default:
      return '未知'
  }
}

function statusTagType(status: Contest['contest_status'] | undefined) {
  switch (status) {
    case 'published':
      return 'info'
    case 'running':
      return 'success'
    case 'ended':
      return 'warning'
    case 'draft':
      return 'info'
    default:
      return 'info'
  }
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.get<Contest[]>('/contests')
    contests.value = data
  } finally {
    loading.value = false
  }
}

function goDetail(row: Contest) {
  router.push(`/contests/${row.id}`)
}

onMounted(load)
</script>

<style scoped>
.page {
  width: 100%;
}

.page-card :deep(.el-card__header) {
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
  max-width: 540px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--el-text-color-secondary);
}

.actions-panel {
  padding: 12px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(111, 134, 214, 0.08), rgba(99, 183, 157, 0.08));
  border: 1px solid rgba(220, 227, 233, 0.84);
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-control {
  width: 150px;
}

.keyword-input {
  width: 220px;
}

.empty {
  padding: 28px;
  text-align: center;
  color: var(--el-text-color-secondary);
}

@media (max-width: 900px) {
  .header {
    flex-direction: column;
  }

  .actions-panel {
    width: 100%;
  }

  .actions {
    flex-wrap: wrap;
  }

  .filter-control,
  .keyword-input {
    width: 100%;
  }
}
</style>
