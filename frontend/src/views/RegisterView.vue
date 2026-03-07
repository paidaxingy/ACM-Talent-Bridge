<template>
  <div>
    <h2 class="heading">注册新账号</h2>
    <p class="subheading">创建一个学生账号，后续可由管理员升级为管理员权限。</p>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="form">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" autocomplete="username" placeholder="仅支持字母/数字/下划线" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input
          v-model="form.password"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="new-password"
          placeholder="至少 6 位，建议包含字母和数字"
        >
          <template #suffix>
            <el-icon @click="showPassword = !showPassword" class="eye">
              <View v-if="!showPassword" />
              <Hide v-else />
            </el-icon>
          </template>
        </el-input>
      </el-form-item>
      <el-form-item label="确认密码" prop="confirmPassword">
        <el-input
          v-model="form.confirmPassword"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="new-password"
          placeholder="再次输入密码"
        />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="submitting" class="submit" @click="onSubmit">
          注册并登录
        </el-button>
      </el-form-item>
    </el-form>

    <div class="footer">
      已有账号？
      <router-link class="link" to="/login">直接登录</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { View, Hide } from '@element-plus/icons-vue'

const router = useRouter()
const auth = useAuthStore()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const showPassword = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const onSubmit = () => {
  if (!formRef.value) return
  formRef.value.validate(async valid => {
    if (!valid) return
    submitting.value = true
    try {
      await auth.register({ username: form.username.trim(), password: form.password })
      ElMessage.success('注册成功，已自动为你登录')
      router.replace('/')
    } catch (e: any) {
      const msg =
        e?.response?.data?.error_detail ||
        e?.response?.data?.detail ||
        '注册失败，请稍后重试或更换用户名'
      ElMessage.error(msg)
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped>
.heading {
  font-size: 24px;
  font-weight: 800;
  margin-bottom: 6px;
  color: #314154;
}

.subheading {
  font-size: 14px;
  line-height: 1.8;
  color: #738297;
  margin-bottom: 24px;
}

.form :deep(.el-form-item__label) {
  color: #5c6d82;
  font-weight: 600;
}

.form :deep(.el-form-item) {
  margin-bottom: 22px;
}

.submit {
  width: 100%;
  min-height: 44px;
}

.footer {
  margin-top: 14px;
  font-size: 13px;
  color: #7d8ba0;
  text-align: center;
}

.link {
  color: #5b76cb;
  text-decoration: none;
  font-weight: 600;
}

.link:hover {
  text-decoration: underline;
}

.eye {
  cursor: pointer;
  color: #8a96aa;
}

.form :deep(.el-input__inner) {
  color: #324255;
}

.form :deep(.el-input__inner::placeholder) {
  color: #a0aab8;
}
</style>
