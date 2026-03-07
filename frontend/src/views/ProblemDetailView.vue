<template>
  <div class="page-wrap">
    <div class="page">
      <div class="left">
        <el-card class="statement-card">
          <template #header>
            <div class="header">
              <div class="title">
                {{ problem?.title || problem?.problem_title || '题目详情' }}
                <span v-if="problemId" class="id">#{{ problemId }}</span>
              </div>
              <div class="subtitle">在这里查看题目、编写代码、运行测试并提交答案。</div>
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
              <el-col :span="12">
                <div class="sample-block">
                  <div class="sample-label">样例输入</div>
                  <pre>{{ sample.input }}</pre>
                </div>
              </el-col>
              <el-col :span="12">
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
            <div class="header">
              <div class="title">代码编辑、运行与提交</div>
              <div class="subtitle" v-if="contestId">
                竞赛 ID：{{ contestId }}
                <span v-if="teamId">｜队伍 ID：{{ teamId }}</span>
                <span v-else>｜个人参赛</span>
                <span v-if="activeTeamName">｜当前队伍：{{ activeTeamName }}</span>
              </div>
            </div>
          </template>

          <el-form label-width="84px" size="small">
            <el-form-item label="语言">
              <el-select v-model="language" style="width: 160px">
                <el-option label="Python 3" value="python3" />
                <el-option label="C++ 17" value="cpp17" />
              </el-select>
            </el-form-item>
            <el-form-item label="代码">
              <el-input
                v-model="code"
                type="textarea"
                :rows="18"
                class="code-area"
                placeholder="在这里编写你的代码..."
              />
            </el-form-item>
            <el-form-item label="自定义输入">
              <el-input
                v-model="runInput"
                type="textarea"
                :rows="6"
                class="code-area"
                placeholder="例如：1 2"
              />
            </el-form-item>
            <el-form-item label="预期结果">
              <el-input
                v-model="expectedOutput"
                type="textarea"
                :rows="5"
                class="code-area"
                placeholder="填写你期望程序输出的结果"
              />
            </el-form-item>
            <el-form-item>
              <el-button :loading="running" @click="onRun">本地运行</el-button>
              <el-button type="primary" :loading="submitting" @click="onSubmit">提交</el-button>
              <el-button style="margin-left: 8px" @click="loadMySubmissions">刷新结果</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="debug-card" style="margin-top: 12px">
          <template #header>
            <div class="header debug-header">
              <div class="title">本地运行结果</div>
              <div class="run-meta" v-if="runResult">
                <el-tag :type="getRunVerdictType(ojRunStatus.code)" size="small">{{ ojRunStatus.label }}</el-tag>
                <span>耗时：{{ displayNumber(runResult.time_ms) }} ms</span>
                <span>内存：{{ displayNumber(runResult.memory_kb) }} KB</span>
              </div>
            </div>
          </template>

          <div v-if="runResult">
            <div v-if="runResult.message" class="run-message">{{ runResult.message }}</div>

            <div class="run-block">
              <div class="run-label">运行输出</div>
              <pre class="run-pre">{{ displayCombinedRunText(runResult) }}</pre>
            </div>

            <div class="run-block">
              <div class="run-label">预期结果</div>
              <pre class="run-pre">{{ displayExpectedText(expectedOutput) }}</pre>
            </div>
          </div>
          <div v-else class="empty">点击“本地运行”后即可在这里查看输出和报错。</div>
        </el-card>

        <el-card class="result-card" style="margin-top: 12px">
          <template #header>
            <div class="header">
              <div class="title">最近提交</div>
            </div>
          </template>

          <el-table :data="submissions" size="small" style="width: 100%" @row-click="onRowClick">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="status" label="状态" width="110" />
            <el-table-column prop="verdict" label="Verdict" width="100" />
            <el-table-column label="耗时(ms)" width="100">
              <template #default="{ row }">
                {{ displayNumber(row.time_ms) }}
              </template>
            </el-table-column>
            <el-table-column label="内存(KB)" width="110">
              <template #default="{ row }">
                {{ displayNumber(row.memory_kb) }}
              </template>
            </el-table-column>
          </el-table>

          <div v-if="!submissions.length" class="empty">
            暂无提交，写完代码后点击“提交”即可看到评测结果。
          </div>
        </el-card>
      </div>
    </div>

    <el-dialog v-model="codeDialogVisible" title="提交详情" width="720px">
      <div v-if="selectedSubmission">
        <div class="meta-line">
          <el-tag size="small">#{{ selectedSubmission.id }}</el-tag>
          <span>语言：{{ selectedSubmission.language }}</span>
          <span>Verdict：{{ selectedSubmission.verdict || '-' }}</span>
          <span>耗时：{{ displayNumber(selectedSubmission.time_ms) }} ms</span>
          <span>内存：{{ displayNumber(selectedSubmission.memory_kb) }} KB</span>
        </div>
        <el-input v-model="selectedSubmission.code" type="textarea" :rows="16" readonly class="code-view" />
      </div>
      <template #footer>
        <el-button @click="codeDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const route = useRoute()
const problemId = Number(route.params.id)
const contestId = route.query.contest_id ? Number(route.query.contest_id) : null
const teamId = route.query.team_id ? Number(route.query.team_id) : null
const activeTeamName = ref<string | null>(null)

interface ProblemDetail {
  id: number
  title?: string
  problem_title?: string
  statement: string
  input_desc?: string | null
  output_desc?: string | null
  time_limit_ms?: number
  memory_limit_mb?: number
}

interface RawTestcase {
  id: number
  input_data?: string
  expected_output?: string
  input?: string
  output?: string
  is_sample?: boolean
}

interface SampleView {
  id: number
  input: string
  output: string
}

interface Submission {
  id: number
  status: string
  verdict: string | null
  time_ms: number | null
  memory_kb: number | null
  language: string
  code: string
}

interface RunResult {
  verdict: string
  stdout: string
  stderr: string
  time_ms: number | null
  memory_kb: number | null
  message: string | null
}

const problem = ref<ProblemDetail | null>(null)
const samples = ref<SampleView[]>([])

const PYTHON_TEMPLATE = `print(input())
`

const CPP_TEMPLATE = `#include <iostream>
#include <cstdio>

using namespace std;

int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b;
    return 0;
}
`

const language = ref<'python3' | 'cpp17'>('python3')
const code = ref(PYTHON_TEMPLATE)
const runInput = ref('')
const expectedOutput = ref('')
const runResult = ref<RunResult | null>(null)
const running = ref(false)
const submissions = ref<Submission[]>([])
const submitting = ref(false)
let submissionsTimer: number | null = null
const codeDialogVisible = ref(false)
const selectedSubmission = ref<Submission | null>(null)

async function loadProblem() {
  const { data } = await api.get<ProblemDetail>(`/problems/${problemId}`)
  problem.value = data
}

async function loadSamples() {
  const { data } = await api.get<RawTestcase[]>(`/problems/${problemId}/testcases`, {
    params: { is_sample: true },
  })
  const list = Array.isArray(data) ? data : []
  const sampleList = list.filter(testcase => testcase.is_sample === true)
  const display = sampleList.length ? sampleList : list

  samples.value = display
    .map(testcase => {
      const input = testcase.input ?? testcase.input_data ?? ''
      const output = testcase.output ?? testcase.expected_output ?? ''
      return input || output
        ? {
            id: testcase.id,
            input,
            output,
          }
        : null
    })
    .filter((item): item is SampleView => item !== null)

  if (samples.value.length) {
    if (!runInput.value) {
      runInput.value = samples.value[0].input
    }
    if (!expectedOutput.value) {
      expectedOutput.value = samples.value[0].output
    }
  }
}

async function loadMySubmissions() {
  const params: Record<string, any> = { problem_id: problemId }
  if (contestId) params.contest_id = contestId
  const { data } = await api.get<Submission[]>('/submissions', { params })
  submissions.value = data
}

watch(
  language,
  (lang) => {
    const isDefaultOrEmpty = code.value.trim() === '' || code.value === PYTHON_TEMPLATE || code.value === CPP_TEMPLATE
    if (!isDefaultOrEmpty) return
    code.value = lang === 'python3' ? PYTHON_TEMPLATE : CPP_TEMPLATE
  },
  { immediate: false },
)

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
    const message = error?.response?.data?.detail || '运行失败，请稍后重试'
    ElMessage.error(message)
  } finally {
    running.value = false
  }
}

async function onSubmit() {
  if (!code.value.trim()) {
    ElMessage.warning('代码不能为空')
    return
  }
  if (contestId && !teamId) {
    ElMessage.warning('请先从竞赛详情页报名后再提交')
    return
  }

  submitting.value = true
  try {
    await api.post('/submissions', {
      problem_id: problemId,
      contest_id: contestId,
      team_id: teamId,
      language: language.value,
      code: code.value,
    })
    ElMessage.success('提交成功，评测结果稍后刷新')
    await loadMySubmissions()
  } catch (error: any) {
    const message = error?.response?.data?.error_detail || error?.response?.data?.detail || '提交失败，请稍后重试'
    ElMessage.error(message)
  } finally {
    submitting.value = false
  }
}

function onRowClick(row: Submission) {
  selectedSubmission.value = row
  codeDialogVisible.value = true
}

onMounted(async () => {
  await Promise.allSettled([loadProblem(), loadSamples(), loadMySubmissions(), loadActiveTeam()])
  submissionsTimer = window.setInterval(() => {
    loadMySubmissions()
  }, 5000)
})

onBeforeUnmount(() => {
  if (submissionsTimer !== null) {
    window.clearInterval(submissionsTimer)
    submissionsTimer = null
  }
})

async function loadActiveTeam() {
  if (!contestId) return
  try {
    const { data } = await api.get<{ team_id: number; team_name: string | null } | null>(`/me/contests/${contestId}/active_team`)
    if (data && typeof data.team_id === 'number') {
      activeTeamName.value = data.team_name || `队伍 #${data.team_id}`
    }
  } catch {
    // 忽略
  }
}

function displayNumber(value: number | null): string {
  if (value === null || value === undefined) return '--'
  return String(value)
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
</script>

<style scoped>
.page-wrap {
  width: 100%;
}

.page {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 2fr);
  gap: 16px;
}

.header {
  display: flex;
  flex-direction: column;
}

.debug-header {
  gap: 8px;
}

.title {
  font-weight: 600;
  font-size: 16px;
}

.title .id {
  margin-left: 8px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.section-title {
  margin: 12px 0 6px;
  font-weight: 600;
}

.paragraph {
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.sample {
  margin-top: 8px;
}

.sample-block {
  background: var(--el-fill-color-light);
  border-radius: 6px;
  padding: 8px;
}

.sample-label,
.run-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.sample-block pre,
.run-pre {
  margin: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
  font-size: 12px;
  white-space: pre-wrap;
}

.code-area :deep(textarea),
.code-view :deep(textarea) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

.run-meta,
.meta-line {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.run-message {
  margin-bottom: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
  font-size: 12px;
}

.run-block + .run-block {
  margin-top: 12px;
}

.run-pre {
  padding: 10px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  min-height: 72px;
}


.empty {
  padding: 12px;
  text-align: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.loading-text {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

@media (max-width: 960px) {
  .page {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
