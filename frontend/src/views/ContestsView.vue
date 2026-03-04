<template>
  <div class="page">
    <!-- 上：创建竞赛 -->
    <el-card>
      <template #header>创建竞赛</template>
      <el-form label-width="92px">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.contest_type" style="width: 100%">
            <el-option label="training" value="training" />
            <el-option label="selection" value="selection" />
            <el-option label="mock" value="mock" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="form.timeRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="题目">
          <el-select
            v-model="form.problemIds"
            multiple
            filterable
            placeholder="从已有题目中选择"
            style="width: 100%"
          >
            <el-option
              v-for="p in problems"
              :key="p.id"
              :label="`#${p.id} ${p.title}`"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="creating" @click="create">创建</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 下：竞赛列表 -->
    <el-card style="margin-top: 16px">
      <template #header>
        <div class="list-header">
          <div>竞赛列表</div>
          <el-button size="small" @click="load">刷新</el-button>
        </div>
      </template>
      <el-table :data="contests" size="small" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="contest_type" label="类型" width="90" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            {{ statusText(row.status) }}
          </template>
        </el-table-column>
        <el-table-column prop="start_at" label="开始时间" width="150">
          <template #default="{ row }">
            {{ formatTime(row.start_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_at" label="结束时间" width="150">
          <template #default="{ row }">
            {{ formatTime(row.end_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="openEditTime(row)">修改时间</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="editDialogVisible" title="修改比赛时间" width="420px">
      <div v-if="!editingContest">请选择要编辑的比赛</div>
      <div v-else>
        <div style="margin-bottom:8px; font-size:13px">
          比赛：<strong>#{{ editingContest.id }} {{ editingContest.name }}</strong>
        </div>
        <el-form label-width="88px">
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="editTimeRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              style="width: 100%"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingEdit" @click="saveEditTime">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const contests = ref<any[]>([])
const creating = ref(false)
const form = reactive({
  name: '',
  contest_type: 'training',
  timeRange: [] as [Date, Date] | [],
  problemIds: [] as number[],
})

const problems = ref<{ id: number; title: string }[]>([])

const editDialogVisible = ref(false)
const editingContest = ref<any | null>(null)
const editTimeRange = ref<[Date, Date] | []>([])
const savingEdit = ref(false)

async function load() {
  const { data } = await api.get('/contests')
  contests.value = data
}

async function loadProblems() {
  const { data } = await api.get('/problems')
  problems.value = data.map((p: any) => ({ id: p.id, title: p.title }))
}

function formatTime(t: string | null) {
  if (!t) return ''
  return dayjs(t).format('YYYY-MM-DD HH:mm')
}

function statusText(status: string) {
  switch (status) {
    case 'draft':
      return '草稿'
    case 'published':
      return '未开始'
    case 'running':
      return '进行中'
    case 'ended':
      return '已结束'
    default:
      return status || '未知'
  }
}

async function create() {
  if (!form.name.trim()) return
  if (!(Array.isArray(form.timeRange) && form.timeRange.length === 2)) {
    ElMessage.warning('请先设置开始/结束时间')
    return
  }
  creating.value = true
  try {
    const [start_at, end_at] =
      Array.isArray(form.timeRange) && form.timeRange.length === 2 ? form.timeRange : [null, null]

    const { data: created } = await api.post('/contests', {
      name: form.name,
      contest_type: form.contest_type,
      description: null,
      start_at,
      end_at,
    })

    const contestId = created.id
    if (Array.isArray(form.problemIds) && form.problemIds.length) {
      let order = 1
      for (const pid of form.problemIds) {
        await api.post(`/contests/${contestId}/problems`, {
          problem_id: pid,
          sort_order: order++,
          score: 100,
        })
      }
    }

    ElMessage.success('竞赛已创建')
    form.name = ''
    form.timeRange = []
    form.problemIds = []
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.response?.data?.error_detail || e?.message || '创建失败'
    ElMessage.error(typeof msg === 'string' ? msg : '创建失败')
  } finally {
    creating.value = false
    // 无论创建/挂题是否报错，最终都刷新列表，避免页面“看起来没变化”
    await load()
  }
}

load()
loadProblems()

function openEditTime(row: any) {
  editingContest.value = row
  const start = row.start_at ? new Date(row.start_at) : null
  const end = row.end_at ? new Date(row.end_at) : null
  if (start && end) {
    editTimeRange.value = [start, end]
  } else {
    editTimeRange.value = []
  }
  editDialogVisible.value = true
}

async function saveEditTime() {
  if (!editingContest.value) return
  if (!(Array.isArray(editTimeRange.value) && editTimeRange.value.length === 2)) {
    ElMessage.warning('请先选择开始和结束时间')
    return
  }
  const id = Number(editingContest.value.id)
  if (!Number.isFinite(id)) return
  savingEdit.value = true
  try {
    const [start_at, end_at] = editTimeRange.value
    await api.patch(`/contests/${id}`, { start_at, end_at })
    ElMessage.success('时间已更新')
    editDialogVisible.value = false
    editingContest.value = null
    editTimeRange.value = []
    await load()
  } finally {
    savingEdit.value = false
  }
}
</script>

<style scoped>
.page {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
