<template>
  <div class="page">
    <div class="layout">
      <el-card class="meta-card">
      <template #header>
        <div class="meta-header">
          <div>
            <div class="contest-title">{{ contest?.name || '加载中...' }}</div>
            <div class="contest-subtitle">
              <el-tag :type="statusTagType(effectiveStatus)" size="small">
                {{ statusText(effectiveStatus) }}
              </el-tag>
              <span v-if="contest?.start_at" class="time">
                {{ contest?.start_at }} — {{ contest?.end_at || '未设置结束时间' }}
              </span>
            </div>
          </div>
          <div class="meta-actions">
            <div v-if="activeRegistration">
              <span class="active-team">
                <template v-if="activeRegistration.type === 'team'">
                  当前参赛队伍：<strong>{{ activeRegistration.team_name || `队伍 #${activeRegistration.team_id}` }}</strong>
                  <span class="team-id">（ID: {{ activeRegistration.team_id }}）</span>
                </template>
                <template v-else>
                  当前状态：<strong>个人参赛</strong>
                </template>
              </span>
            </div>
            <el-button type="primary" size="small" :loading="registering" @click="openRegisterDialog" :disabled="!canRegister">
              {{ registerButtonText }}
            </el-button>
          </div>
        </div>
      </template>
      <div v-if="contest">
        <p class="meta-row"><strong>比赛 ID：</strong>{{ contest.id }}</p>
        <p class="meta-row"><strong>简介：</strong>{{ contest.description || '暂无描述' }}</p>
      </div>
      <div v-else class="loading-text">正在加载竞赛信息...</div>
      </el-card>

      <el-card class="main-card">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="题目列表" name="problems">
            <el-table :data="problems" size="small" style="width: 100%" @row-click="goProblem">
              <el-table-column prop="problem_letter" label="#" width="80" />
              <el-table-column prop="problem_title" label="题目" />
              <el-table-column prop="problem_id" label="ID" width="100" />
            </el-table>
            <div v-if="!problems.length" class="empty">暂无题目，请联系管理员配置竞赛题目。</div>
          </el-tab-pane>
          <el-tab-pane label="队伍榜" name="scoreboard">
            <div v-if="!scoreboard">
              <el-button type="primary" size="small" :loading="loadingScoreboard" @click="loadScoreboard">
                加载榜单
              </el-button>
            </div>
            <el-table v-else :data="scoreboard.rows" size="small" style="width: 100%">
              <el-table-column prop="team_id" label="队伍 ID" width="90" />
              <el-table-column prop="team_name" label="队伍" />
              <el-table-column prop="members" label="成员">
                <template #default="{ row }">
                  <span v-for="(m, idx) in row.members" :key="m.user_id">
                    {{ m.username }}<span v-if="idx < row.members.length - 1">、</span>
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="solved" label="Solved" width="90" />
              <el-table-column prop="penalty_minutes" label="罚时" width="90" />
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <el-dialog v-model="registerDialogVisible" title="报名参赛" width="440px">
      <el-radio-group v-model="registerType" class="register-type-group">
        <el-radio label="individual">个人参赛</el-radio>
        <el-radio label="team">团队参赛</el-radio>
      </el-radio-group>
      <div v-if="registerType === 'team'" style="margin-top: 16px">
        <div v-if="!myTeams.length" style="font-size: 13px; color: var(--el-text-color-secondary)">
          你当前还没有队伍，请先在"我的队伍"页创建或加入队伍后再来报名。
        </div>
        <el-radio-group v-else v-model="selectedTeamId" class="team-radio-group">
          <el-radio v-for="t in myTeams" :key="t.team_id" :label="t.team_id">
            {{ t.team_name || `队伍 #${t.team_id}` }}（ID: {{ t.team_id }}）
          </el-radio>
        </el-radio-group>
      </div>
      <div v-else style="margin-top: 16px; font-size: 13px; color: var(--el-text-color-secondary)">
        个人参赛无需组队，可直接参加比赛。
      </div>
      <template #footer>
        <el-button @click="registerDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="registering" @click="onRegisterConfirm">确认报名</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()
const contestId = Number(route.params.id)

interface ContestDetail {
  id: number
  name: string
  description?: string | null
  // 新字段兼容：后端可能返回 contest_status 或 status
  contest_status?: 'draft' | 'published' | 'running' | 'ended'
  status?: 'draft' | 'published' | 'running' | 'ended'
  start_at?: string | null
  end_at?: string | null
}

interface ContestProblem {
  problem_id: number
  problem_letter: string
  problem_title: string
}

interface ScoreboardRow {
  team_id: number
  team_name: string
  members: { user_id: number; username: string }[]
  solved: number
  penalty_minutes: number
  // problems: ... 省略 P1 细节
}

interface Scoreboard {
  rows: ScoreboardRow[]
}

interface MyTeam {
  team_id: number
  team_name: string | null
  team_members: { user_id: number; username: string }[]
}

interface ActiveRegistration {
  type: 'team' | 'individual'
  team_id?: number
  team_name?: string | null
}

const contest = ref<ContestDetail | null>(null)
const problems = ref<ContestProblem[]>([])
const scoreboard = ref<Scoreboard | null>(null)
const myTeams = ref<MyTeam[]>([])
const activeRegistration = ref<ActiveRegistration | null>(null)
const registerDialogVisible = ref(false)
const selectedTeamId = ref<number | null>(null)
const registerType = ref<'individual' | 'team'>('individual')

const activeTab = ref<'problems' | 'scoreboard'>('problems')
const registering = ref(false)
const loadingScoreboard = ref(false)
let scoreboardTimer: number | null = null

const effectiveStatus = computed<ContestDetail['contest_status'] | undefined>(() => {
  if (!contest.value) return undefined
  const raw = contest.value.contest_status || contest.value.status
  if (raw === 'finished') return 'ended'
  if (raw === 'registration') return 'published'
  return raw
})

const canRegister = computed(() => {
  return effectiveStatus.value === 'published' || effectiveStatus.value === 'running'
})

const registerButtonText = computed(() => {
  const status = effectiveStatus.value
  if (!contest.value) return '报名参赛'
  if (status === 'draft') return '未发布，暂不可报名'
  if (status === 'ended') return '已结束，不可报名'
  if (!canRegister.value) return '当前状态不可报名'
  return '报名参赛'
})

function statusText(status?: ContestDetail['contest_status']) {
  switch (status) {
    case 'published':
      return '未开始'
    case 'running':
      return '进行中'
    case 'ended':
      return '已结束'
    default:
      return '未知'
  }
}

function statusTagType(status?: ContestDetail['contest_status']) {
  switch (status) {
    case 'published':
      return 'info'
    case 'running':
      return 'success'
    case 'ended':
      return 'warning'
    default:
      return 'info'
  }
}

async function loadContest() {
  const { data } = await api.get<ContestDetail>(`/contests/${contestId}`)
  contest.value = data
}

async function loadProblems() {
  const { data } = await api.get<ContestProblem[]>(`/contests/${contestId}/problems/detail`)
  problems.value = data
}

async function loadMyTeams() {
  const { data } = await api.get<MyTeam[]>('/me/teams')
  myTeams.value = data
  const storedTeam = window.localStorage.getItem(`acm_tb_active_team_${contestId}`)
  const storedIndividual = window.localStorage.getItem(`acm_tb_active_individual_${contestId}`)
  if (storedIndividual === 'true') {
    activeRegistration.value = { type: 'individual' }
    registerType.value = 'individual'
  } else if (storedTeam) {
    const team = myTeams.value.find(t => t.team_id === Number(storedTeam))
    if (team) {
      activeRegistration.value = { type: 'team', team_id: team.team_id, team_name: team.team_name }
      selectedTeamId.value = team.team_id
      registerType.value = 'team'
    }
  }
}

async function loadScoreboard() {
  loadingScoreboard.value = true
  try {
    const { data } = await api.get<Scoreboard>(`/contests/${contestId}/scoreboard`)
    scoreboard.value = data
  } finally {
    loadingScoreboard.value = false
  }
}

function openRegisterDialog() {
  if (activeRegistration.value?.type === 'team' && activeRegistration.value.team_id) {
    selectedTeamId.value = activeRegistration.value.team_id
    registerType.value = 'team'
  } else {
    registerType.value = 'individual'
    selectedTeamId.value = null
  }
  registerDialogVisible.value = true
}

async function onRegisterConfirm() {
  if (!canRegister.value) return
  registering.value = true
  try {
    if (registerType.value === 'individual') {
      await api.post(`/contests/${contestId}/register`, {})
      activeRegistration.value = { type: 'individual' }
      window.localStorage.setItem(`acm_tb_active_individual_${contestId}`, 'true')
      window.localStorage.removeItem(`acm_tb_active_team_${contestId}`)
      ElMessage.success('报名成功，你将以个人身份参赛')
    } else {
      const id = selectedTeamId.value
      if (!id) {
        ElMessage.warning('请选择一支队伍报名')
        return
      }
      const team = myTeams.value.find(t => t.team_id === id)
      if (!team) {
        ElMessage.error('选择的队伍不存在，请刷新后重试')
        return
      }
      await api.post(`/contests/${contestId}/register-team`, { team_id: team.team_id })
      activeRegistration.value = { type: 'team', team_id: team.team_id, team_name: team.team_name }
      window.localStorage.setItem(`acm_tb_active_team_${contestId}`, String(team.team_id))
      window.localStorage.removeItem(`acm_tb_active_individual_${contestId}`)
      ElMessage.success('报名成功，队伍已加入本场竞赛')
    }
    registerDialogVisible.value = false
  } catch (e: any) {
    const status = e?.response?.status
    const detail = e?.response?.data?.error_detail || e?.response?.data?.detail
    if (status === 409 && typeof detail === 'string' && detail.toLowerCase().includes('already')) {
      if (registerType.value === 'individual') {
        activeRegistration.value = { type: 'individual' }
        window.localStorage.setItem(`acm_tb_active_individual_${contestId}`, 'true')
        window.localStorage.removeItem(`acm_tb_active_team_${contestId}`)
      } else {
        const team = myTeams.value.find(t => t.team_id === selectedTeamId.value)
        if (team) {
          activeRegistration.value = { type: 'team', team_id: team.team_id, team_name: team.team_name }
          window.localStorage.setItem(`acm_tb_active_team_${contestId}`, String(team.team_id))
          window.localStorage.removeItem(`acm_tb_active_individual_${contestId}`)
        }
      }
      ElMessage.info('已报名成功')
      registerDialogVisible.value = false
    } else {
      const msg = detail || '报名失败，请稍后重试'
      ElMessage.error(msg)
    }
  } finally {
    registering.value = false
  }
  }

function goProblem(row: ContestProblem) {
  const query: Record<string, any> = { contest_id: contestId }
  if (activeRegistration.value?.type === 'team' && activeRegistration.value.team_id) {
    query.team_id = activeRegistration.value.team_id
  }
  router.push({ path: `/problems/${row.problem_id}`, query })
}

onMounted(async () => {
  await Promise.allSettled([loadContest(), loadProblems(), loadMyTeams()])
  if (route.hash === '#scoreboard') {
    activeTab.value = 'scoreboard'
    await loadScoreboard()
  }
})

watch(
  () => activeTab.value,
  async val => {
    if (val === 'scoreboard') {
      await loadScoreboard()
      if (scoreboardTimer === null) {
        scoreboardTimer = window.setInterval(() => {
          loadScoreboard()
        }, 8000)
      }
    } else if (scoreboardTimer !== null) {
      window.clearInterval(scoreboardTimer)
      scoreboardTimer = null
    }
  },
)

onBeforeUnmount(() => {
  if (scoreboardTimer !== null) {
    window.clearInterval(scoreboardTimer)
    scoreboardTimer = null
  }
})
</script>

<style scoped>
.page {
  width: 100%;
}

.layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.meta-card {
  margin-bottom: 4px;
}

.meta-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.meta-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.active-team {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.active-team .team-id {
  margin-left: 4px;
}

.contest-title {
  font-size: 18px;
  font-weight: 700;
}

.contest-subtitle {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.time {
  opacity: 0.9;
}

.meta-row {
  margin: 4px 0;
  font-size: 13px;
}

.main-card {
  margin-top: 0;
}

.empty {
  padding: 16px;
  text-align: center;
  color: var(--el-text-color-secondary);
}

.loading-text {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>

