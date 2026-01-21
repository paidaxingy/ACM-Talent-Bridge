<template>
  <el-row :gutter="16">
    <el-col :span="10">
      <el-card>
        <template #header>
          <div class="header">
            <div class="title">我的队伍</div>
            <div class="subtitle">参考牛客团队页：支持创建 / 加入 / 退出队伍。</div>
          </div>
        </template>

        <div v-if="myTeams.length">
          <el-timeline>
            <el-timeline-item v-for="t in myTeams" :key="t.team_id">
              <div class="team-item">
                <div class="team-header">
                  <div>
                    <div class="team-name">{{ t.team_name || `队伍 #${t.team_id}` }}</div>
                    <div class="team-id">队伍 ID：{{ t.team_id }}</div>
                  </div>
                  <div class="team-actions">
                    <el-button size="small" @click="copyTeamId(t.team_id)">复制队伍 ID</el-button>
                    <el-button size="small" text @click="copyInvite(t)">复制邀请文案</el-button>
                  </div>
                </div>
                <div class="team-members">
                  队员：
                  <span v-for="(m, idx) in t.team_members" :key="m.user_id">
                    {{ m.username }}<span v-if="idx < t.team_members.length - 1">、</span>
                  </span>
                </div>
                <el-button size="small" type="danger" plain @click="leave(t.team_id)">退出队伍</el-button>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
        <div v-else class="empty">
          你当前还没有加入任何队伍，可以在右侧创建一个新队伍或加入已有队伍。
        </div>
      </el-card>
    </el-col>

    <el-col :span="14">
      <el-card>
        <template #header>创建队伍</template>
        <el-form label-width="80px" size="small">
          <el-form-item label="队伍名称">
            <el-input v-model="createForm.team_name" maxlength="32" show-word-limit />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="creating" @click="create">创建并加入</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card style="margin-top: 16px">
        <template #header>加入队伍</template>
        <el-form label-width="80px" size="small">
          <el-form-item label="队伍 ID">
            <el-input v-model="joinForm.teamId" placeholder="由队友提供队伍 ID" />
          </el-form-item>
          <el-form-item>
            <el-button :loading="joining" type="primary" @click="join">加入</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

interface TeamMember {
  user_id: number
  username: string
}

interface MyTeam {
  team_id: number
  team_name: string | null
  team_members: TeamMember[]
}

const myTeams = ref<MyTeam[]>([])

const creating = ref(false)
const joining = ref(false)

const createForm = reactive({
  team_name: '',
})

const joinForm = reactive({
  teamId: '',
})

async function loadMyTeams() {
  const { data } = await api.get<MyTeam[]>('/me/teams')
  myTeams.value = data
}

async function create() {
  creating.value = true
  try {
    await api.post('/teams', { team_name: createForm.team_name || null })
    ElMessage.success('创建队伍成功')
    createForm.team_name = ''
    await loadMyTeams()
  } catch (e: any) {
    const msg = e?.response?.data?.error_detail || e?.response?.data?.detail || '创建队伍失败'
    ElMessage.error(msg)
  } finally {
    creating.value = false
  }
}

async function join() {
  if (!joinForm.teamId.trim()) {
    ElMessage.warning('请输入队伍 ID')
    return
  }
  const id = Number(joinForm.teamId)
  if (!Number.isFinite(id) || id <= 0) {
    ElMessage.warning('请输入合法的队伍 ID（纯数字）')
    return
  }
  joining.value = true
  try {
    await api.post(`/teams/${id}/join`)
    ElMessage.success('加入队伍成功')
    joinForm.teamId = ''
    await loadMyTeams()
  } catch (e: any) {
    const msg = e?.response?.data?.error_detail || e?.response?.data?.detail || '加入队伍失败'
    ElMessage.error(msg)
  } finally {
    joining.value = false
  }
}

async function leave(teamId: number) {
  try {
    await api.post(`/teams/${teamId}/leave`)
    ElMessage.success('已退出队伍')
    await loadMyTeams()
  } catch (e: any) {
    const msg = e?.response?.data?.error_detail || e?.response?.data?.detail || '退出队伍失败'
    ElMessage.error(msg)
  }
}

function copyTeamId(teamId: number) {
  navigator.clipboard
    .writeText(String(teamId))
    .then(() => {
      ElMessage.success('已复制队伍 ID')
    })
    .catch(() => {
      ElMessage.error('复制失败，请手动选择队伍 ID 复制')
    })
}

function copyInvite(team: MyTeam) {
  const name = team.team_name || `队伍 #${team.team_id}`
  const text = `队伍「${name}」（ID: ${team.team_id}）。在 ACM Talent Bridge 打开 /teams 页面，输入队伍 ID 加入队伍。`
  navigator.clipboard
    .writeText(text)
    .then(() => {
      ElMessage.success('已复制邀请文案')
    })
    .catch(() => {
      ElMessage.error('复制失败，请手动复制邀请信息')
    })
}

onMounted(loadMyTeams)
</script>

<style scoped>
.header .title {
  font-weight: 600;
}

.header .subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.team-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.team-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.team-name {
  font-weight: 600;
}

.team-id {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.team-members {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.empty {
  padding: 16px;
  text-align: center;
  color: var(--el-text-color-secondary);
}
</style>

