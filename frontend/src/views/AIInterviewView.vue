<template>
  <el-row :gutter="16">
    <el-col :span="10">
      <el-card>
        <template #header>创建面试 Session</template>
        <el-form label-width="96px">
          <el-form-item label="Member ID">
            <el-input-number v-model="form.member_id" :min="1" style="width:100%" />
          </el-form-item>
          <el-form-item label="目标方向">
            <el-input v-model="form.target_role" placeholder="可选" />
          </el-form-item>
          <el-form-item label="题目数">
            <el-input-number v-model="form.num_questions" :min="1" :max="20" style="width:100%" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="creating" @click="create">创建</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card style="margin-top:16px" v-if="selectedSession">
        <template #header>题目与作答</template>
        <el-alert type="info" show-icon :title="`Session #${selectedSession.id} (${selectedSession.status})`" />

        <el-divider />
        <div v-for="q in questions" :key="q.id" style="margin-bottom:12px">
          <el-card shadow="never">
            <div style="font-weight:600">Q{{ q.sort_order }}. {{ q.question }}</div>
            <div style="margin-top:8px">
              <el-input v-model="answers[q.id]" type="textarea" :rows="3" placeholder="输入回答..." />
              <div style="margin-top:8px;display:flex;gap:8px">
                <el-button size="small" type="primary" @click="submitAnswer(q.id)">提交并评估</el-button>
                <el-button size="small" @click="loadAnswers(q.id)">查看历史</el-button>
              </div>
              <el-table v-if="answerList[q.id]" :data="answerList[q.id]" size="small" style="margin-top:8px">
                <el-table-column prop="attempt" label="Attempt" width="90" />
                <el-table-column prop="status" label="Status" width="110" />
                <el-table-column prop="score" label="Score" width="90" />
              </el-table>
            </div>
          </el-card>
        </div>
      </el-card>
    </el-col>

    <el-col :span="14">
      <el-card>
        <template #header>
          <div style="display:flex; align-items:center; justify-content:space-between">
            <div>面试 Sessions</div>
            <el-button size="small" @click="loadSessions">刷新</el-button>
          </div>
        </template>
        <el-table :data="sessions" size="small" style="width:100%" @row-click="select">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="member_id" label="Member" width="90" />
          <el-table-column prop="status" label="Status" width="110" />
          <el-table-column prop="num_questions" label="N" width="70" />
          <el-table-column prop="target_role" label="Target" />
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { api } from '../api/client'

const sessions = ref<any[]>([])
const creating = ref(false)
const form = reactive({ member_id: 1, target_role: '', num_questions: 5 })

const selectedSession = ref<any | null>(null)
const questions = ref<any[]>([])
const answers = reactive<Record<number, string>>({})
const answerList = reactive<Record<number, any[]>>({})

async function loadSessions() {
  const { data } = await api.get('/ai/interviews/sessions', { params: { member_id: form.member_id } })
  sessions.value = data
}

async function create() {
  creating.value = true
  try {
    await api.post('/ai/interviews/sessions', {
      member_id: form.member_id,
      target_role: form.target_role || null,
      num_questions: form.num_questions,
    })
    await loadSessions()
  } finally {
    creating.value = false
  }
}

async function select(row: any) {
  selectedSession.value = row
  await loadQuestions(row.id)
}

async function loadQuestions(sessionId: number) {
  const { data } = await api.get(`/ai/interviews/sessions/${sessionId}/questions`)
  questions.value = data
}

async function submitAnswer(questionId: number) {
  await api.post(`/ai/interviews/questions/${questionId}/answers`, { answer: answers[questionId] || '' })
  await loadAnswers(questionId)
}

async function loadAnswers(questionId: number) {
  const { data } = await api.get(`/ai/interviews/questions/${questionId}/answers`)
  answerList[questionId] = data
}

loadSessions()
</script>
