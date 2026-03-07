<template>
  <div class="page">
    <div class="page-hero">
      <div>
        <div class="eyebrow">Team PK</div>
        <div class="page-title">队伍 PK 管理</div>
        <div class="page-subtitle">创建 2 队对抗、跟踪当前比赛状态，并快速结算胜负结果。</div>
      </div>
      <el-button size="small" @click="load">刷新列表</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="10">
        <el-card>
          <template #header>
            <div class="card-heading">创建 PK（2 队）</div>
          </template>
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

      <el-col :xs="24" :lg="14">
        <el-card>
          <template #header>
            <div class="list-header">
              <div>
                <div class="card-heading">PK 列表</div>
                <div class="list-subtitle">支持快速查看当前状态并手动结算。</div>
              </div>
              <el-button size="small" @click="load">刷新</el-button>
            </div>
          </template>

          <el-table :data="matches" size="small" style="width:100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="title" label="标题" />
            <el-table-column prop="status" label="状态" width="110" />
            <el-table-column label="操作" min-width="180">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button size="small" type="success" @click="finish(row.id, 1)">Team1 Win</el-button>
                  <el-button size="small" type="danger" @click="finish(row.id, 2)">Team2 Win</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
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

<style scoped>
.page {
  display: grid;
  gap: 18px;
}

.page-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 22px 24px;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(111, 134, 214, 0.11), rgba(99, 183, 157, 0.12), rgba(215, 174, 106, 0.08));
  border: 1px solid rgba(220, 227, 233, 0.86);
}

.eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #8a97aa;
}

.page-title {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 800;
  color: #314154;
}

.page-subtitle,
.list-subtitle {
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.8;
  color: #6f7f94;
}

.card-heading {
  font-weight: 700;
  color: #314154;
}

.list-header,
.table-actions {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

@media (max-width: 900px) {
  .page-hero,
  .list-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
