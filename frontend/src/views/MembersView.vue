<template>
  <el-row :gutter="16">
    <el-col :span="10">
      <el-card>
        <template #header>添加成员</template>
        <el-form label-width="96px">
          <el-form-item label="Handle">
            <el-input v-model="form.handle" placeholder="例如 yzt" />
          </el-form-item>
          <el-form-item label="组别">
            <el-input v-model="form.group_name" placeholder="可选" />
          </el-form-item>
          <el-form-item label="梯队">
            <el-input-number v-model="form.tier" :min="1" :max="10" style="width: 100%" />
          </el-form-item>
          <el-form-item label="初始分">
            <el-input-number v-model="form.rating" :min="0" :max="4000" style="width: 100%" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="creating" @click="create">创建</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card style="margin-top: 16px">
        <template #header>能力画像</template>
        <el-form label-width="96px">
          <el-form-item label="成员ID">
            <el-input-number v-model="profileMemberId" :min="1" style="width: 100%" />
          </el-form-item>
          <el-form-item>
            <el-button :loading="loadingProfile" @click="loadProfile">查询</el-button>
          </el-form-item>
        </el-form>

        <div v-if="profile">
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="Handle">{{ profile.handle }}</el-descriptions-item>
            <el-descriptions-item label="Rating">{{ profile.rating }}</el-descriptions-item>
            <el-descriptions-item label="PK">{{ profile.pk_wins }}W/{{ profile.pk_draws }}D/{{ profile.pk_losses }}L ({{ profile.pk_total }})</el-descriptions-item>
            <el-descriptions-item label="提交">AC {{ profile.submissions_ac }} / {{ profile.submissions_total }}</el-descriptions-item>
            <el-descriptions-item label="面试均分">{{ profile.interview_avg_score ?? '-' }}</el-descriptions-item>
          </el-descriptions>

          <el-divider />
          <div>
            <el-tag type="success">竞技强度 {{ profile.competitive_strength }}</el-tag>
            <el-tag style="margin-left: 8px" type="info">稳定性 {{ profile.consistency }}</el-tag>
            <el-tag style="margin-left: 8px" type="warning">表达 {{ profile.communication }}</el-tag>
            <el-tag style="margin-left: 8px" type="primary">解题 {{ profile.problem_solving }}</el-tag>
          </div>

          <el-divider />
          <div>
            <div style="font-weight:600; margin-bottom:8px">推荐方向</div>
            <el-alert
              v-for="(d, idx) in profile.recommended_directions"
              :key="idx"
              :title="d.direction"
              :description="d.reason"
              type="info"
              show-icon
              style="margin-bottom: 8px"
            />
          </div>

          <div>
            <div style="font-weight:600; margin:12px 0 8px">提升计划</div>
            <el-timeline>
              <el-timeline-item v-for="(p, idx) in profile.improvement_plan" :key="idx">{{ p }}</el-timeline-item>
            </el-timeline>
          </div>
        </div>
      </el-card>
    </el-col>

    <el-col :span="14">
      <el-card>
        <template #header>
          <div style="display:flex; align-items:center; justify-content:space-between">
            <div>成员列表</div>
            <div>
              <el-button size="small" style="margin-left:8px" @click="load">刷新</el-button>
            </div>
          </div>
        </template>

        <el-table :data="members" style="width:100%" size="small" @row-click="onRow">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="handle" label="Handle" />
          <el-table-column prop="tier" label="梯队" width="80" />
          <el-table-column prop="rating" label="Rating" width="90" />
        </el-table>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { api } from '../api/client'

type Member = { id: number; lab_id: number; handle: string; tier: number; rating: number }
type Profile = any

const members = ref<Member[]>([])
const creating = ref(false)
const form = reactive({
  handle: '',
  group_name: '',
  tier: 1,
  rating: 1500,
})

async function load() {
  const { data } = await api.get('/members')
  members.value = data
}

async function create() {
  if (!form.handle.trim()) return
  creating.value = true
  try {
    await api.post('/members', {
      handle: form.handle,
      group_name: form.group_name || null,
      tier: form.tier,
      rating: form.rating,
      is_active: true,
    })
    form.handle = ''
    await load()
  } finally {
    creating.value = false
  }
}

const profileMemberId = ref(1)
const profile = ref<Profile | null>(null)
const loadingProfile = ref(false)

async function loadProfile() {
  loadingProfile.value = true
  try {
    const { data } = await api.get(`/members/${profileMemberId.value}/profile`)
    profile.value = data
  } finally {
    loadingProfile.value = false
  }
}

function onRow(row: Member) {
  profileMemberId.value = row.id
  loadProfile()
}

load()
</script>
