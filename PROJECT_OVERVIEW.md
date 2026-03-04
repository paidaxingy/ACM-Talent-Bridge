# ACM-Talent-Bridge 项目概述

## 1. 项目定位

ACM-Talent-Bridge 是一个面向 ACM 实验室的人才培养与就业辅助系统。  
核心思路是把训练赛/竞赛/OJ 提交数据统一沉淀，然后围绕训练、竞赛组织和求职准备提供闭环能力。

主要能力包括：
- 竞赛与训练数据管理
- PK 对抗与 Elo-like 竞技分
- OJ 提交与异步判题
- 外部赛历聚合（当前默认 Codeforces）
- AI 面试（聊天式，学生侧）
- 成员能力画像与建议（DeepSeek 日更缓存，失败保留历史）

## 2. 技术栈

- 后端：FastAPI + SQLAlchemy
- 数据库：MySQL 8
- 缓存/队列：Redis
- 异步任务：Celery（worker + beat）
- 前端：Vue 3 + Vite + Element Plus
- 判题：默认本地执行（Python3），可选 Docker 沙箱（Python3/C++17）

## 3. 目录结构（关键）

```text
ACM-Talent-Bridge/
  backend/                 # FastAPI + Celery
    app/
      api/                 # 路由
      core/                # 配置/DB/Celery/安全
      models/              # SQLAlchemy 模型
      schemas/             # Pydantic schema
      services/            # 领域服务（Elo/Judge/AI/画像/聚合）
      tasks/               # Celery 任务
  frontend/                # Vue 3 + Vite
  docker/                  # judge runner 镜像等
  scripts/                 # 脚本（如 smoke_test）
  docker-compose.yml       # 一键启动
```

## 4. 核心运行链路（理解系统的最小路径）

1. 前端调用后端 API 提交业务请求（如提交题解）。
2. 后端落库并把判题任务投递给 Celery。
3. Worker 异步执行判题并回写提交状态。
4. 竞赛榜单、成员画像、PK 分数等由业务接口读取并聚合展示。

## 5. 本地启动（推荐命令）

### 5.1 Docker Compose（最快）

在项目根目录：

```bash
cp backend/.env.example backend/.env
docker compose up -d --build
```

验证：
- `http://localhost:8000/docs`
- `http://localhost:8000/api/v1/health`

### 5.2 前端开发服务

```bash
cd frontend
npm install
npm run dev
```

默认前端地址：`http://localhost:5173`

## 6. 高价值接口（快速联调）

- 健康检查：`GET /api/v1/health`
- 鉴权：`/api/v1/auth/*`
- 成员：`/api/v1/members`
- PK：`/api/v1/pk/*`
- 题目/测试点：`/api/v1/problems`、`/api/v1/problems/{id}/testcases`
- 提交：`/api/v1/submissions`
- 竞赛：`/api/v1/contests`、`/api/v1/contests/{id}/scoreboard`
- 外部赛历：`/api/v1/external/contests*`
- AI 面试（聊天式）：
  - `POST /api/v1/ai/interviews/chat/sessions/start`
  - `POST /api/v1/ai/interviews/chat/sessions/{id}/reply`
  - `GET /api/v1/ai/interviews/chat/sessions/{id}/messages`
  - `GET /api/v1/ai/interviews/chat/sessions/{id}/summary`
  - `POST /api/v1/ai/interviews/chat/sessions/{id}/finish`

## 7. AI 面试现状（给协作 AI 的关键上下文）

- 学生必须先上传 **PDF 简历** 才能开始会话。
- 会话模式为**聊天式**：问一轮、答一轮，用户手动结束为主，不需要预先选择轮次。
- 出题策略：优先基于简历项目/技术栈，同时允许延展到相关基础知识追问（八股）。
- 每轮返回：分数、标准答案、优缺点与建议；会话结束可查看总分汇总。
- PDF 文本抽取支持 OCR 兜底（中文+英文），扫描件质量不足时会返回明确错误提示。
- AI 供应商通过 OpenAI 兼容接口接入（推荐 DeepSeek）。
- 前端请求超时：180 秒；后端 AI 调用超时：90 秒。

## 8. 个人主页 AI 画像现状（给协作 AI 的关键上下文）

- 画像由 Celery 每日定时生成一次（北京时间），并持久化到成员缓存字段。
- 生成内容包括：
  - 四项维度评分（0-100）
  - 推荐方向（方向 + 原因）
  - 提升计划（可执行建议）
  - 能力画像总结文案
- 读取策略：`/me/profile` 和 `/members/{id}/profile` 优先返回 AI 缓存；无缓存时回退规则版。
- 失败策略：调用 DeepSeek 失败时不覆盖旧缓存，仅记录错误，前端继续展示旧结果。

## 9. AI 协作约束（给智能体）

- 优先最小改动，不做无关重构。
- 修改前先阅读相关调用链路，避免跨模块误改。
- 对外行为变更需说明影响面（接口、数据、任务调度）。
- 涉及启动/运行问题时，先确认 MySQL/Redis/API/Worker 是否都在运行。
- Docker 环境下简历目录已持久化到宿主机：`/home/yzt/workspace/ACM-Talent-Bridge/backend/resumes`。
- 优先给出可复制命令，路径使用绝对路径。

## 10. 事实来源

本文件内容来自项目 `README.md` 的当前实现说明与启动步骤。若与实际代码不一致，以代码与运行结果为准，并及时回写本文件。
