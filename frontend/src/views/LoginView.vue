<template>
  <div>
    <h2 class="heading">登录账号</h2>
    <p class="subheading">使用账号密码登录，开始训练 / 参赛 / 提交代码。</p>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="form" @submit.prevent="onSubmit">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" autocomplete="username" placeholder="例如 acmer_01" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input
          v-model="form.password"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="current-password"
          placeholder="请输入密码"
          @keyup.enter="onSubmit"
        >
          <template #suffix>
            <el-icon @click="showPassword = !showPassword" class="eye">
              <View v-if="!showPassword" />
              <Hide v-else />
            </el-icon>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="submitting" class="submit" @click="onSubmit">
          登录
        </el-button>
      </el-form-item>
    </el-form>

    <div class="footer">
      还没有账号？
      <router-link class="link" to="/register">立即注册</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { View, Hide } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const showPassword = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

function getRedirectPath() {
  const redirect = route.query.redirect
  if (typeof redirect === 'string' && redirect.startsWith('/')) {
    return redirect
  }
  return '/'
}

const onSubmit = () => {
  if (!formRef.value) return
  formRef.value.validate(async valid => {
    if (!valid) return
    submitting.value = true
    try {
      await auth.login({ username: form.username.trim(), password: form.password })
      ElMessage.success(`欢迎回来，${auth.user?.username}`)
      router.replace(getRedirectPath())
    } catch (e: any) {
      const msg =
        e?.response?.data?.error_detail ||
        e?.response?.data?.detail ||
        '登录失败，请检查用户名或密码'
      ElMessage.error(msg)
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped>
.heading {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 4px;
}

.subheading {
  font-size: 13px;
  color: #9ca3af;
  margin-bottom: 20px;
}

.form :deep(.el-form-item__label) {
  color: #e5e7eb;
}

.submit {
  width: 100%;
}

.footer {
  margin-top: 12px;
  font-size: 13px;
  color: #9ca3af;
  text-align: center;
}

.link {
  color: #38bdf8;
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}

.eye {
  cursor: pointer;
}
</style>

