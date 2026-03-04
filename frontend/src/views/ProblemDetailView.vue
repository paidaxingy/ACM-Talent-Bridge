<template>
  <div class="page">
    <div class="left">
      <el-card class="statement-card">
        <template #header>
          <div class="header">
            <div class="title">
              {{ problem?.problem_title || '题目详情' }}
              <span v-if="problemId" class="id">#{{ problemId }}</span>
            </div>
            <div class="subtitle">参考牛客题面布局：左侧题面 + 右侧代码编辑与提交。</div>
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
            <el-col :span="12">
              <div class="sample-block">
                <div class="sample-label">样例输入</div>
                <pre>{{ s.input }}</pre>
              </div>
            </el-col>
            <el-col :span="12">
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
          <div class="header">
            <div class="title">代码编辑与提交</div>
            <div class="subtitle" v-if="contestId">
              竞赛 ID：{{ contestId }}
              <span v-if="teamId">｜队伍 ID：{{ teamId }}</span>
              <span v-else>｜个人参赛</span>
            </div>
          </div>
        </template>

        <el-form label-width="72px" size="small">
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
          <el-form-item>
            <el-button type="primary" :loading="submitting" @click="onSubmit">提交</el-button>
            <el-button style="margin-left: 8px" @click="loadMySubmissions">刷新结果</el-button>
          </el-form-item>
        </el-form>
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
        <span style="margin-left:8px">语言：{{ selectedSubmission.language }}</span>
        <span style="margin-left:12px">Verdict：{{ selectedSubmission.verdict || '-' }}</span>
        <span style="margin-left:12px">耗时：{{ displayNumber(selectedSubmission.time_ms) }} ms</span>
        <span style="margin-left:12px">内存：{{ displayNumber(selectedSubmission.memory_kb) }} KB</span>
      </div>
      <el-input v-model="selectedSubmission.code" type="textarea" :rows="16" readonly class="code-view" />
    </div>
    <template #footer>
      <el-button @click="codeDialogVisible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
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
  problem_title: string
  statement: string
  input_desc?: string | null
  output_desc?: string | null
}

// 后端返回的原始测试点结构（兼容 input_data/expected_output 与 input/output）
interface RawTestcase {
  id: number
  input_data?: string
  expected_output?: string
  input?: string
  output?: string
  is_sample?: boolean
}

// 前端展示用的样例结构
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
  // 优先使用 is_sample=true 的样例；如果后端没有打标，则退化为展示全部测试点
  const list = Array.isArray(data) ? data : []
  const sampleList = list.filter(tc => tc.is_sample === true)
  const display = sampleList.length ? sampleList : list

  samples.value = display
    .map(tc => {
      const input = tc.input ?? tc.input_data ?? ''
      const output = tc.output ?? tc.expected_output ?? ''
      return input || output
        ? {
            id: tc.id,
            input,
            output,
          }
        : null
    })
    .filter((x): x is SampleView => x !== null)
}

async function loadMySubmissions() {
  const params: Record<string, any> = { problem_id: problemId }
  if (contestId) params.contest_id = contestId
  const { data } = await api.get<Submission[]>('/submissions', { params })
  submissions.value = data
}

watch(
  language,
  (lang, prev) => {
    // 仅在代码区域还是默认模板或为空时，切换语言才自动填充对应模板，避免覆盖用户已编辑代码
    const isDefaultOrEmpty =
      code.value.trim() === '' ||
      code.value === PYTHON_TEMPLATE ||
      code.value === CPP_TEMPLATE

    if (!isDefaultOrEmpty) return

    if (lang === 'python3') {
      code.value = PYTHON_TEMPLATE
    } else if (lang === 'cpp17') {
      code.value = CPP_TEMPLATE
    }
  },
  { immediate: false }
)

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
  } catch (e: any) {
    const msg = e?.response?.data?.error_detail || e?.response?.data?.detail || '提交失败，请稍后重试'
    ElMessage.error(msg)
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
  // 简单轮询最近提交，用于自动刷新 verdict/status
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

function displayNumber(val: number | null): string {
  if (val === null || val === undefined) return '--'
  return String(val)
}
</script>

<style scoped>
.page {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 2fr);
  gap: 16px;
}

.header {
  display: flex;
  flex-direction: column;
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

.sample-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.sample-block pre {
  margin: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New',
    monospace;
  font-size: 12px;
  white-space: pre-wrap;
}

.code-area :deep(textarea) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New',
    monospace;
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

.meta-line {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.code-view :deep(textarea) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

@media (max-width: 960px) {
  .page {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>

