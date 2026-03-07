<template>
  <div class="page">
    <el-card class="page-card">
      <template #header>
        <div class="header">
          <div>
            <div class="eyebrow">Submission Timeline</div>
            <div class="title">我的提交</div>
            <div class="subtitle">按竞赛、题目和状态快速筛选最近评测记录，点击任意一行可查看提交代码。</div>
          </div>
          <div class="actions-panel">
            <div class="actions">
              <el-input
                v-model="filters.contestId"
                placeholder="竞赛 ID（可选）"
                size="small"
                clearable
                class="filter-control"
              />
              <el-input
                v-model="filters.problemId"
                placeholder="题目 ID（可选）"
                size="small"
                clearable
                class="filter-control"
              />
              <el-select
                v-model="filters.status"
                placeholder="状态"
                size="small"
                clearable
                class="status-control"
              >
                <el-option label="全部状态" value="" />
                <el-option label="评测中" value="pending" />
                <el-option label="完成" value="done" />
              </el-select>
              <el-button size="small" type="primary" :loading="loading" @click="load">
                刷新
              </el-button>
            </div>
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
      <div v-if="selectedSubmission" class="dialog-body">
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
  status: '' | 'pending' | 'done'
}>({
  contestId: '',
  problemId: '',
  status: '',
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
.page {
  width: 100%;
}

.page-card :deep(.el-card__header) {
  padding-bottom: 20px;
}

.header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #8a97aa;
}

.title {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 800;
  color: #314154;
}

.subtitle {
  margin-top: 8px;
  max-width: 560px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--el-text-color-secondary);
}

.actions-panel {
  padding: 12px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(111, 134, 214, 0.08), rgba(99, 183, 157, 0.08));
  border: 1px solid rgba(220, 227, 233, 0.84);
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-control {
  width: 160px;
}

.status-control {
  width: 140px;
}

.empty {
  padding: 28px;
  text-align: center;
  color: var(--el-text-color-secondary);
}

.dialog-body {
  display: grid;
  gap: 14px;
}

.meta-line {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(111, 134, 214, 0.08), rgba(215, 174, 106, 0.08));
  color: #516277;
}

.code-view :deep(.el-textarea__inner) {
  min-height: 360px;
  background: rgba(250, 252, 255, 0.88) !important;
}

.code-view :deep(textarea) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

@media (max-width: 900px) {
  .header {
    flex-direction: column;
  }

  .actions-panel {
    width: 100%;
  }

  .actions {
    flex-wrap: wrap;
  }

  .filter-control,
  .status-control {
    width: 100%;
  }
}
</style>
