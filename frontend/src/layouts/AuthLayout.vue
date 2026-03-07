<template>
  <div class="auth-wrapper">
    <div class="aurora aurora-left"></div>
    <div class="aurora aurora-right"></div>

    <div class="auth-shell">
      <section class="intro-panel">
        <div class="brand">
          <div class="logo">ACM</div>
          <div class="meta">
            <div class="eyebrow">Algorithm · Career · Growth</div>
            <div class="title">ACM Talent Bridge</div>
            <div class="subtitle">把训练、竞赛、面试准备和成长记录，放进一个舒适清晰的入口里。</div>
          </div>
        </div>

        <div class="feature-list">
          <div class="feature-item">
            <span class="feature-dot feature-blue"></span>
            训练赛、提交记录与榜单进度一处查看
          </div>
          <div class="feature-item">
            <span class="feature-dot feature-green"></span>
            AI 面试与能力画像帮助你持续复盘
          </div>
          <div class="feature-item">
            <span class="feature-dot feature-gold"></span>
            从实验室训练到求职准备，体验保持连贯
          </div>
        </div>
      </section>

      <section class="auth-card">
        <div class="card-badge">Welcome Back</div>
        <div class="card-title">进入你的训练空间</div>
        <div class="card-subtitle">登录或创建账号后，即可继续比赛、练题与查看画像。</div>
        <div class="form-host">
          <router-view />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.auth-wrapper {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(183, 210, 223, 0.5), transparent 30%),
    radial-gradient(circle at bottom right, rgba(214, 226, 198, 0.52), transparent 32%),
    linear-gradient(160deg, #fcfaf6 0%, #f4f8fb 52%, #f6f7f1 100%);
  padding: 32px 20px;
}

.aurora {
  position: absolute;
  border-radius: 50%;
  filter: blur(24px);
  opacity: 0.8;
  pointer-events: none;
}

.aurora-left {
  top: -80px;
  left: -90px;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(117, 144, 220, 0.22) 0%, rgba(117, 144, 220, 0) 72%);
}

.aurora-right {
  right: -70px;
  bottom: -90px;
  width: 320px;
  height: 320px;
  background: radial-gradient(circle, rgba(99, 183, 157, 0.22) 0%, rgba(99, 183, 157, 0) 72%);
}

.auth-shell {
  position: relative;
  z-index: 1;
  width: min(1080px, 100%);
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 24px;
  align-items: stretch;
}

.intro-panel,
.auth-card {
  border: 1px solid rgba(220, 227, 233, 0.8);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.68);
  backdrop-filter: blur(18px);
  box-shadow: 0 30px 70px -46px rgba(82, 100, 124, 0.38);
}

.intro-panel {
  padding: 40px 38px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 620px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.78), rgba(248, 250, 249, 0.72)),
    linear-gradient(135deg, rgba(117, 144, 220, 0.08), rgba(99, 183, 157, 0.08));
}

.brand {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.logo {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  background: linear-gradient(135deg, #7590dc 0%, #74b6b0 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 20px;
  color: #fff;
  box-shadow: 0 20px 30px -20px rgba(111, 134, 214, 0.8);
}

.meta {
  max-width: 460px;
}

.eyebrow {
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #8090a4;
}

.meta .title {
  margin-top: 10px;
  font-size: 34px;
  line-height: 1.15;
  font-weight: 800;
  color: #304155;
}

.meta .subtitle {
  margin-top: 14px;
  font-size: 15px;
  line-height: 1.8;
  color: #708095;
}

.feature-list {
  display: grid;
  gap: 14px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  border-radius: 18px;
  color: #4d5f73;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(222, 229, 234, 0.84);
}

.feature-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  flex: 0 0 auto;
}

.feature-blue {
  background: #7e96dd;
}

.feature-green {
  background: #6bb7a0;
}

.feature-gold {
  background: #d7ae6a;
}

.auth-card {
  padding: 32px 30px 28px;
  align-self: center;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(252, 248, 243, 0.88));
}

.card-badge {
  display: inline-flex;
  padding: 7px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: #5d74c5;
  background: rgba(111, 134, 214, 0.1);
}

.card-title {
  margin-top: 18px;
  font-size: 28px;
  font-weight: 800;
  color: #314154;
}

.card-subtitle {
  margin-top: 10px;
  font-size: 14px;
  line-height: 1.8;
  color: #738297;
}

.form-host {
  margin-top: 26px;
}

@media (max-width: 960px) {
  .auth-shell {
    grid-template-columns: 1fr;
  }

  .intro-panel {
    min-height: auto;
    gap: 24px;
  }

  .meta .title {
    font-size: 30px;
  }
}

@media (max-width: 640px) {
  .auth-wrapper {
    padding: 20px 14px;
  }

  .intro-panel,
  .auth-card {
    border-radius: 22px;
  }

  .intro-panel {
    padding: 28px 22px;
  }

  .auth-card {
    padding: 24px 20px 22px;
  }

  .brand {
    flex-direction: column;
  }

  .meta .title {
    font-size: 26px;
  }

  .card-title {
    font-size: 24px;
  }
}
</style>
