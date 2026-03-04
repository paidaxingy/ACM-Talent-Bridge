<template>
  <component :is="layoutComponent" />
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from './layouts/AppLayout.vue'
import AuthLayout from './layouts/AuthLayout.vue'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const auth = useAuthStore()

const layoutComponent = computed(() => {
  return route.meta.layout === 'auth' ? AuthLayout : AppLayout
})

onMounted(() => {
  auth.loadTokenFromStorage()
  auth.fetchMe()
})
</script>

<style>
:root {
  /* 柔和的色彩体系 (Macaron / Morandi Inspired) */
  --el-color-primary: #818cf8; /* 长春花蓝 */
  --el-color-primary-light-3: #a5b4fc;
  --el-color-primary-light-5: #c7d2fe;
  --el-color-primary-light-7: #e0e7ff;
  --el-color-primary-light-8: #e0e7ff;
  --el-color-primary-light-9: #eef2ff;
  --el-color-primary-dark-2: #6366f1;

  --el-color-success: #34d399; /* 薄荷绿 */
  --el-color-success-light-3: #6ee7b7;
  --el-color-success-light-5: #a7f3d0;
  --el-color-success-light-7: #d1fae5;
  --el-color-success-light-8: #d1fae5;
  --el-color-success-light-9: #ecfdf5;
  --el-color-success-dark-2: #10b981;

  --el-color-warning: #fbbf24; /* 向日葵黄 */
  --el-color-warning-light-3: #fcd34d;
  --el-color-warning-light-5: #fde68a;
  --el-color-warning-light-7: #fef3c7;
  --el-color-warning-light-8: #fef3c7;
  --el-color-warning-light-9: #fffbeb;
  --el-color-warning-dark-2: #f59e0b;

  --el-color-danger: #f87171; /* 珊瑚红 */
  --el-color-danger-light-3: #fca5a5;
  --el-color-danger-light-5: #fecaca;
  --el-color-danger-light-7: #fee2e2;
  --el-color-danger-light-8: #fee2e2;
  --el-color-danger-light-9: #fef2f2;
  --el-color-danger-dark-2: #ef4444;

  --el-color-info: #94a3b8; /* 蓝灰 */
  --el-color-info-light-3: #cbd5e1;
  --el-color-info-light-5: #e2e8f0;
  --el-color-info-light-7: #f1f5f9;
  --el-color-info-light-8: #f1f5f9;
  --el-color-info-light-9: #f8fafc;
  --el-color-info-dark-2: #64748b;

  /* 基础文字与背景颜色 */
  --el-text-color-primary: #334155;
  --el-text-color-regular: #475569;
  --el-text-color-secondary: #64748b;
  --el-bg-color: #ffffff;
  --el-bg-color-page: #f8fafc; /* 极轻微的暖灰底色 */

  /* 圆角全面加大，带来柔和感 */
  --el-border-radius-base: 8px;
  --el-border-radius-small: 6px;
  --el-border-radius-round: 20px;

  /* 边框减弱 */
  --el-border-color: #e2e8f0;
  --el-border-color-light: #f1f5f9;
  --el-border-color-lighter: #f8fafc;

  /* 弥散阴影 */
  --el-box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
  --el-box-shadow-light: 0 2px 4px rgba(0, 0, 0, 0.02), 0 1px 2px rgba(0, 0, 0, 0.04);
  --el-box-shadow-lighter: 0 1px 2px rgba(0, 0, 0, 0.02);
  --el-box-shadow-dark: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.05);
}

body {
  margin: 0;
  padding: 0;
  background-color: var(--el-bg-color-page);
  color: var(--el-text-color-primary);
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 针对特定组件的复写：无边框 & 更大的卡片圆角 */
.el-card {
  border: none !important;
  border-radius: 16px !important;
  background-color: #ffffff;
  box-shadow: 0 4px 20px -2px rgba(148, 163, 184, 0.15) !important;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.el-card.is-hover-shadow:hover, .el-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px -4px rgba(148, 163, 184, 0.25) !important;
}

/* 标签：糖果色无边框设计 */
.el-tag {
  border: none !important;
  border-radius: 8px !important;
  font-weight: 500;
  padding: 0 10px;
}
.el-tag.el-tag--info {
  background-color: #f1f5f9 !important;
  color: #475569 !important;
}

/* 按钮稍微加点圆润度 */
.el-button {
  border-radius: 8px !important;
  font-weight: 500 !important;
}

/* 输入框等也变得更圆滑 */
.el-input__wrapper, .el-textarea__inner {
  border-radius: 8px !important;
  box-shadow: 0 0 0 1px var(--el-border-color) inset !important;
}
.el-input__wrapper.is-focus, .el-textarea__inner:focus {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset !important;
}
</style>
