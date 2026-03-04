<template>
  <div class="page">
    <el-card class="main-card" shadow="hover">
      <template #header>
        <div class="header">
          <div>
            <div class="title">{{ profile?.handle || '我的主页' }}</div>
            <div class="subtitle">能力画像 · 评级趋势 · 训练数据总览</div>
          </div>
          <el-button size="small" :loading="loading" @click="load">刷新</el-button>
        </div>
      </template>

      <div v-if="profile">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-card class="block-card" shadow="hover">
              <div class="block-title">基础信息</div>
              <el-descriptions :column="1" size="small" border>
                <el-descriptions-item label="Handle">{{ profile.handle }}</el-descriptions-item>
                <el-descriptions-item label="Rating">{{ profile.rating }}</el-descriptions-item>
                <el-descriptions-item label="梯队">{{ profile.tier }}</el-descriptions-item>
                <el-descriptions-item label="分组">{{ profile.group_name || '-' }}</el-descriptions-item>
              </el-descriptions>
              <div class="resume-section">
                <div class="block-title" style="margin-top: 12px">简历</div>
                <el-upload
                  v-if="!resumeUrl"
                  action=""
                  :auto-upload="false"
                  :show-file-list="false"
                  accept=".pdf,.doc,.docx"
                  :on-change="handleResumeChange"
                >
                  <el-button size="small">上传简历</el-button>
                  <template #tip>
                    <div class="el-upload__tip" style="font-size: 12px; color: #909399">支持 PDF/DOC/DOCX</div>
                  </template>
                </el-upload>
                <div v-else style="display: flex; gap: 8px; align-items: center">
                  <el-button size="small" type="success" @click="previewResume">查看简历</el-button>
                  <el-button size="small" type="danger" :loading="deleting" @click="deleteResume">删除</el-button>
                </div>
              </div>
            </el-card>
          </el-col>

          <el-col :span="8">
            <el-card class="block-card" shadow="hover">
              <div class="block-title">训练 & PK</div>
              <el-descriptions :column="1" size="small" border>
                <el-descriptions-item label="提交">
                  AC {{ profile.submissions_ac }} / {{ profile.submissions_total }}
                </el-descriptions-item>
                <el-descriptions-item label="参赛场次">
                  {{ profile.contests_registered }}
                </el-descriptions-item>
                <el-descriptions-item label="PK 战绩">
                  {{ profile.pk_wins }}W / {{ profile.pk_draws }}D / {{ profile.pk_losses }}L（共 {{ profile.pk_total }} 场）
                </el-descriptions-item>
                <el-descriptions-item label="近10场 PK 评分变化">
                  {{ profile.rating_trend_last10 >= 0 ? '+' : '' }}{{ profile.rating_trend_last10 }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>

          <el-col :span="8">
            <el-card class="block-card" shadow="hover">
              <div class="block-title">维度评分</div>
              <div class="metric">
                <span>竞技强度</span>
                <el-progress :percentage="profile.competitive_strength" :stroke-width="10" />
              </div>
              <div class="metric">
                <span>稳定性</span>
                <el-progress :percentage="profile.consistency" :stroke-width="10" status="success" />
              </div>
              <div class="metric">
                <span>表达</span>
                <el-progress :percentage="profile.communication" :stroke-width="10" status="warning" />
              </div>
              <div class="metric">
                <span>解题</span>
                <el-progress :percentage="profile.problem_solving" :stroke-width="10" status="exception" />
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16" style="margin-top: 16px">
          <el-col :span="12">
            <el-card class="block-card" shadow="hover">
              <div class="block-title">推荐方向</div>
              <div v-if="profile.recommended_directions.length">
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
              <div v-else class="empty">暂无推荐方向</div>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card class="block-card" shadow="hover">
              <div class="block-title">提升计划</div>
              <el-timeline v-if="profile.improvement_plan.length">
                <el-timeline-item v-for="(p, idx) in profile.improvement_plan" :key="idx">
                  {{ p }}
                </el-timeline-item>
              </el-timeline>
              <div v-else class="empty">暂无专项提升计划</div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <div v-else class="empty" v-if="!loading">
        当前账号还没有绑定成员档案，请让管理员在“成员管理”中为该用户名创建成员（handle = 用户名）。
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, apiBaseUrl } from '../api/client'

interface Profile {
  member_id: number
  handle: string
  rating: number
  tier: number
  group_name: string | null
  pk_total: number
  pk_wins: number
  pk_losses: number
  pk_draws: number
  submissions_total: number
  submissions_ac: number
  contests_registered: number
  interview_avg_score: number | null
  rating_trend_last10: number
  competitive_strength: number
  consistency: number
  communication: number
  problem_solving: number
  recommended_directions: { direction: string; reason: string }[]
  improvement_plan: string[]
}

const profile = ref<Profile | null>(null)
const loading = ref(false)
const uploading = ref(false)
const deleting = ref(false)
const resumeUrl = ref<string | null>(null)
const route = useRoute()
let refreshTimer: number | null = null

async function load() {
  loading.value = true
  try {
    const memberId = route.params.memberId as string | undefined
    let url = '/me/profile'
    if (memberId) {
      url = `/members/${Number(memberId)}/profile`
    }
    const { data } = await api.get<Profile>(url)
    profile.value = data
  } catch (e: any) {
    const msg = e?.response?.data?.detail || '加载失败'
    ElMessage.error(msg)
    profile.value = null
  } finally {
    loading.value = false
  }
}

async function loadResume() {
  try {
    const { data } = await api.get('/me/resume')
    resumeUrl.value = data.url
  } catch (e) {
    resumeUrl.value = null
  }
}

async function handleResumeChange(file: any) {
  const rawFile = file.raw
  if (!rawFile) return

  const isValid = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(rawFile.type)
  if (!isValid) {
    ElMessage.error('只支持 PDF/DOC/DOCX 格式')
    return
  }

  uploading.value = true
  const formData = new FormData()
  formData.append('file', rawFile)
  try {
    await api.post('/me/resume', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    await loadResume()
    ElMessage.success('上传成功')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

async function deleteResume() {
  try {
    await ElMessageBox.confirm('确定删除简历？', '提示', { type: 'warning' })
  } catch {
    return
  }

  deleting.value = true
  try {
    await api.delete('/me/resume')
    resumeUrl.value = null
    ElMessage.success('已删除')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  } finally {
    deleting.value = false
  }
}

function previewResume() {
  if (resumeUrl.value) {
    const baseUrl = apiBaseUrl()
    window.open(baseUrl + resumeUrl.value, '_blank')
  }
}

// 自动刷新：每30秒刷新一次（仅自己的主页）
onMounted(() => {
  load()
  loadResume()
  if (!route.params.memberId) {
    // 只有查看自己的主页时才自动刷新
    refreshTimer = window.setInterval(() => {
      load()
    }, 30000) // 30秒
  }
})

onBeforeUnmount(() => {
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.page {
  padding: 8px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  font-weight: 600;
  font-size: 16px;
}

.subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.block-card {
  margin-bottom: 16px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  border-radius: 8px;
}

.block-card:hover {
  transform: translateY(-2px);
}

.block-title {
  font-weight: 600;
  margin-bottom: 12px;
  font-size: 15px;
  color: #303133;
}

.metric {
  margin-bottom: 8px;
}

.metric span {
  display: inline-block;
  width: 72px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.empty {
  padding: 16px;
  text-align: center;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.resume-section {
  margin-top: 12px;
}
</style>

