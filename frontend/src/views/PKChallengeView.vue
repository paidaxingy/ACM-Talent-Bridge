<template>
  <div class="page">
    <div class="page-hero">
      <div>
        <div class="eyebrow">PK Arena</div>
        <div class="page-title">单人 PK 挑战</div>
        <div class="page-subtitle">发起挑战、接受对局并追踪结果，把竞技状态和 Rating 变化放在一个页面里查看。</div>
      </div>
      <el-button size="small" :loading="creating" @click="load">刷新状态</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="8">
        <el-card class="side-card">
          <template #header>
            <div class="card-heading">发起 PK 挑战</div>
          </template>
          <el-form label-width="100px">
            <el-form-item label="挑战对象">
              <el-select
                v-model="selectedMemberId"
                placeholder="输入用户名搜索挑战对象"
                style="width: 100%"
                filterable
                clearable
                default-first-option
              >
                <el-option
                  v-for="m in members"
                  :key="m.id"
                  :label="`${m.handle} (Rating: ${m.rating})`"
                  :value="m.id"
                  :disabled="m.handle === myHandle"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="creating" :disabled="!selectedMemberId" @click="createChallenge">
                发起挑战
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="side-card stats-card">
          <template #header>
            <div class="card-heading">我的信息</div>
          </template>
          <div v-if="myProfile" class="profile-grid">
            <div class="profile-item">
              <span class="profile-label">Handle</span>
              <strong>{{ myProfile.handle }}</strong>
            </div>
            <div class="profile-item">
              <span class="profile-label">Rating</span>
              <strong>{{ myProfile.rating }}</strong>
            </div>
            <div class="profile-item">
              <span class="profile-label">Tier</span>
              <strong>{{ myProfile.tier }}</strong>
            </div>
          </div>
        </el-card>

        <el-card v-if="activeChallenge" class="side-card active-card">
          <template #header>
            <div class="card-heading">当前 PK</div>
          </template>
          <div class="active-pk">
            <div class="active-line"><span>对手</span><strong>{{ activeOpponentName }}</strong></div>
            <div class="active-line"><span>题目</span><strong>{{ getProblemName(activeChallenge.problem_id) }}</strong></div>
            <div class="active-line">
              <span>状态</span>
              <el-tag :type="getStatusType(activeChallenge.status)" size="small">
                {{ getStatusText(activeChallenge.status) }}
              </el-tag>
            </div>
            <div v-if="activeChallenge.started_at" class="active-line">
              <span>开始时间</span>
              <strong>{{ formatTime(activeChallenge.started_at) }}</strong>
            </div>
            <div class="active-actions">
              <el-button type="primary" size="small" @click="goToProblem(activeChallenge.problem_id!, activeChallenge.id)">
                去答题
              </el-button>
              <el-button type="danger" size="small" @click="giveUp">
                放弃 PK
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card class="record-card">
          <template #header>
            <div class="record-header">
              <div>
                <div class="card-heading">PK 挑战记录</div>
                <div class="record-subtitle">查看待处理挑战、进行中的对局和已结束结果。</div>
              </div>
              <el-button size="small" @click="load">刷新</el-button>
            </div>
          </template>

          <el-tabs v-model="activeTab">
            <el-tab-pane label="待处理" name="pending">
              <el-table :data="pendingChallenges" size="small" style="width: 100%">
                <el-table-column label="类型" width="80">
                  <template #default="{ row }">
                    <el-tag v-if="row.challenger_handle === myHandle" type="primary">发出</el-tag>
                    <el-tag v-else type="warning">收到</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="对手" width="140">
                  <template #default="{ row }">
                    {{ getOpponentName(row) }}
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" min-width="220">
                  <template #default="{ row }">
                    <div class="table-actions">
                      <template v-if="row.status === 'pending'">
                        <el-button v-if="row.challenger_handle === myHandle" size="small" type="danger" @click="cancel(row.id)">
                          取消
                        </el-button>
                        <template v-else>
                          <el-button size="small" type="success" @click="acceptAndGo(row)">接受</el-button>
                          <el-button size="small" type="danger" @click="reject(row.id)">拒绝</el-button>
                        </template>
                      </template>
                      <template v-else-if="row.status === 'accepted'">
                        <el-button size="small" link type="primary" @click="goToProblem(row.problem_id!, row.id)">
                          去答题 ({{ getProblemName(row.problem_id) }})
                        </el-button>
                      </template>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>

            <el-tab-pane label="已结束" name="finished">
              <el-table :data="finishedChallenges" size="small" style="width: 100%">
                <el-table-column label="类型" width="80">
                  <template #default="{ row }">
                    <el-tag v-if="row.challenger_handle === myHandle" type="primary">发出</el-tag>
                    <el-tag v-else type="warning">收到</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="对手" width="140">
                  <template #default="{ row }">
                    {{ getOpponentName(row) }}
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="结果" width="100">
                  <template #default="{ row }">
                    <el-tag v-if="row.is_draw" type="info">平局</el-tag>
                    <el-tag v-else-if="row.winner_handle === myHandle" type="success">胜利</el-tag>
                    <el-tag v-else type="danger">失败</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="Rating 变化" width="120">
                  <template #default="{ row }">
                    <span
                      v-if="getRatingDelta(row) !== null"
                      :class="['rating-delta', getRatingDelta(row)! > 0 ? 'is-up' : getRatingDelta(row)! < 0 ? 'is-down' : 'is-flat']"
                    >
                      {{ getRatingDelta(row)! > 0 ? `+${getRatingDelta(row)}` : getRatingDelta(row) }}
                    </span>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
                <el-table-column label="用时" width="120">
                  <template #default="{ row }">
                    {{ formatDuration(row.started_at, row.finished_at) }}
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

interface Challenge {
  id: number
  challenger_handle: string
  challengee_handle: string
  status: string
  problem_id: number | null
  winner_handle: string | null
  is_draw: boolean
  started_at: string | null
  finished_at: string | null
  challenger_rating_delta?: number | null
  challengee_rating_delta?: number | null
}

interface Member {
  id: number
  handle: string
  rating: number
}

const challenges = ref<Challenge[]>([])
const members = ref<Member[]>([])
const myProfile = ref<any>(null)
const myHandle = ref<string | null>(null)
const selectedMemberId = ref<number | null>(null)
const creating = ref(false)
const activeTab = ref('pending')
const pollTimer = ref<number | null>(null)
const shownResults = ref<Set<number>>(new Set())

const pendingChallenges = computed(() => challenges.value.filter(c => ['pending', 'accepted'].includes(c.status)))
const finishedChallenges = computed(() => challenges.value.filter(c => ['finished', 'rejected', 'cancelled'].includes(c.status)))

const activeChallenge = computed(() => {
  return challenges.value.find(c => c.status === 'accepted' &&
    (c.challenger_handle === myHandle.value || c.challengee_handle === myHandle.value))
})

const activeOpponentName = computed(() => {
  if (!activeChallenge.value) return ''
  return getOpponentName(activeChallenge.value)
})

const problemMap = ref<Record<number, string>>({})

async function load() {
  try {
    const [challengesRes, membersRes, profileRes] = await Promise.all([
      api.get('/pk/challenges'),
      api.get('/members'),
      api.get('/me/profile'),
    ])
    challenges.value = challengesRes.data
    members.value = membersRes.data
    myProfile.value = profileRes.data
    myHandle.value = profileRes.data.handle || null
    localStorage.setItem('pk_profile', JSON.stringify({
      handle: profileRes.data.handle || '',
    }))

    const problemIds = [...new Set(challenges.value.map(c => c.problem_id).filter(Boolean))]
    if (problemIds.length) {
      const problemsRes = await Promise.all(
        problemIds.map(id => api.get(`/problems/${id}`).catch(() => null)),
      )
      problemsRes.forEach((res: any) => {
        if (res?.data) {
          problemMap.value[res.data.id] = res.data.title
        }
      })
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '加载失败')
  }
}

async function createChallenge() {
  if (!selectedMemberId.value) return
  creating.value = true
  try {
    const opponent = members.value.find(m => m.id === selectedMemberId.value)
    await ElMessageBox.confirm(
      `确定要向 ${opponent?.handle || '该用户'} 发起 PK 挑战吗？`,
      '确认发起 PK',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )

    await api.post('/pk/challenges', { challengee_member_id: selectedMemberId.value })
    ElMessage.success('挑战已发起，等待对方接受')
    selectedMemberId.value = null
    await load()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '发起失败')
    }
  } finally {
    creating.value = false
  }
}

async function acceptAndGo(challenge: Challenge) {
  try {
    await ElMessageBox.confirm(
      '接受 PK 挑战后将跳转到题目页面',
      '确认接受',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'info' },
    )

    await api.post(`/pk/challenges/${challenge.id}/accept`)
    ElMessage.success('已接受 PK，开始比赛！')
    await load()
    if (challenge.problem_id) {
      goToProblem(challenge.problem_id, challenge.id)
    }
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '接受失败')
    }
  }
}

async function reject(id: number) {
  try {
    await api.post(`/pk/challenges/${id}/reject`)
    ElMessage.success('已拒绝挑战')
    await load()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function cancel(id: number) {
  try {
    await api.post(`/pk/challenges/${id}/cancel`)
    ElMessage.success('已取消挑战')
    await load()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function giveUp() {
  if (!activeChallenge.value) return

  try {
    await ElMessageBox.confirm(
      '放弃 PK 将会判负，确定要放弃吗？',
      '确认放弃',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' },
    )

    await api.post(`/pk/challenges/${activeChallenge.value.id}/cancel`)
    ElMessage.success('已放弃 PK')
    await load()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '操作失败')
    }
  }
}

function getOpponentName(challenge: Challenge) {
  const opponentHandle = challenge.challenger_handle === myHandle.value
    ? challenge.challengee_handle
    : challenge.challenger_handle
  if (opponentHandle) {
    return opponentHandle
  }
  return '未知对手'
}

function getStatusType(status: string) {
  const map: Record<string, string> = {
    pending: 'warning',
    accepted: 'success',
    rejected: 'danger',
    cancelled: 'info',
    finished: '',
  }
  return map[status] || ''
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    pending: '待处理',
    accepted: '进行中',
    rejected: '已拒绝',
    cancelled: '已取消',
    finished: '已结束',
  }
  return map[status] || status
}

function getRatingDelta(challenge: Challenge): number | null {
  if (challenge.is_draw) return 0
  const isChallenger = challenge.challenger_handle === myHandle.value
  const delta = isChallenger ? challenge.challenger_rating_delta : challenge.challengee_rating_delta
  if (delta === undefined || delta === null) {
    return null
  }
  return Number.isFinite(delta as number) ? (delta as number) : null
}

function getProblemName(problemId: number | null) {
  if (!problemId) return '未知'
  return problemMap.value[problemId] || `题目 #${problemId}`
}

function goToProblem(problemId: number, challengeId?: number) {
  localStorage.setItem('pk_profile', JSON.stringify({
    handle: myProfile.value?.handle || '',
  }))
  if (challengeId) {
    router.push(`/pk/problems/${problemId}?challenge_id=${challengeId}`)
  } else {
    router.push(`/pk/problems/${problemId}`)
  }
}

function formatDuration(startedAt: string | null, finishedAt: string | null) {
  if (!startedAt || !finishedAt) return '-'
  const start = new Date(startedAt + 'Z')
  const end = new Date(finishedAt + 'Z')
  const seconds = Math.floor((end.getTime() - start.getTime()) / 1000)
  if (seconds < 60) return `${seconds}秒`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}分${seconds % 60}秒`
  const hours = Math.floor(minutes / 60)
  return `${hours}时${minutes % 60}分`
}

function formatTime(timeStr: string) {
  return new Date(timeStr + 'Z').toLocaleString('zh-CN', { hour12: false })
}

async function pollForUpdates() {
  try {
    const { data } = await api.get<Challenge[]>('/pk/challenges')
    const oldMap = new Map(challenges.value.map(c => [c.id, c]))
    challenges.value = data

    for (const newChallenge of data) {
      const oldChallenge = oldMap.get(newChallenge.id)

      if (!oldChallenge) {
        if (newChallenge.challengee_handle === myHandle.value && newChallenge.status === 'pending') {
          ElMessageBox.alert(
            `${newChallenge.challenger_handle || '有人'} 向你发起 PK 挑战！`,
            '收到 PK 挑战',
            { confirmButtonText: '去查看', type: 'info' },
          ).then(() => {
            activeTab.value = 'pending'
          })
        }
      } else if (oldChallenge.status !== newChallenge.status) {
        if (newChallenge.status === 'accepted' && newChallenge.challengee_handle === myHandle.value) {
          ElMessageBox.alert(
            `你的 PK 挑战已被接受！\n题目: ${getProblemName(newChallenge.problem_id)}`,
            'PK 已开始',
            { confirmButtonText: '去答题', type: 'success' },
          ).then(() => {
            if (newChallenge.problem_id) {
              goToProblem(newChallenge.problem_id, newChallenge.id)
            }
          })
        } else if (newChallenge.status === 'finished' && !shownResults.value.has(newChallenge.id)) {
          shownResults.value.add(newChallenge.id)
          if (newChallenge.winner_handle === myHandle.value) {
            ElMessageBox.alert(
              `你赢得了 PK！\n用时: ${formatDuration(newChallenge.started_at, newChallenge.finished_at)}`,
              'PK 胜利',
              { confirmButtonText: '确定', type: 'success' },
            )
          } else if (newChallenge.winner_handle && newChallenge.winner_handle !== myHandle.value) {
            const opponent = getOpponentName(newChallenge)
            ElMessageBox.alert(
              `你输给了 ${opponent}\n用时: ${formatDuration(newChallenge.started_at, newChallenge.finished_at)}`,
              'PK 失败',
              { confirmButtonText: '确定', type: 'error' },
            )
          } else if (newChallenge.is_draw) {
            ElMessageBox.alert(
              `平局！\n用时: ${formatDuration(newChallenge.started_at, newChallenge.finished_at)}`,
              'PK 平局',
              { confirmButtonText: '确定', type: 'info' },
            )
          }
        }
      }
    }
  } catch (e: any) {
    console.error('轮询失败:', e)
  }
}

onMounted(async () => {
  await load()
  pollTimer.value = window.setInterval(pollForUpdates, 3000)
})

onBeforeUnmount(() => {
  if (pollTimer.value !== null) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
})
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

.page-subtitle {
  margin-top: 8px;
  max-width: 640px;
  font-size: 14px;
  line-height: 1.8;
  color: #6f7f94;
}

.side-card,
.record-card {
  margin-bottom: 16px;
}

.card-heading {
  font-weight: 700;
  color: #314154;
}

.record-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.record-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.profile-grid {
  display: grid;
  gap: 10px;
}

.profile-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(246, 249, 251, 0.74);
  border: 1px solid rgba(224, 229, 234, 0.88);
}

.profile-label,
.active-line span {
  display: block;
  font-size: 12px;
  color: #8795a8;
}

.profile-item strong,
.active-line strong {
  display: block;
  margin-top: 6px;
  color: #314154;
}

.active-pk {
  display: grid;
  gap: 12px;
}

.active-line {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(224, 229, 234, 0.88);
}

.active-actions,
.table-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.rating-delta.is-up {
  color: #3b9b72;
}

.rating-delta.is-down {
  color: #cb736d;
}

.rating-delta.is-flat {
  color: #728197;
}

@media (max-width: 900px) {
  .page-hero,
  .record-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
