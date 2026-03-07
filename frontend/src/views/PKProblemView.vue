<template>
  <div class="pk-problem-page">
    <div class="hero-card">
      <el-page-header @back="goBack">
        <template #content>
          <div>
            <div class="eyebrow">PK Match</div>
            <span class="title">{{ problem?.problem_title || '加载中...' }}</span>
          </div>
        </template>
        <template #extra>
          <div class="hero-extra">
            <el-tag v-if="pkChallenge" :type="getStatusType(pkChallenge.status)" size="large">
              {{ getStatusText(pkChallenge.status) }}
            </el-tag>
            <span v-if="pkChallenge" class="opponent">对手: {{ opponentName }}</span>
          </div>
        </template>
      </el-page-header>
    </div>

    <div class="content">
      <div class="left">
        <el-card class="statement-card">
          <template #header>
            <div class="card-header">
              <span>题目 #{{ problemId }}</span>
              <el-tag size="small" type="info">PK 专用</el-tag>
            </div>
          </template>

          <div v-if="problem">
            <h3 class="section-title">题目描述</h3>
            <p class="paragraph">{{ problem.statement }}</p>

            <h3 class="section-title" v-if="problem.input_desc">输入描述</h3>
            <p class="paragraph" v-if="problem.input_desc">{{ problem.input_desc }}</p>

            <h3 class="section-title" v-if="problem.output_desc">输出描述</h3>
            <p class="paragraph" v-if="problem.output_desc">{{ problem.output_desc }}</p>

            <h3 class="section-title" v-if="samples.length">样例</h3>
            <el-row v-for="s in samples" :key="s.id" :gutter="12" class="sample">
              <el-col :xs="24" :md="12">
                <div class="sample-block">
                  <div class="sample-label">样例输入</div>
                  <pre>{{ s.input }}</pre>
                </div>
              </el-col>
              <el-col :xs="24" :md="12">
                <div class="sample-block">
                  <div class="sample-label">样例输出</div>
                  <pre>{{ s.output }}</pre>
                </div>
              </el-col>
            </el-row>
          </div>
          <div v-else class="loading-text">正在加载题面...</div>
        </el-card>
      </div>

      <div class="right">
        <el-card class="editor-card">
          <template #header>
            <div class="card-header">
              <div>
                <div class="editor-title">代码编辑</div>
                <div class="editor-subtitle">支持 Python 3 / C++ 17，提交后会自动刷新 PK 状态。</div>
              </div>
              <el-select v-model="language" class="language-select" size="small">
                <el-option label="Python 3" value="python3" />
                <el-option label="C++ 17" value="cpp17" />
              </el-select>
            </div>
          </template>

          <el-form label-width="0" size="small">
            <el-form-item>
              <el-input
                v-model="code"
                type="textarea"
                :rows="16"
                class="code-area"
                placeholder="在这里编写你的代码..."
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="submitting" @click="onSubmit">
                提交 (Ctrl+Enter)
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <span>PK 状态</span>
              <span class="time">{{ formatDuration(pkChallenge?.started_at, currentTime) }}</span>
            </div>
          </template>
          <div class="pk-status">
            <div class="player">
              <span class="name">{{ myHandle || '我' }}</span>
              <el-tag v-if="myAc" type="success" size="small">已 AC</el-tag>
            </div>
            <div class="vs">VS</div>
            <div class="player">
              <span class="name">{{ opponentName || '对手' }}</span>
              <el-tag v-if="opponentAc" type="success" size="small">已 AC</el-tag>
            </div>
          </div>
        </el-card>

        <el-card class="submissions-card">
          <template #header>
            <div class="card-header">
              <span>实时提交记录</span>
              <el-button size="small" @click="loadSubmissions" :loading="loadingSubs">刷新</el-button>
            </div>
          </template>
          <el-table :data="pkSubmissions" size="small" style="width: 100%">
            <el-table-column label="选手" width="110">
              <template #default="{ row }">
                <el-tag type="primary" size="small">
                  {{ getMemberName(row.handle) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="结果" width="90">
              <template #default="{ row }">
                <el-tag :type="getVerdictType(row.verdict)" size="small">
                  {{ row.verdict || row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="语言" width="90">
              <template #default="{ row }">
                {{ row.language }}
              </template>
            </el-table-column>
            <el-table-column label="耗时" width="90">
              <template #default="{ row }">
                {{ row.time_ms ? `${row.time_ms}ms` : '-' }}
              </template>
            </el-table-column>
            <el-table-column label="时间" width="100">
              <template #default="{ row }">
                {{ formatSubmitTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
          <div v-if="!pkSubmissions.length" class="empty-subs">暂无提交记录</div>
        </el-card>
      </div>
    </div>

    <el-result
      v-if="pkResult"
      :icon="pkResult.win ? 'success' : 'error'"
      :title="pkResult.win ? '你赢了！' : pkResult.lose ? '你输了' : '平局'"
      :sub-title="pkResult.message"
      class="result-card"
    >
      <template #extra>
        <el-button type="primary" @click="goBack">返回 PK 页面</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()

const problemId = Number(route.params.id)
const pkChallengeIdRaw = route.query.challenge_id
const pkChallengeId = pkChallengeIdRaw ? (Array.isArray(pkChallengeIdRaw) ? Number(pkChallengeIdRaw[0]) : Number(pkChallengeIdRaw)) : null

const problem = ref<any>(null)
const samples = ref<any[]>([])
const pkChallenge = ref<any>(null)
const language = ref<'python3' | 'cpp17'>('python3')
const code = ref('')
const submitting = ref(false)
const currentTime = ref<string | null>(null)
const myAc = ref(false)
const opponentAc = ref(false)
const pkResult = ref<any>(null)
const pollTimer = ref<number | null>(null)

const opponentName = ref('')
const pkSubmissions = ref<any[]>([])
const loadingSubs = ref(false)
const opponentId = ref<number | null>(null)
const myHandle = ref<string | null>(null)

const PYTHON_TEMPLATE = `print(input())
`

const CPP_TEMPLATE = `#include <bits/stdc++.h>
using namespace std;

int main() {
  ios::sync_with_stdio(false);
  cin.tie(nullptr);

  return 0;
}
`

watch(language, lang => {
  const isDefaultOrEmpty = code.value.trim() === '' || code.value === PYTHON_TEMPLATE || code.value === CPP_TEMPLATE
  if (!isDefaultOrEmpty) return
  code.value = lang === 'python3' ? PYTHON_TEMPLATE : CPP_TEMPLATE
}, { immediate: false })

async function loadProblem() {
  try {
    const { data } = await api.get(`/problems/${problemId}`)
    problem.value = data

    const { data: tcData } = await api.get(`/problems/${problemId}/testcases`, {
      params: { is_sample: true },
    })
    const list = Array.isArray(tcData) ? tcData : []
    samples.value = list
      .filter((tc: any) => tc.is_sample === true || tc.input || tc.input_data)
      .map((tc: any) => ({
        id: tc.id,
        input: tc.input ?? tc.input_data ?? '',
        output: tc.output ?? tc.expected_output ?? '',
      }))
  } catch (e: any) {
    ElMessage.error('加载题目失败')
  }
}

async function loadPKChallenge() {
  if (!pkChallengeId) {
    ElMessage.warning('缺少 PK 挑战 ID，请从 PK 页面重新进入')
    return
  }
  try {
    const { data } = await api.get(`/pk/challenges/${pkChallengeId}`)
    pkChallenge.value = data

    const profileStr = localStorage.getItem('pk_profile')
    if (profileStr) {
      const profile = JSON.parse(profileStr)
      myHandle.value = profile.handle || null
    }

    if (myHandle.value === data.challenger_handle) {
      opponentName.value = data.challengee_handle || `ID: ${data.challengee_member_id}`
      opponentId.value = data.challengee_member_id
    } else {
      opponentName.value = data.challenger_handle || `ID: ${data.challenger_member_id}`
      opponentId.value = data.challenger_member_id
    }
  } catch (e: any) {
    ElMessage.error('加载PK信息失败')
  }
}

async function loadSubmissions() {
  loadingSubs.value = true
  try {
    if (!pkChallenge.value || !pkChallenge.value.started_at) return

    const { data } = await api.get('/submissions', {
      params: { problem_id: problemId, contest_id: null },
    })

    const opponent = opponentId.value
    const myId = myHandle.value
    const pkStartTime = new Date(pkChallenge.value.started_at + 'Z').getTime()

    if (!myId || !opponent) return

    pkSubmissions.value = data
      .filter((s: any) => {
        if (!s.handle) return false
        if (s.handle !== myId && s.handle !== opponent) return false
        if (!s.created_at) return false
        const submitTime = new Date(s.created_at + 'Z').getTime()
        return submitTime >= pkStartTime
      })
      .sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    myAc.value = pkSubmissions.value.some((s: any) => s.handle === myId && s.verdict === 'AC')
    opponentAc.value = pkSubmissions.value.some((s: any) => s.handle === opponent && s.verdict === 'AC')

    if (!pkResult.value) {
      if (myAc.value) {
        pkResult.value = { win: true, message: '恭喜！你率先 AC！', lose: false }
      } else if (opponentAc.value) {
        pkResult.value = { win: false, message: '对手已 AC，你输了', lose: true }
      }
    }
  } catch (e: any) {
    console.error('加载提交记录失败', e)
  } finally {
    loadingSubs.value = false
  }
}

async function onSubmit() {
  if (!code.value.trim()) {
    ElMessage.warning('代码不能为空')
    return
  }
  if (!pkChallenge.value) {
    ElMessage.warning('PK 未开始')
    return
  }
  if (pkChallenge.value.status !== 'accepted') {
    ElMessage.warning('PK 已结束')
    return
  }

  submitting.value = true
  try {
    await api.post('/submissions', {
      problem_id: problemId,
      contest_id: null,
      team_id: null,
      language: language.value,
      code: code.value,
    })
    ElMessage.success('提交成功，评测中...')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

async function pollStatus() {
  if (!pkChallengeId) return

  try {
    const { data } = await api.get(`/pk/challenges/${pkChallengeId}`)
    pkChallenge.value = data
    currentTime.value = new Date().toISOString()
    await loadSubmissions()

    if (data.status === 'finished' && !pkResult.value) {
      if (data.winner_handle === myHandle.value) {
        pkResult.value = { win: true, message: '恭喜！你赢了！', lose: false }
        ElMessageBox.alert('你赢得了 PK！', '胜利', { confirmButtonText: '确定', type: 'success' })
      } else if (data.winner_handle && data.winner_handle !== myHandle.value) {
        pkResult.value = { win: false, message: `你输给了 ${opponentName.value}`, lose: true }
        ElMessageBox.alert(`你输给了 ${opponentName.value}`, '失败', { confirmButtonText: '确定', type: 'error' })
      } else if (data.is_draw) {
        pkResult.value = { win: false, message: '平局', lose: false }
        ElMessageBox.alert('平局！', 'PK 结束', { confirmButtonText: '确定', type: 'info' })
      }
    }
  } catch (e: any) {
    console.error('轮询失败', e)
  }
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

function formatDuration(startedAt: string | null, nowStr: string | null) {
  if (!startedAt || !nowStr) return '-'
  const start = new Date(startedAt + 'Z')
  const end = new Date(nowStr)
  const seconds = Math.floor((end.getTime() - start.getTime()) / 1000)
  if (seconds < 0) return '0秒'
  if (seconds < 60) return `${seconds}秒`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}分${seconds % 60}秒`
  const hours = Math.floor(minutes / 60)
  return `${hours}时${minutes % 60}分${seconds % 60}秒`
}

function goBack() {
  router.push('/pk')
}

function getMemberName(handle: string) {
  if (handle === myHandle.value) return '我'
  if (handle === opponentName.value) return opponentName.value
  return handle
}

function getVerdictType(verdict: string | null) {
  if (!verdict) return 'info'
  const map: Record<string, string> = {
    AC: 'success',
    WA: 'danger',
    TLE: 'warning',
    MLE: 'warning',
    RE: 'warning',
    CE: 'info',
    PE: 'warning',
  }
  return map[verdict] || 'info'
}

function formatSubmitTime(timeStr: string) {
  if (!timeStr) return '-'
  const date = new Date(timeStr + 'Z')
  return date.toLocaleTimeString('zh-CN', { hour12: false })
}

onMounted(async () => {
  code.value = PYTHON_TEMPLATE
  currentTime.value = new Date().toISOString()

  await loadProblem()
  await loadPKChallenge()
  await loadSubmissions()

  pollTimer.value = window.setInterval(pollStatus, 1000)
})

onBeforeUnmount(() => {
  if (pollTimer.value !== null) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
})
</script>

<style scoped>
.pk-problem-page {
  display: grid;
  gap: 18px;
}

.hero-card {
  padding: 18px 20px;
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

.title {
  display: block;
  margin-top: 8px;
  font-size: 28px;
  font-weight: 800;
  color: #314154;
}

.hero-extra {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.opponent {
  color: #68788d;
}

.content {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(0, 0.92fr);
  gap: 16px;
}

.left,
.right {
  min-width: 0;
}

.right {
  display: grid;
  gap: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.editor-title {
  font-weight: 700;
  color: #314154;
}

.editor-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.language-select {
  width: 140px;
}

.section-title {
  margin: 14px 0 8px;
  font-weight: 700;
  color: #314154;
}

.paragraph {
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  color: #4b5d72;
}

.sample {
  margin-top: 8px;
}

.sample-block {
  height: 100%;
  background: rgba(246, 249, 251, 0.84);
  border-radius: 14px;
  padding: 12px;
  border: 1px solid rgba(224, 229, 234, 0.88);
}

.sample-label {
  font-size: 12px;
  color: #7a889b;
  margin-bottom: 6px;
}

.sample-block pre {
  margin: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 12px;
  white-space: pre-wrap;
}

.loading-text {
  font-size: 14px;
  color: #8896a8;
}

.code-area :deep(textarea) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  min-height: 370px;
  background: rgba(250, 252, 255, 0.92) !important;
}

.pk-status {
  display: flex;
  justify-content: space-around;
  align-items: center;
  gap: 14px;
  padding: 10px 0;
}

.player {
  min-width: 110px;
  text-align: center;
  padding: 16px 14px;
  border-radius: 16px;
  background: rgba(246, 249, 251, 0.72);
  border: 1px solid rgba(224, 229, 234, 0.88);
}

.player .name {
  display: block;
  font-weight: 700;
  margin-bottom: 8px;
  color: #314154;
}

.vs {
  font-size: 28px;
  font-weight: 800;
  color: #6f86d6;
}

.time {
  font-size: 13px;
  color: #6f7f94;
}

.empty-subs {
  padding: 22px;
  text-align: center;
  color: #8896a8;
}

.result-card {
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.66);
}

@media (max-width: 960px) {
  .content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .hero-extra,
  .card-header,
  .pk-status {
    flex-direction: column;
    align-items: flex-start;
  }

  .language-select {
    width: 100%;
  }

  .title {
    font-size: 24px;
  }
}
</style>
