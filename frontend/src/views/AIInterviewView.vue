<template>
  <el-row :gutter="16">
    <el-col :span="8">
      <el-card>
        <template #header>开始聊天面试</template>
        <el-form label-width="96px">
          <el-form-item label="简历状态">
            <el-tag :type="resumeReady ? 'success' : 'danger'">
              {{ resumeReady ? '已上传 PDF' : '未上传 PDF' }}
            </el-tag>
          </el-form-item>
          <el-form-item label="目标方向">
            <el-input v-model="form.target_role" placeholder="例如：后端开发 / 算法工程师（可选）" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="creating" :disabled="!resumeReady" @click="startSession">开始面试</el-button>
          </el-form-item>
        </el-form>
        <el-alert
          v-if="!resumeReady"
          type="warning"
          :closable="false"
          title="请先在我的主页上传 PDF 简历后再开始 AI 面试"
        />
      </el-card>

      <el-card style="margin-top:16px">
        <template #header>
          <div style="display:flex; align-items:center; justify-content:space-between">
            <div>我的面试会话</div>
            <el-button size="small" @click="loadChatSessions">刷新</el-button>
          </div>
        </template>
        <el-table :data="chatSessions" size="small" style="width:100%" @row-click="selectSession">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="status" label="状态" width="100" />
          <el-table-column prop="target_role" label="方向" />
        </el-table>
      </el-card>
    </el-col>

    <el-col :span="16">
      <el-card v-if="activeSession">
        <template #header>
          <div style="display:flex; align-items:center; justify-content:space-between">
            <div>Session #{{ activeSession.id }}</div>
            <div style="display:flex; gap:8px; align-items:center">
              <el-tag type="info">{{ activeSession.status }}</el-tag>
              <el-tag type="primary">总分：{{ chatSummary?.total_score ?? '--' }}</el-tag>
            </div>
          </div>
        </template>
        <div ref="chatContainerRef" class="chat-container">
          <div
            v-for="msg in messages"
            :key="msg.id"
            :class="['chat-row', msg.role === 'candidate' ? 'chat-row-right' : 'chat-row-left']"
          >
            <div :class="['chat-bubble', msg.role === 'candidate' ? 'bubble-candidate' : 'bubble-interviewer']">
              <div class="bubble-header">
                <span>{{ msg.role === 'candidate' ? '我' : 'AI 面试官' }}</span>
                <span class="bubble-round">第 {{ msg.round_no }} 轮</span>
              </div>
              <div class="bubble-content">
                <template v-if="msg.isThinking">
                  <span class="thinking-text">AI 正在思考</span>
                  <span class="thinking-dots" aria-hidden="true">
                    <i></i><i></i><i></i>
                  </span>
                </template>
                <template v-else>
                  {{ msg.role === 'interviewer' ? normalizeInterviewerContent(msg.content) : msg.content }}
                </template>
              </div>
              <div v-if="msg.role === 'interviewer' && !msg.isThinking" class="bubble-meta">
                难度：{{ msg.difficulty || 'medium' }}
              </div>
              <div v-if="msg.role === 'candidate' && msg.isPending" class="bubble-meta">
                正在发送并等待面试官回复...
              </div>
              <div v-if="msg.role === 'candidate' && !msg.isPending" class="bubble-evaluation">
                <div><strong>本轮得分：</strong>{{ msg.score ?? '--' }}</div>
                <el-collapse v-model="expandedEvaluationIds" class="eval-collapse" accordion>
                  <el-collapse-item title="查看本轮评估详情" :name="String(msg.id)" class="eval-collapse-item">
                    <div><strong>标准答案：</strong>{{ msg.standard_answer || '-' }}</div>
                    <div><strong>优点：</strong>{{ msg.strengths || '-' }}</div>
                    <div><strong>不足：</strong>{{ msg.weaknesses || '-' }}</div>
                    <div><strong>建议：</strong>{{ msg.suggestions || '-' }}</div>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </div>
          </div>
        </div>

        <el-divider />
        <el-input
          v-model="answerInput"
          type="textarea"
          :rows="4"
          placeholder="请输入你的回答..."
          :disabled="activeSession.status === 'completed'"
          @keydown.enter="onAnswerKeydown"
        />
        <div style="margin-top:10px; display:flex; gap:8px">
          <el-button type="primary" :loading="replying" :disabled="!canReply" @click="sendReply">
            {{ replying ? '等待面试官...' : '发送回答' }}
          </el-button>
          <el-button :disabled="activeSession.status === 'completed'" @click="finishSession">
            结束面试
          </el-button>
          <el-button @click="loadSummary(activeSession.id)">刷新总分</el-button>
        </div>
      </el-card>
      <el-empty v-else description="请先创建或选择一个面试 Session" />
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

type ChatSession = {
  id: number
  member_id: number
  status: string
  num_rounds: number
  target_role: string | null
}

type ChatMessage = {
  id: number | string
  session_id: number
  round_no: number
  role: 'interviewer' | 'candidate'
  content: string
  difficulty: string | null
  score: number | null
  standard_answer: string | null
  strengths: string | null
  weaknesses: string | null
  suggestions: string | null
  isThinking?: boolean
  isPending?: boolean
}

type ChatSummaryRound = {
  round_no: number
  question: string
  difficulty: string | null
  answer: string | null
  score: number | null
  standard_answer: string | null
  strengths: string | null
  weaknesses: string | null
  suggestions: string | null
}

type ChatSummary = {
  session_id: number
  status: string
  total_rounds: number
  answered_rounds: number
  total_score: number
  rounds: ChatSummaryRound[]
}

const chatSessions = ref<ChatSession[]>([])
const creating = ref(false)
const replying = ref(false)
const form = reactive({ target_role: '' })
const activeSession = ref<ChatSession | null>(null)
const messages = ref<ChatMessage[]>([])
const chatSummary = ref<ChatSummary | null>(null)
const answerInput = ref('')
const resumeReady = ref(false)
const chatContainerRef = ref<HTMLElement | null>(null)
const expandedEvaluationIds = ref<string[]>([])
const thinkingMessageId = ref<string | null>(null)

const canReply = computed(() => {
  return !!activeSession.value && !replying.value && activeSession.value.status !== 'completed' && !!answerInput.value.trim()
})

function scrollToBottom() {
  nextTick(() => {
    if (chatContainerRef.value) {
      chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight
    }
  })
}

async function loadResumeStatus() {
  try {
    const { data } = await api.get('/me/resume')
    const url = String(data?.url || '')
    resumeReady.value = !!url && url.toLowerCase().endsWith('.pdf')
  } catch {
    resumeReady.value = false
  }
}

async function loadChatSessions() {
  try {
    const { data } = await api.get('/ai/interviews/chat/sessions')
    chatSessions.value = data
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载面试会话失败')
  }
}

async function startSession() {
  creating.value = true
  try {
    const { data } = await api.post('/ai/interviews/chat/sessions/start', {
      target_role: form.target_role || null,
    })
    ElMessage.success('面试已开始')
    await loadChatSessions()
    await selectSession(data)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '创建面试失败')
  } finally {
    creating.value = false
  }
}

async function selectSession(row: ChatSession) {
  activeSession.value = row
  answerInput.value = ''
  expandedEvaluationIds.value = []
  thinkingMessageId.value = null
  await Promise.all([loadMessages(row.id), loadSummary(row.id)])
  scrollToBottom()
}

async function loadMessages(sessionId: number) {
  try {
    const { data } = await api.get(`/ai/interviews/chat/sessions/${sessionId}/messages`)
    messages.value = data
    thinkingMessageId.value = null
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载聊天记录失败')
  }
}

async function loadSummary(sessionId: number) {
  try {
    const { data } = await api.get(`/ai/interviews/chat/sessions/${sessionId}/summary`)
    chatSummary.value = data
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '加载面试汇总失败')
  }
}

async function sendReply() {
  if (!activeSession.value || !answerInput.value.trim()) return
  const sessionId = activeSession.value.id
  const sentAnswer = answerInput.value.trim()
  const tempId = `temp-${Date.now()}`
  const tempMessage: ChatMessage = {
    id: tempId,
    session_id: sessionId,
    round_no: inferCurrentRoundNo(),
    role: 'candidate',
    content: sentAnswer,
    difficulty: null,
    score: null,
    standard_answer: null,
    strengths: null,
    weaknesses: null,
    suggestions: null,
    isPending: true,
  }

  messages.value.push(tempMessage)
  const tempThinkingId = addThinkingBubble(sessionId, tempMessage.round_no + 1)
  answerInput.value = ''
  scrollToBottom()

  replying.value = true
  try {
    const { data } = await api.post(`/ai/interviews/chat/sessions/${sessionId}/reply`, {
      answer: sentAnswer,
    })
    removeThinkingBubble(tempThinkingId)
    activeSession.value = data.session
    replaceTempMessage(tempId, data.candidate_message)
    if (data.next_question) {
      messages.value.push(data.next_question)
    }
    await Promise.all([loadSummary(sessionId), loadChatSessions()])
    scrollToBottom()
  } catch (e: any) {
    messages.value = messages.value.filter((m) => m.id !== tempId)
    removeThinkingBubble(tempThinkingId)
    answerInput.value = sentAnswer
    ElMessage.error(extractErrorMessage(e))
  } finally {
    replying.value = false
  }
}

async function finishSession() {
  if (!activeSession.value) return
  try {
    const { data } = await api.post(`/ai/interviews/chat/sessions/${activeSession.value.id}/finish`)
    chatSummary.value = data
    activeSession.value.status = 'completed'
    await loadChatSessions()
    ElMessage.success('面试已结束')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '结束面试失败')
  }
}

loadResumeStatus()
loadChatSessions()

function normalizeInterviewerContent(content: string) {
  const text = String(content || '').trim()
  if (!text) return ''

  const parseQuestion = (raw: string): string | null => {
    try {
      const obj = JSON.parse(raw)
      if (obj && typeof obj === 'object' && typeof (obj as any).question === 'string') {
        const q = String((obj as any).question).trim()
        return q || null
      }
      return null
    } catch {
      return null
    }
  }

  const direct = parseQuestion(text)
  if (direct) return direct

  const fenceMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/i)
  if (fenceMatch?.[1]) {
    const fromFence = parseQuestion(fenceMatch[1].trim())
    if (fromFence) return fromFence
  }

  return text
}

function inferCurrentRoundNo() {
  if (!messages.value.length) return 1
  const last = messages.value[messages.value.length - 1]
  if (last.role === 'interviewer') return last.round_no
  return last.round_no + 1
}

function replaceTempMessage(tempId: string, message: ChatMessage) {
  const idx = messages.value.findIndex((m) => m.id === tempId)
  if (idx >= 0) {
    messages.value[idx] = { ...message, isPending: false }
  } else {
    messages.value.push({ ...message, isPending: false })
  }
}

function onAnswerKeydown(event: KeyboardEvent) {
  if (event.shiftKey) return
  event.preventDefault()
  if (canReply.value) {
    void sendReply()
  }
}

function addThinkingBubble(sessionId: number, roundNo: number) {
  const id = `thinking-${Date.now()}`
  const msg: ChatMessage = {
    id,
    session_id: sessionId,
    round_no: roundNo,
    role: 'interviewer',
    content: '',
    difficulty: null,
    score: null,
    standard_answer: null,
    strengths: null,
    weaknesses: null,
    suggestions: null,
    isThinking: true,
  }
  messages.value.push(msg)
  thinkingMessageId.value = id
  scrollToBottom()
  return id
}

function removeThinkingBubble(id: string | null) {
  if (!id) return
  messages.value = messages.value.filter((m) => m.id !== id)
  if (thinkingMessageId.value === id) {
    thinkingMessageId.value = null
  }
}

function extractErrorMessage(e: any) {
  const detail = e?.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail) && detail.length) return String(detail[0]?.msg || '提交回答失败')
  if (typeof e?.message === 'string' && e.message.trim()) return e.message
  return '提交回答失败，请稍后重试'
}
</script>

<style scoped>
.chat-container {
  max-height: 520px;
  overflow-y: auto;
  padding: 8px;
  border-radius: 10px;
  background: var(--el-fill-color-lighter);
}

.chat-row {
  display: flex;
  margin-bottom: 10px;
}

.chat-row-left {
  justify-content: flex-start;
}

.chat-row-right {
  justify-content: flex-end;
}

.chat-bubble {
  max-width: 86%;
  border-radius: 16px;
  padding: 12px 14px;
  line-height: 1.6;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
}

.bubble-interviewer {
  background: #f4f6ff;
}

.bubble-candidate {
  background: #edf8f2;
}

.bubble-header {
  font-size: 12px;
  display: flex;
  justify-content: space-between;
  color: var(--el-text-color-secondary);
}

.bubble-content {
  margin-top: 4px;
  white-space: pre-wrap;
}

.thinking-text {
  color: var(--el-text-color-secondary);
}

.thinking-dots {
  display: inline-flex;
  margin-left: 4px;
  gap: 3px;
  vertical-align: middle;
}

.thinking-dots i {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--el-text-color-secondary);
  opacity: 0.25;
  animation: thinking-blink 1.2s infinite ease-in-out;
}

.thinking-dots i:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dots i:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes thinking-blink {
  0%, 80%, 100% {
    opacity: 0.25;
    transform: translateY(0);
  }
  40% {
    opacity: 1;
    transform: translateY(-1px);
  }
}

.bubble-meta {
  margin-top: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.bubble-evaluation {
  margin-top: 8px;
  font-size: 13px;
}

.eval-collapse {
  margin-top: 8px;
  border-radius: 10px;
  overflow: hidden;
}

:deep(.eval-collapse-item .el-collapse-item__header) {
  background: rgba(148, 163, 184, 0.12);
  border-bottom: 0;
  font-size: 13px;
  padding-left: 10px;
}

:deep(.eval-collapse-item .el-collapse-item__wrap) {
  background: rgba(255, 255, 255, 0.55);
}

:deep(.eval-collapse-item .el-collapse-item__content) {
  padding: 10px;
  line-height: 1.7;
}
</style>
