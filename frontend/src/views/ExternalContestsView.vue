<template>
  <el-card>
    <template #header>
      <div style="display:flex; align-items:center; justify-content:space-between">
        <div>赛历聚合</div>
        <div>
          <el-select v-model="source" size="small" style="width:160px">
            <el-option label="All" value="" />
            <el-option label="Codeforces" value="codeforces" />
            <el-option label="AtCoder" value="atcoder" />
            <el-option label="Nowcoder" value="nowcoder" />
          </el-select>
          <el-button size="small" style="margin-left:8px" :loading="refreshing" @click="refresh">触发刷新</el-button>
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
          <el-link :href="row.url" target="_blank">打开</el-link>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { api } from '../api/client'

const source = ref('')
const rows = ref<any[]>([])
const refreshing = ref(false)

async function refresh() {
  refreshing.value = true
  try {
    await api.post('/external/contests/refresh')
  } finally {
    refreshing.value = false
  }
}

async function load() {
  const params: any = { upcoming_only: true }
  if (source.value) params.source = source.value
  const { data } = await api.get('/external/contests', { params })
  rows.value = data
}

load()
</script>
