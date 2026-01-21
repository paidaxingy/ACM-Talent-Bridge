<template>
  <el-row :gutter="16">
    <el-col :span="10">
      <el-card>
        <template #header>创建题目</template>
        <el-form label-width="92px">
          <el-form-item label="标题">
            <el-input v-model="form.title" />
          </el-form-item>
          <el-form-item label="题面">
            <el-input v-model="form.statement" type="textarea" :rows="4" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="creating" @click="create">创建</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card style="margin-top: 16px">
        <template #header>测试点（样例/隐藏）</template>
        <el-form label-width="92px" size="small">
          <el-form-item label="题目 ID">
            <el-input-number v-model="tcForm.problemId" :min="1" style="width: 100%" />
          </el-form-item>
          <el-form-item label="输入">
            <el-input v-model="tcForm.input_data" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="期望输出">
            <el-input v-model="tcForm.expected_output" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="样例">
            <el-switch v-model="tcForm.is_sample" />
          </el-form-item>
          <el-form-item label="顺序">
            <el-input-number v-model="tcForm.sort_order" :min="1" style="width: 100%" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="addingTc" @click="addTestcase">添加测试点</el-button>
            <el-button style="margin-left:8px" :loading="loadingTcs" @click="loadTestcases">刷新测试点</el-button>
          </el-form-item>
        </el-form>

        <el-table v-if="testcases.length" :data="testcases" size="small" style="width:100%; margin-top:8px">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="sort_order" label="序号" width="70" />
          <el-table-column prop="is_sample" label="样例" width="70">
            <template #default="{ row }">
              <el-tag size="small" :type="row.is_sample ? 'success' : 'info'">{{ row.is_sample ? '是' : '否' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="input_data" label="输入" />
          <el-table-column prop="expected_output" label="输出" />
          <el-table-column label="操作" width="110">
            <template #default="{ row }">
              <el-button size="small" type="danger" @click="deleteTc(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-else class="empty-hint">输入题目 ID 后点击刷新，可查看/新增测试点</div>
      </el-card>
    </el-col>

    <el-col :span="14">
      <el-card>
        <template #header>
          <div style="display:flex; align-items:center; justify-content:space-between">
            <div>题库</div>
            <el-button size="small" @click="load">刷新</el-button>
          </div>
        </template>
        <el-table :data="problems" size="small" style="width:100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="title" label="标题">
            <template #default="{ row }">
              <el-link type="primary" @click="goProblem(row)">{{ row.title }}</el-link>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="110">
            <template #default="{ row }">
              <el-button size="small" type="danger" @click="deleteProblem(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { api } from '../api/client'

const router = useRouter()

const problems = ref<any[]>([])
const creating = ref(false)
const form = reactive({ title: '', statement: '' })

const testcases = ref<any[]>([])
const loadingTcs = ref(false)
const addingTc = ref(false)
const tcForm = reactive({
  problemId: null as number | null,
  input_data: '',
  expected_output: '',
  is_sample: true,
  sort_order: 1,
})

async function load() {
  const { data } = await api.get('/problems')
  problems.value = data
}

function goProblem(row: any) {
  const id = Number(row?.id)
  if (!Number.isFinite(id) || id <= 0) return
  router.push({ path: `/problems/${id}` })
}

async function create() {
  if (!form.title.trim() || !form.statement.trim()) return
  creating.value = true
  try {
    await api.post('/problems', {
      title: form.title,
      statement: form.statement,
      input_desc: null,
      output_desc: null,
      time_limit_ms: 2000,
      memory_limit_mb: 256,
    })
    form.title = ''
    form.statement = ''
    await load()
  } finally {
    creating.value = false
  }
}

async function loadTestcases() {
  if (!tcForm.problemId) return
  loadingTcs.value = true
  try {
    const { data } = await api.get(`/problems/${tcForm.problemId}/testcases`)
    testcases.value = data
  } finally {
    loadingTcs.value = false
  }
}

async function addTestcase() {
  if (!tcForm.problemId) return
  if (!tcForm.input_data.trim() && !tcForm.expected_output.trim()) return
  addingTc.value = true
  try {
    await api.post(`/problems/${tcForm.problemId}/testcases`, {
      input_data: tcForm.input_data,
      expected_output: tcForm.expected_output,
      is_sample: tcForm.is_sample,
      sort_order: tcForm.sort_order || 1,
    })
    await loadTestcases()
  } finally {
    addingTc.value = false
  }
}

async function deleteProblem(row: any) {
  const id = Number(row?.id)
  if (!Number.isFinite(id) || id <= 0) return
  try {
    await ElMessageBox.confirm(`确认删除题目 #${id} 吗？该题下测试点也会一起删除。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await api.delete(`/problems/${id}`)
  ElMessage.success('已删除题目')
  // 如果正在查看该题测试点，顺带清空
  if (tcForm.problemId === id) {
    tcForm.problemId = null
    testcases.value = []
  }
  await load()
}

async function deleteTc(row: any) {
  const pid = tcForm.problemId
  const tcid = Number(row?.id)
  if (!pid || !Number.isFinite(tcid) || tcid <= 0) return
  try {
    await ElMessageBox.confirm(`确认删除测试点 #${tcid} 吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await api.delete(`/problems/${pid}/testcases/${tcid}`)
  ElMessage.success('已删除测试点')
  await loadTestcases()
}

load()
</script>

<style scoped>
.empty-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: center;
}
</style>
