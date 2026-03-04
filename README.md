## ACM-Talent-Bridge

面向 ACM 实验室的智能人才培养与就业辅助系统：以 **训练赛/竞赛/OJ 提交**为数据入口，融合 **PK（Elo-like）**、**赛历聚合**、**AI 面试**与**能力画像**，为成员训练、竞赛组织与就业指导提供一体化支持。

> 产品/前后端共享写作入口：见 `PRODUCT_COLLAB.md`

### 技术栈

- **后端**：FastAPI + SQLAlchemy
- **数据库**：MySQL 8
- **缓存/队列**：Redis
- **异步任务**：Celery（worker + beat）
- **判题**：MVP 默认本地执行（Python3），可选 Docker 沙箱（Python3 / C++17）
- **前端**：Vue 3 + Vite + Element Plus

### 目录结构

```
ACM-Talent-Bridge/
  backend/                 # FastAPI + Celery
    app/
      api/                 # 路由
      core/                # 配置/DB/Celery/安全
      models/              # SQLAlchemy 模型
      schemas/             # Pydantic schema
      services/            # 领域服务（Elo/Judge/AI/画像/聚合）
      tasks/               # Celery 任务
    Dockerfile
    requirements.txt
    .env.example
  frontend/                # Vue 3
  docker/                  # judge runner 镜像等
  docker-compose.yml
  Makefile
```

### 已实现功能（当前仓库）

- **实验室/成员管理**：成员分组/梯队、初始竞技分、查询与维护
- **PK 对抗（2 队）**：创建对抗、结算胜负/平局、自动更新竞技分（Elo-like）
- **竞赛管理（MVP）**：创建竞赛、配置题目、报名、榜单（基于提交结果计算 ACM 风格）
- **题库 + 测试用例**：题目与测试点维护
- **OJ 提交 + 异步评测**：提交后 Celery 异步判题并回写结果；支持 rejudge
- **赛历聚合**：当前默认聚合 Codeforces，支持接口触发刷新与定时刷新
- **AI 面试（聊天式）**：学生侧对话面试、逐轮评分/标准答案、会话总分；支持 DeepSeek（OpenAI 兼容）
- **能力画像/就业建议（AI 日更）**：每天由 DeepSeek 生成维度评分、推荐方向、提升计划与能力画像文案；失败时保留上次成功结果
- **认证占位（JWT）**：注册/登录/获取当前用户（当前业务接口未强制鉴权，后续可逐步加 RBAC）

> 完整接口请以 Swagger 为准：启动后访问 `http://localhost:8000/docs`

---

## 快速开始（Docker Compose 一键跑）

### 1）准备环境

- Docker / Docker Compose

### 2）配置环境变量

```bash
cp backend/.env.example backend/.env
```

### 3）启动后端全套（MySQL + Redis + API + Celery worker + Celery beat）

```bash
docker compose up -d --build
```

### 4）访问

- Swagger：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/v1/health`

---

## 本地开发（Python venv，适配 WSL + fish）

目标：**API/worker 在本机跑（方便调试）**，MySQL/Redis 用 Docker。

### 1）创建 venv

```bash
python3 -m venv .venv
```

如提示缺少 venv：

```bash
sudo apt update && sudo apt install -y python3-venv
```

### 2）激活 venv

- fish：

```bash
source .venv/bin/activate.fish
```

- bash/zsh：

```bash
source .venv/bin/activate
```

### 3）安装依赖

```bash
pip install -U pip
pip install -r backend/requirements.txt
```

### 4）启动 MySQL/Redis

```bash
docker compose up -d mysql redis
```

### 5）本地 `.env` 主机名改为本机

将 `backend/.env` 中的：
- `DATABASE_URL`：主机从 `mysql` 改为 `127.0.0.1`
- `REDIS_URL / CELERY_BROKER_URL / CELERY_RESULT_BACKEND`：主机从 `redis` 改为 `127.0.0.1`

### 6）启动 API（热重载）

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7）启动 Celery（新开终端）

```bash
cd backend
celery -A app.core.celery_app:celery worker -l INFO
```

（可选）启动 beat（赛历定时聚合依赖 beat）：

```bash
cd backend
celery -A app.core.celery_app:celery beat -l INFO
```

> 也可以用 `Makefile`：`make venv` / `make deps` / `make backend-dev` / `make worker`

---

## 前端启动（Vue 3）

```bash
cd frontend
npm install
# 可选：指定后端地址（默认 http://localhost:8000）
export VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

---

## （可选）启用 Docker 沙箱判题

默认判题（MVP）是 worker 里本地执行，仅支持 `python3`。如要启用 Docker 沙箱（支持 `python3`/`cpp17`）：

### 1）构建 runner 镜像（一次即可）

```bash
docker build -t acm-judge-runner:latest docker/judge-runner
```

### 2）在 `backend/.env` 中开启

```bash
JUDGE_ENABLE_DOCKER=1
JUDGE_DOCKER_MODE=volume
JUDGE_WORKSPACE_DIR=/judge_workspace
JUDGE_WORKSPACE_VOLUME=judge_workspace
```

> `docker-compose.yml` 已把 `judge_workspace` volume 挂载到 worker 的 `/judge_workspace`，用于和 runner 容器共享文件。

---

## 关键接口速览（高频）

- **Health**：`GET /api/v1/health`
- **Auth**：`POST /api/v1/auth/register`、`POST /api/v1/auth/login`、`GET /api/v1/auth/me`
- **Labs**：`/api/v1/labs`
- **Members**：`/api/v1/members`，画像：`GET /api/v1/members/{id}/profile`
- **PK**：创建：`POST /api/v1/pk/matches`，结算：`POST /api/v1/pk/matches/{id}/finish`
- **Problems/Testcases**：`/api/v1/problems`、`/api/v1/problems/{id}/testcases`
- **Contests**：`/api/v1/contests`、榜单：`GET /api/v1/contests/{id}/scoreboard`
- **Submissions**：`POST /api/v1/submissions`、`POST /api/v1/submissions/{id}/rejudge`
- **External contests**：列表：`GET /api/v1/external/contests`、刷新：`POST /api/v1/external/contests/refresh`
- **AI interviews（聊天式）**：
  - 开始：`POST /api/v1/ai/interviews/chat/sessions/start`
  - 回复：`POST /api/v1/ai/interviews/chat/sessions/{id}/reply`
  - 消息：`GET /api/v1/ai/interviews/chat/sessions/{id}/messages`
  - 汇总：`GET /api/v1/ai/interviews/chat/sessions/{id}/summary`
  - 结束：`POST /api/v1/ai/interviews/chat/sessions/{id}/finish`
  - 说明：开始前要求学生先上传 **PDF** 简历

---

## 配置说明（`backend/.env`）

- **数据库/队列**：`DATABASE_URL`、`REDIS_URL`、`CELERY_BROKER_URL`、`CELERY_RESULT_BACKEND`
- **OJ 判题**：`JUDGE_ENABLE_DOCKER`、`JUDGE_TIME_LIMIT_MS`、`JUDGE_MEMORY_LIMIT_MB`、`JUDGE_DOCKER_IMAGE`
- **AI Provider**
  - 默认：`AI_PROVIDER=mock`
  - OpenAI-compatible：设置 `AI_PROVIDER` 非 `mock`，并配置 `AI_BASE_URL`、`AI_API_KEY`、`AI_MODEL`
  - DeepSeek（推荐）：
    - `AI_PROVIDER=openai`
    - `AI_BASE_URL=https://api.deepseek.com`
    - `AI_API_KEY=<你的 DeepSeek Key>`
    - `AI_MODEL=deepseek-chat`

---

## AI 面试注意事项（最新）

- **不需要预先选择轮次**：聊天会话以“用户手动结束”为主（前端点击“结束面试”）。
- **提问策略**：优先围绕简历项目/职责/技术栈，同时允许延展到相关基础知识（如简历提到 C++，会追问 C++ 基础与工程实践）。
- **简历解析**：PDF 先走文本提取，文本质量不足时自动 OCR（中文+英文）兜底；若仍不可读，会返回“请上传可复制文字的 PDF”。
- **超时策略**：后端调用 AI 超时上调为 90s；前端 API 请求超时上调为 180s（3 分钟），减少 DeepSeek 慢响应导致的前端超时。
- **Docker 持久化**：`docker-compose.yml` 已挂载 `./backend/resumes:/app/resumes`，重建 `api/worker` 后简历文件仍保留在宿主机 `backend/resumes`。

---

## 个人主页 AI 画像（日更）

- **生成机制**：后端 Celery beat 每天（北京时间）自动执行一次成员画像生成任务（DeepSeek）。
- **覆盖范围**：维度评分（竞技强度/稳定性/表达/解题）、推荐方向、提升计划、能力画像文案。
- **失败策略**：若某次调用失败，仅记录错误，不覆盖历史缓存；页面继续展示上一次成功结果。
- **接口表现**：`/api/v1/me/profile` 与 `/api/v1/members/{id}/profile` 优先返回 AI 缓存，首次无缓存时回退规则版。

