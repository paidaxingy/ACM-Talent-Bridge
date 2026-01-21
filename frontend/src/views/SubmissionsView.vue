<template>
  <el-row :gutter="16">
    <el-col :span="10">
      <el-card>
        <template #header>提交代码（MVP 支持 Python3）</template>
        <el-form label-width="92px">
          <el-form-item label="Member ID">
            <el-input-number v-model="form.member_id" :min="1" style="width:100%" />
          </el-form-item>
          <el-form-item label="Problem ID">
            <el-input-number v-model="form.problem_id" :min="1" style="width:100%" />
          </el-form-item>
          <el-form-item label="Contest ID">
            <el-input-number v-model="form.contest_id" :min="1" style="width:100%" />
            <div style="font-size:12px;color:var(--el-text-color-secondary);margin-top:4px">不参赛可留空</div>
          </el-form-item>
          <el-form-item label="语言">
            <el-select v-model="form.language" style="width:100%">
              <el-option label="python3" value="python3" />
              <el-option label="cpp17" value="cpp17" />
            </el-select>
          </el-form-item>
          <el-form-item label="代码">
            <el-input v-model="form.code" type="textarea" :rows="10" placeholder="print(input())" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="submitting" @click="submit">提交</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>

    <el-col :span="14">
      <el-card>
        <template #header>
          <div style="display:flex; align-items:center; justify-content:space-between">
            <div>提交记录</div>
            <el-button size="small" @click="load">刷新</el-button>
          </div>
        </template>
        <el-table :data="subs" size="small" style="width:100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="member_id" label="Member" width="90" />
          <el-table-column prop="problem_id" label="Problem" width="90" />
          <el-table-column prop="language" label="Lang" width="90" />
          <el-table-column prop="status" label="Status" width="110" />
          <el-table-column prop="verdict" label="Verdict" width="90" />
          <el-table-column prop="time_ms" label="Time(ms)" width="90" />
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { api } from '../api/client'

const subs = ref<any[]>([])
const submitting = ref(false)
const form = reactive({
  member_id: 1,
  problem_id: 1,
  contest_id: undefined as number | undefined,
  language: 'python3',
  code: 'print(input())\n',
})

async function load() {
  const { data } = await api.get('/submissions')
  subs.value = data
}

async function submit() {
  if (!form.code.trim()) return
  submitting.value = true
  try {
    await api.post('/submissions', {
      member_id: form.member_id,
      problem_id: form.problem_id,
      contest_id: form.contest_id || null,
      language: form.language,
      code: form.code,
    })
    await load()
  } finally {
    submitting.value = false
  }
}

load()
</script>
