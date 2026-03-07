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
  --el-color-primary: #6f86d6;
  --el-color-primary-light-3: #95a7e2;
  --el-color-primary-light-5: #b4c2eb;
  --el-color-primary-light-7: #d4dcf4;
  --el-color-primary-light-8: #e3e9f8;
  --el-color-primary-light-9: #f1f4fc;
  --el-color-primary-dark-2: #5870c0;

  --el-color-success: #63b79d;
  --el-color-success-light-3: #89c9b4;
  --el-color-success-light-5: #aeddcc;
  --el-color-success-light-7: #d5eee5;
  --el-color-success-light-8: #e4f5ef;
  --el-color-success-light-9: #f2fbf8;
  --el-color-success-dark-2: #4e9e86;

  --el-color-warning: #d5a85f;
  --el-color-warning-light-3: #dfbf85;
  --el-color-warning-light-5: #e9d4a9;
  --el-color-warning-light-7: #f4ead0;
  --el-color-warning-light-8: #f8f1e0;
  --el-color-warning-light-9: #fcf8ef;
  --el-color-warning-dark-2: #bc9149;

  --el-color-danger: #db8a85;
  --el-color-danger-light-3: #e7a8a4;
  --el-color-danger-light-5: #efc2bf;
  --el-color-danger-light-7: #f8e2e0;
  --el-color-danger-light-8: #faeceb;
  --el-color-danger-light-9: #fdf5f4;
  --el-color-danger-dark-2: #c6706a;

  --el-color-info: #8b98ae;
  --el-color-info-light-3: #a6b1c3;
  --el-color-info-light-5: #c3cbda;
  --el-color-info-light-7: #e2e6ef;
  --el-color-info-light-8: #edf0f6;
  --el-color-info-light-9: #f7f8fb;
  --el-color-info-dark-2: #748199;

  --el-text-color-primary: #324255;
  --el-text-color-regular: #495b70;
  --el-text-color-secondary: #728197;
  --el-text-color-placeholder: #9ea9b8;

  --el-bg-color: rgba(255, 255, 255, 0.82);
  --el-bg-color-overlay: rgba(255, 255, 255, 0.94);
  --el-bg-color-page: #f5f7f4;
  --el-fill-color: #f7f4ef;
  --el-fill-color-light: #fbf8f3;
  --el-fill-color-lighter: #f8fbfd;
  --el-fill-color-blank: rgba(255, 255, 255, 0.78);

  --app-bg-gradient:
    radial-gradient(circle at top left, rgba(181, 210, 225, 0.34), transparent 32%),
    radial-gradient(circle at top right, rgba(216, 226, 198, 0.34), transparent 28%),
    linear-gradient(180deg, #fbfaf7 0%, #f4f8fb 44%, #f5f7f3 100%);
  --app-surface-strong: rgba(255, 251, 246, 0.84);
  --app-surface-soft: rgba(246, 250, 253, 0.78);
  --app-surface-mute: rgba(240, 244, 239, 0.92);
  --app-accent-wash: linear-gradient(135deg, rgba(111, 134, 214, 0.16), rgba(99, 183, 157, 0.12));

  --el-border-radius-base: 10px;
  --el-border-radius-small: 8px;
  --el-border-radius-round: 999px;

  --el-border-color: rgba(183, 194, 206, 0.7);
  --el-border-color-light: rgba(210, 220, 229, 0.62);
  --el-border-color-lighter: rgba(232, 237, 241, 0.78);
  --el-border-color-extra-light: rgba(238, 243, 246, 0.92);

  --el-box-shadow: 0 18px 44px -28px rgba(94, 112, 141, 0.34);
  --el-box-shadow-light: 0 10px 30px -24px rgba(94, 112, 141, 0.28);
  --el-box-shadow-lighter: 0 4px 16px -14px rgba(94, 112, 141, 0.18);
  --el-box-shadow-dark: 0 26px 60px -32px rgba(86, 102, 126, 0.36);
}

html {
  min-height: 100%;
  background: #f7f7f2;
}

body {
  margin: 0;
  padding: 0;
  min-height: 100vh;
  background: var(--app-bg-gradient);
  color: var(--el-text-color-primary);
  font-family: 'Avenir Next', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  min-height: 100vh;
}

* {
  box-sizing: border-box;
}

.el-card {
  border: 1px solid rgba(222, 229, 234, 0.78) !important;
  border-radius: 20px !important;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(252, 249, 245, 0.9)) !important;
  box-shadow: 0 20px 48px -34px rgba(92, 107, 132, 0.38) !important;
  backdrop-filter: blur(14px);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.el-card.is-hover-shadow:hover,
.el-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 26px 52px -34px rgba(89, 109, 141, 0.44) !important;
}

.el-card__header {
  border-bottom: 1px solid rgba(223, 228, 232, 0.85) !important;
  background: linear-gradient(180deg, rgba(246, 249, 251, 0.74), rgba(255, 250, 245, 0.32));
}

.el-tag {
  border: 1px solid transparent !important;
  border-radius: 999px !important;
  font-weight: 500;
  padding: 0 11px;
}

.el-tag.el-tag--info {
  background-color: rgba(226, 232, 240, 0.7) !important;
  color: #5a687e !important;
}

.el-tag.el-tag--primary {
  background-color: rgba(111, 134, 214, 0.12) !important;
  border-color: rgba(111, 134, 214, 0.18) !important;
  color: #5570c8 !important;
}

.el-button {
  border-radius: 12px !important;
  font-weight: 500 !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease !important;
}

.el-button:not(.is-disabled):hover {
  transform: translateY(-1px);
}

.el-button--primary {
  background: linear-gradient(135deg, #7590dc 0%, #6ca8c8 100%) !important;
  border-color: transparent !important;
  box-shadow: 0 14px 24px -18px rgba(111, 134, 214, 0.72) !important;
}

.el-button--primary.is-plain {
  background: rgba(111, 134, 214, 0.08) !important;
  border-color: rgba(111, 134, 214, 0.18) !important;
}

.el-button.is-text.is-has-bg {
  background: rgba(111, 134, 214, 0.1) !important;
  color: #5570c8 !important;
}

.el-input__wrapper,
.el-textarea__inner,
.el-select__wrapper {
  border-radius: 12px !important;
  background: rgba(255, 255, 255, 0.68) !important;
  box-shadow: 0 0 0 1px rgba(210, 220, 229, 0.88) inset !important;
}

.el-input__wrapper:hover,
.el-textarea__inner:hover,
.el-select__wrapper:hover {
  box-shadow: 0 0 0 1px rgba(175, 189, 203, 0.92) inset !important;
}

.el-input__wrapper.is-focus,
.el-select__wrapper.is-focused,
.el-textarea__inner:focus {
  box-shadow: 0 0 0 1px rgba(111, 134, 214, 0.9) inset, 0 0 0 4px rgba(111, 134, 214, 0.12) !important;
}

.el-table {
  --el-table-border-color: rgba(228, 233, 238, 0.92);
  --el-table-header-bg-color: rgba(245, 247, 249, 0.9);
  --el-table-row-hover-bg-color: rgba(111, 134, 214, 0.06);
  border-radius: 16px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.48);
}

.el-table th.el-table__cell {
  background: linear-gradient(180deg, rgba(244, 248, 251, 0.98), rgba(249, 246, 240, 0.9)) !important;
  color: var(--el-text-color-regular);
  font-weight: 600;
}

.el-table tr {
  background: transparent;
}

.el-table .el-table__cell {
  padding: 13px 0;
}

.el-dialog {
  border: 1px solid rgba(221, 227, 233, 0.92);
  border-radius: 22px !important;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(250, 247, 242, 0.95)) !important;
  box-shadow: 0 28px 80px -46px rgba(76, 93, 118, 0.48) !important;
}

.el-dialog__header {
  margin-right: 0 !important;
  padding-bottom: 16px !important;
  border-bottom: 1px solid rgba(229, 233, 237, 0.88);
  background: linear-gradient(180deg, rgba(245, 248, 251, 0.92), rgba(255, 252, 247, 0.72));
}

.el-dialog__body {
  background: rgba(255, 255, 255, 0.42);
}

.el-tabs__nav-wrap::after {
  background-color: rgba(224, 230, 236, 0.9) !important;
}

.el-tabs__item {
  color: var(--el-text-color-secondary);
  font-weight: 500;
}

.el-tabs__item.is-active {
  color: var(--el-color-primary);
}

.el-tabs__active-bar {
  height: 3px !important;
  border-radius: 999px;
  background: linear-gradient(90deg, #6f86d6, #74b6b0) !important;
}

.el-descriptions {
  --el-descriptions-table-border: rgba(227, 232, 238, 0.94);
}

.el-descriptions__label.el-descriptions__cell.is-bordered-label {
  background: rgba(245, 248, 250, 0.92) !important;
  color: var(--el-text-color-regular) !important;
  font-weight: 600;
}

.el-descriptions__content.el-descriptions__cell.is-bordered-content {
  background: rgba(255, 255, 255, 0.74) !important;
}

.el-empty__description,
.el-empty__description p {
  color: var(--el-text-color-secondary);
}
</style>
