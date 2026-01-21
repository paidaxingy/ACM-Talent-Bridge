<template>
  <el-row :gutter="16">
    <el-col :span="10">
      <el-card>
        <template #header>创建 PK（2 队）</template>
        <el-form label-width="92px">
          <el-form-item label="标题">
            <el-input v-model="form.title" placeholder="可选" />
          </el-form-item>
          <el-form-item label="Team 1 IDs">
            <el-input v-model="form.team1" placeholder="例如 1,2" />
          </el-form-item>
          <el-form-item label="Team 2 IDs">
            <el-input v-model="form.team2" placeholder="例如 3" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="creating" @click="create">创建</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>

    <el-col :span="14">
      <el-card>
        <template #header>
          <div style="display:flex; align-items:center; justify-content:space-between">
            <div>PK 列表</div>
            <el-button size="small" @click="load">刷新</el-button>
          </div>
        </template>

        <el-table :data="matches" size="small" style="width:100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="title" label="标题" />
          <el-table-column prop="status" label="状态" width="110" />
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button size="small" type="success" @click="finish(row.id, 1)">Team1 Win</el-button>
              <el-button size="small" type="danger" @click="finish(row.id, 2)">Team2 Win</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { api } from '../api/client'

const matches = ref<any[]>([])
const creating = ref(false)
const form = reactive({ title: '', team1: '', team2: '' })

function parseIds(s: string): number[] {
  return s
    .split(',')
    .map(x => x.trim())
    .filter(Boolean)
    .map(x => Number(x))
    .filter(x => Number.isFinite(x) && x > 0)
}

async function load() {
  const { data } = await api.get('/pk/matches')
  matches.value = data
}

async function create() {
  const t1 = parseIds(form.team1)
  const t2 = parseIds(form.team2)
  if (!t1.length || !t2.length) return
  creating.value = true
  try {
    await api.post('/pk/matches', { title: form.title || null, teams: [t1, t2] })
    form.title = ''
    form.team1 = ''
    form.team2 = ''
    await load()
  } finally {
    creating.value = false
  }
}

async function finish(matchId: number, winnerTeam: 1 | 2) {
  await api.post(`/pk/matches/${matchId}/finish`, { winner_team_no: winnerTeam, is_draw: false })
  await load()
}

load()
</script>
