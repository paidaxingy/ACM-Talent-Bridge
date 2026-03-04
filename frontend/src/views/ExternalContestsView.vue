<template>
  <el-card>
    <template #header>
      <div style="display:flex; align-items:center; justify-content:space-between">
        <div>赛历聚合</div>
        <div>
          <el-select v-model="source" size="small" style="width:160px">
            <el-option label="Codeforces" value="codeforces" />
          </el-select>
          <el-button
            v-if="isAdmin"
            size="small"
            style="margin-left:8px"
            :loading="refreshing"
            @click="refresh"
          >
            触发刷新
          </el-button>
          <el-button size="small" style="margin-left:8px" @click="load">加载</el-button>
        </div>
      </div>
    </template>

    <el-table :data="rows" size="small" style="width:100%">
      <el-table-column prop="source" label="来源" width="110" />
      <el-table-column prop="name" label="比赛" />
      <el-table-column prop="start_at" label="开始时间" width="180" />
      <el-table-column prop="duration_seconds" label="时长(s)" width="100" />
      <el-table-column label="链接" width="120">
        <template #default="{ row }">
          <el-link :href="linkUrl(row)" target="_blank">去注册</el-link>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'

type ContestRow = {
  source: string
  external_id: string
  url: string
  contest_phase?: string | null
  register_url?: string | null
}

const source = ref('codeforces')
const rows = ref<ContestRow[]>([])
const refreshing = ref(false)
const auth = useAuthStore()
const isAdmin = computed(() => auth.user?.role === 'admin')

function linkUrl(row: ContestRow) {
  if (row.source === 'codeforces' && row.external_id) {
    return `https://codeforces.com/contestRegistration/${row.external_id}`
  }
  return row.register_url || row.url
}

async function refresh() {
  refreshing.value = true
  try {
    await api.post('/external/contests/refresh')
  } finally {
    refreshing.value = false
  }
}

async function load() {
  const params: any = { upcoming_only: true, source: source.value }
  const { data } = await api.get('/external/contests', { params })
  rows.value = data
}

load()
</script>
