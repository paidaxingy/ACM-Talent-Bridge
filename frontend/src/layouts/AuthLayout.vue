<template>
  <div class="auth-wrapper">
    <div class="auth-card">
      <div class="brand">
        <div class="logo">ACM</div>
        <div class="meta">
          <div class="title">ACM Talent Bridge</div>
          <div class="subtitle">登录 / 注册，开启你的竞赛之旅</div>
        </div>
      </div>
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.auth-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at top left, #1e293b, #020617);
  padding: 24px;
}

.auth-card {
  width: 420px;
  max-width: 100%;
  padding: 32px 28px 28px;
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.9);
  box-shadow:
    0 24px 60px rgba(15, 23, 42, 0.9),
    0 0 0 1px rgba(148, 163, 184, 0.2);
  color: #e5e7eb;
}

.brand {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.logo {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background: conic-gradient(from 180deg at 50% 50%, #22c55e, #22d3ee, #6366f1, #22c55e);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 18px;
  color: #0f172a;
  margin-right: 12px;
}

.meta .title {
  font-weight: 700;
  font-size: 18px;
}

.meta .subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: #9ca3af;
}
</style>

