<template>
  <el-card>
    <template #header>
      <div class="header">
        <div>
          <div class="title">我的提交</div>
          <div class="subtitle">按竞赛 / 题目 / 状态快速筛选最近的评测记录。</div>
        </div>
        <div class="actions">
          <el-input
            v-model="filters.contestId"
            placeholder="竞赛 ID（可选）"
            size="small"
            style="width: 160px"
            clearable
          />
          <el-input
            v-model="filters.problemId"
            placeholder="题目 ID（可选）"
            size="small"
            style="width: 160px; margin-left: 8px"
            clearable
          />
          <el-select
            v-model="filters.status"
            placeholder="状态"
            size="small"
            style="width: 140px; margin-left: 8px"
            clearable
          >
            <el-option label="全部状态" :value="undefined" />
            <el-option label="评测中" value="pending" />
            <el-option label="完成" value="done" />
          </el-select>
          <el-button size="small" type="primary" :loading="loading" style="margin-left: 8px" @click="load">
            刷新
          </el-button>
        </div>
      </div>
    </template>

    <el-table :data="rows" size="small" style="width: 100%" @row-click="onRowClick">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="contest_id" label="Contest" width="90" />
      <el-table-column prop="problem_id" label="Problem" width="90" />
      <el-table-column prop="language" label="语言" width="90" />
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

    <div v-if="!rows.length && !loading" class="empty">
      暂无提交记录，去任意题面页写一发代码试试吧～
    </div>
  </el-card>

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
import { reactive, ref } from 'vue'
import { api } from '../api/client'

interface SubmissionRow {
  id: number
  contest_id: number | null
  problem_id: number
  language: string
  code: string
  status: string
  verdict: string | null
  time_ms: number | null
  memory_kb: number | null
}

const rows = ref<SubmissionRow[]>([])
const loading = ref(false)
const codeDialogVisible = ref(false)
const selectedSubmission = ref<SubmissionRow | null>(null)

const filters = reactive<{
  contestId?: string
  problemId?: string
  status?: 'pending' | 'done'
}>({
  contestId: '',
  problemId: '',
  status: undefined,
})

async function load() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (filters.contestId) params.contest_id = Number(filters.contestId)
    if (filters.problemId) params.problem_id = Number(filters.problemId)
    if (filters.status) params.status = filters.status
    const { data } = await api.get<SubmissionRow[]>('/submissions', { params })
    rows.value = data
  } finally {
    loading.value = false
  }
}

function onRowClick(row: SubmissionRow) {
  selectedSubmission.value = row
  codeDialogVisible.value = true
}

function displayNumber(val: number | null): string {
  if (val === null || val === undefined) return '--'
  return String(val)
}

load()
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.title {
  font-weight: 600;
}

.subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.actions {
  display: flex;
  align-items: center;
}

.empty {
  padding: 24px;
  text-align: center;
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
</style>

