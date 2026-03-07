<template>
  <div class="pk-problem-page">
    <div class="hero-card">
      <el-page-header @back="goBack">
        <template #content>
          <div>
            <div class="eyebrow">实时对战</div>
            <span class="title">{{ problem?.title || problem?.problem_title || '加载中...' }}</span>
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
              <el-tag size="small" type="info">对战题目</el-tag>
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
            <el-row v-for="sample in samples" :key="sample.id" :gutter="12" class="sample">
              <el-col :xs="24" :md="12">
                <div class="sample-block">
                  <div class="sample-label">样例输入</div>
                  <pre>{{ sample.input }}</pre>
                </div>
              </el-col>
              <el-col :xs="24" :md="12">
                <div class="sample-block">
                  <div class="sample-label">样例输出</div>
                  <pre>{{ sample.output }}</pre>
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
                <div class="editor-subtitle">支持 Python 3 和 C++ 17，可先运行测试，再正式提交。</div>
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
              <el-input
                v-model="runInput"
                type="textarea"
                :rows="5"
                class="code-area"
                placeholder="自定义输入，例如：1 2"
              />
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="expectedOutput"
                type="textarea"
                :rows="5"
                class="code-area"
                placeholder="预期结果，例如：3"
              />
            </el-form-item>
            <el-form-item>
              <el-button :loading="running" @click="onRun">本地运行</el-button>
              <el-button type="primary" :loading="submitting" @click="onSubmit">
                提交 (Ctrl+Enter)
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="debug-card">
          <template #header>
            <div class="card-header">
              <span>本地运行结果</span>
              <div v-if="runResult" class="run-meta">
                <el-tag :type="getRunVerdictType(runResult.verdict)" size="small">{{ runResult.verdict }}</el-tag>
                <el-tag v-if="compareStatus" :type="compareStatus.matched ? 'success' : 'danger'" size="small">
                  {{ compareStatus.matched ? '与预期一致' : '与预期不一致' }}
                </el-tag>
                <span class="time">{{ displayNumber(runResult.time_ms) }} ms</span>
              </div>
            </div>
          </template>
          <div v-if="runResult">
            <div v-if="runResult.message" class="run-message">{{ runResult.message }}</div>
            <div class="run-block">
              <div class="sample-label">运行输出</div>
              <pre class="run-pre">{{ displayCombinedRunText(runResult) }}</pre>
            </div>
            <div class="run-block">
              <div class="sample-label">预期结果</div>
              <pre class="run-pre">{{ displayExpectedText(expectedOutput) }}</pre>
            </div>
          </div>
          <div v-else class="empty-subs">点击“本地运行”后查看输出、报错和耗时。</div>
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
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api/client'

const route = useRoute()
const router = useRouter()

const problemId = Number(route.params.id)
const pkChallengeIdRaw = route.query.challenge_id
const pkChallengeId = pkChallengeIdRaw
  ? Array.isArray(pkChallengeIdRaw)
    ? Number(pkChallengeIdRaw[0])
    : Number(pkChallengeIdRaw)
  : null

interface RunResult {
  verdict: string
  stdout: string
  stderr: string
  time_ms: number | null
  memory_kb: number | null
  message: string | null
}

const problem = ref<any>(null)
const samples = ref<any[]>([])
const pkChallenge = ref<any>(null)
const language = ref<'python3' | 'cpp17'>('python3')
const code = ref('')
const runInput = ref('')
const expectedOutput = ref('')
const runResult = ref<RunResult | null>(null)
const running = ref(false)
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

watch(
  language,
  (lang) => {
    const isDefaultOrEmpty = code.value.trim() === '' || code.value === PYTHON_TEMPLATE || code.value === CPP_TEMPLATE
    if (!isDefaultOrEmpty) return
    code.value = lang === 'python3' ? PYTHON_TEMPLATE : CPP_TEMPLATE
  },
  { immediate: false },
)

async function loadProblem() {
  try {
    const { data } = await api.get(`/problems/${problemId}`)
    problem.value = data

    const { data: testcaseData } = await api.get(`/problems/${problemId}/testcases`, {
      params: { is_sample: true },
    })
    const list = Array.isArray(testcaseData) ? testcaseData : []
    samples.value = list
      .filter((testcase: any) => testcase.is_sample === true || testcase.input || testcase.input_data)
      .map((testcase: any) => ({
        id: testcase.id,
        input: testcase.input ?? testcase.input_data ?? '',
        output: testcase.output ?? testcase.expected_output ?? '',
      }))

    if (samples.value.length) {
      if (!runInput.value) {
        runInput.value = samples.value[0].input
      }
      if (!expectedOutput.value) {
        expectedOutput.value = samples.value[0].output
      }
    }
  } catch (error: any) {
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
  } catch (error: any) {
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
      .filter((submission: any) => {
        if (!submission.handle) return false
        if (submission.handle !== myId && submission.handle !== opponent) return false
        if (!submission.created_at) return false
        const submitTime = new Date(submission.created_at + 'Z').getTime()
        return submitTime >= pkStartTime
      })
      .sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    myAc.value = pkSubmissions.value.some((submission: any) => submission.handle === myId && submission.verdict === 'AC')
    opponentAc.value = pkSubmissions.value.some((submission: any) => submission.handle === opponent && submission.verdict === 'AC')

    if (!pkResult.value) {
      if (myAc.value) {
        pkResult.value = { win: true, message: '恭喜！你率先 AC！', lose: false }
      } else if (opponentAc.value) {
        pkResult.value = { win: false, message: '对手已 AC，你输了', lose: true }
      }
    }
  } catch (error: any) {
    console.error('加载提交记录失败', error)
  } finally {
    loadingSubs.value = false
  }
}

async function onRun() {
  if (!code.value.trim()) {
    ElMessage.warning('代码不能为空')
    return
  }

  running.value = true
  try {
    const { data } = await api.post<RunResult>(`/problems/${problemId}/run`, {
      language: language.value,
      code: code.value,
      input: runInput.value,
    })
    runResult.value = data
    if (data.verdict === 'OK') {
      ElMessage.success('本地运行完成')
    } else {
      ElMessage.warning(data.message || `运行结束：${data.verdict}`)
    }
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '运行失败')
  } finally {
    running.value = false
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
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '提交失败')
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
  } catch (error: any) {
    console.error('轮询失败', error)
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

function getRunVerdictType(verdict: string): 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    AC: 'success',
    WA: 'danger',
    OK: 'success',
    CE: 'info',
    RE: 'danger',
    TLE: 'warning',
    SE: 'danger',
    PENDING: 'info',
  }
  return map[verdict] || 'info'
}

function formatSubmitTime(timeStr: string) {
  if (!timeStr) return '-'
  const date = new Date(timeStr + 'Z')
  return date.toLocaleTimeString('zh-CN', { hour12: false })
}

function displayCombinedRunText(result: RunResult): string {
  const stdout = result.stdout || ''
  const stderr = result.stderr || ''
  if (stdout && stderr) {
    return `${stdout}

[stderr]
${stderr}`
  }
  const merged = stdout || stderr
  return merged.length ? merged : '（空）'
}

function displayExpectedText(value: string): string {
  return value && value.length ? value : '（空）'
}

function normalizeOutput(value: string): string {
  const lines = value
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .split('\n')
    .map(line => line.replace(/\s+$/g, ''))
  while (lines.length && lines[lines.length - 1] === '') {
    lines.pop()
  }
  return lines.join('\n')
}

const compareStatus = computed(() => {
  if (!runResult.value || !expectedOutput.value.trim().length) return null
  const matched = normalizeOutput(runResult.value.stdout || '') === normalizeOutput(expectedOutput.value)
  return { matched }
})

const ojRunStatus = computed(() => {
  if (!runResult.value) {
    return { code: 'PENDING', label: 'Pending' }
  }

  if (runResult.value.verdict !== 'OK') {
    const code = runResult.value.verdict
    const labels: Record<string, string> = {
      CE: 'Compile Error',
      RE: 'Runtime Error',
      TLE: 'Time Limit Exceeded',
      SE: 'System Error',
    }
    return { code, label: labels[code] || code }
  }

  if (compareStatus.value) {
    return compareStatus.value.matched
      ? { code: 'AC', label: 'Accepted' }
      : { code: 'WA', label: 'Wrong Answer' }
  }

  return { code: 'OK', label: 'Ran Successfully' }
})

function displayNumber(value: number | null): string {
  if (value === null || value === undefined) return '--'
  return String(value)
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

.card-header,
.run-meta {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
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

.sample-block pre,
.run-pre {
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

.run-message {
  margin-bottom: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(246, 249, 251, 0.84);
  color: #4b5d72;
  font-size: 12px;
}

.run-block + .run-block {
  margin-top: 12px;
}

.run-pre {
  padding: 12px;
  border-radius: 14px;
  background: rgba(246, 249, 251, 0.84);
  border: 1px solid rgba(224, 229, 234, 0.88);
  min-height: 72px;
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
