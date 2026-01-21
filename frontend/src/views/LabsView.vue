<template>
  <el-row :gutter="16">
    <el-col :span="10">
      <el-card>
        <template #header>创建实验室</template>
        <el-form label-width="88px">
          <el-form-item label="名称">
            <el-input v-model="form.name" placeholder="例如 ACM Lab" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="form.description" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="creating" @click="create">创建</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>

    <el-col :span="14">
      <el-card>
        <template #header>
          <div style="display:flex; align-items:center; justify-content:space-between">
            <div>实验室列表</div>
            <el-button size="small" @click="load">刷新</el-button>
          </div>
        </template>
        <el-table :data="labs" style="width:100%" size="small">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="description" label="描述" />
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { api } from '../api/client'

type Lab = { id: number; name: string; description?: string }

const labs = ref<Lab[]>([])
const creating = ref(false)
const form = reactive({ name: '', description: '' })

async function load() {
  const { data } = await api.get('/labs')
  labs.value = data
}

async function create() {
  if (!form.name.trim()) return
  creating.value = true
  try {
    await api.post('/labs', { name: form.name, description: form.description || null })
    form.name = ''
    form.description = ''
    await load()
  } finally {
    creating.value = false
  }
}

load()
</script>
