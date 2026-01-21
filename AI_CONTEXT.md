# ACM Talent Bridge - AI 上下文提示词

> **目的**：让 AI 助手快速理解项目架构、核心逻辑和设计决策，无需阅读整个代码库即可高效协助开发。

---

## 📋 项目概述

**ACM Talent Bridge** 是一个面向 ACM 实验室的智能人才培养与就业辅助系统。核心功能包括：
- **训练赛/竞赛管理**：创建竞赛、添加题目、报名、提交代码、自动评测
- **能力画像系统**：基于提交/PK/面试数据，生成个人能力画像和就业建议
- **PK 对抗系统**：Elo-like 评分机制，支持 2 队对抗
- **AI 面试**：自动生成题目、评估回答、结构化反馈
- **赛历聚合**：聚合 Codeforces、AtCoder 等外部竞赛

### 技术栈

- **后端**：FastAPI + SQLAlchemy + MySQL 8 + Redis + Celery
- **前端**：Vue 3 + Vite + Element Plus + TypeScript
- **判题**：Docker 沙箱（Python3 / C++17），支持时间/内存限制
- **认证**：JWT Token
- **时区**：统一使用中国标准时间（UTC+8，Asia/Shanghai）

---

## 🗄️ 核心数据模型

### 用户体系（User ↔ Member）

**重要设计决策**：
- `users` 表：登录账号（username, password, role, is_active）
- `members` 表：训练成员档案（handle, rating, tier, group_name）
- **注册时自动创建**：用户注册时，自动在 `members` 表创建一条记录，`handle = username`，`rating = 1500`，`tier = 1`
- **提交自动关联**：创建提交时，根据 `user.username` 查找 `Member.handle`，自动设置 `submission.member_id`

**关键字段**：
- `User.role`: `"student"` 或 `"admin"`
- `Member.rating`: Elo-like 评分（默认 1500）
- `Member.tier`: 梯队（1-10）
- `Member.handle`: 唯一标识（注册时 = username）

### 题目与测试用例

**Problem** (`problems` 表)：
- `id`, `lab_id`（已废弃，内部使用默认 Lab）
- `title`, `statement`, `input_desc`, `output_desc`
- `time_limit_ms`, `memory_limit_mb`

**Testcase** (`testcases` 表)：
- `id`, `problem_id`（FK）
- `input_data`, `expected_output`
- **`is_sample`**: `True` = 样例（学生可见），`False` = 隐藏测试点（仅评测用）
- `sort_order`

### 竞赛系统

**Contest** (`contests` 表)：
- `id`, `lab_id`（已废弃，内部使用默认 Lab）
- `name`, `contest_type`（training/selection/mock）
- **`status`**: 由 `start_at` / `end_at` 自动计算，不允许手动设置
  - `draft`: 草稿（未设置时间）
  - `published`: 已发布但未开始（`now < start_at`）
  - `running`: 进行中（`start_at <= now < end_at`）
  - `finished`: 已结束（`now >= end_at`）
- `start_at`, `end_at`（MySQL DATETIME，无时区，后端统一按 UTC+8 解释）

**ContestProblem** (`contest_problems` 表)：
- `contest_id`, `problem_id`, `sort_order`, `score`

**ContestTeamRegistration** (`contest_team_registrations` 表)：
- `contest_id`, `team_id`（队伍报名竞赛）

### 提交与评测

**Submission** (`submissions` 表)：
- `id`, `user_id`, `member_id`（自动关联）, `team_id`, `problem_id`, `contest_id`
- `language`（python3/cpp17）, `code`
- `status`（pending/judging/done）
- `verdict`（AC/WA/CE/RE/TLE/SE）
- `time_ms`, `memory_kb`（Docker 评测时自动捕获）
- `judge_task_id`（Celery task ID）

**评测流程**：
1. 用户提交 → `POST /api/v1/submissions`
2. 创建 `Submission` 记录，`status = "pending"`
3. 异步调用 `judge_submission.delay(submission.id)`
4. Celery worker 执行评测（Docker 或本地）
5. 更新 `Submission`：`status = "done"`, `verdict`, `time_ms`, `memory_kb`

### 队伍系统

**Team** (`teams` 表)：
- `id`, `lab_id`（已废弃）
- `name`

**TeamMember** (`team_members` 表)：
- `team_id`, `user_id`（多对多关系）
- `joined_at`

### PK 对抗系统

**PKMatch** (`pk_matches` 表)：
- `id`, `lab_id`（已废弃）
- `title`, `status`（pending/finished）
- `winner_team_no`（1 或 2），`is_draw`

**PKParticipant** (`pk_participants` 表)：
- `match_id`, `member_id`, `team_no`（1 或 2）
- `rating_before`, `rating_delta`（结算时计算）

**Elo 计算**：在 `finish_pk_match` 时，根据胜负/平局，使用 Elo 公式更新 `Member.rating`。

---

## 🔐 权限与认证

### 角色体系

- **student**（默认）：普通学生
- **admin**：管理员（可管理用户、题目、竞赛等）

### 权限控制

**后端依赖**：
- `get_current_user`: 获取当前登录用户（JWT）
- `require_admin`: 仅管理员可访问

**受保护的操作**（需要 `require_admin`）：
- 创建/更新/删除题目
- 创建/更新/删除竞赛
- 创建/更新/删除测试用例
- 用户管理（修改角色、激活/禁用）
- 重新评测（rejudge）

**学生权限**：
- 查看自己的提交（`/submissions` 自动过滤 `user_id`）
- 查看自己的主页（`/me/profile`）
- 查看题目、竞赛列表
- 提交代码（需在队伍中）

---

## 🌐 API 路由结构

### 认证相关 (`/api/v1/auth`)
- `POST /register`: 注册（自动创建 Member）
- `POST /login`: 登录（返回 JWT）
- `GET /me`: 获取当前用户信息

### 用户管理 (`/api/v1/users`) - 仅管理员
- `GET /users`: 列表（支持 `role`, `is_active` 过滤）
- `PATCH /users/{user_id}`: 修改角色/激活状态

### 成员画像 (`/api/v1/members`)
- `GET /members`: 列表
- `GET /members/{member_id}/profile`: 获取能力画像（公开）

### 我的信息 (`/api/v1/me`)
- `GET /me/profile`: 获取当前用户的能力画像
- `GET /me/teams`: 获取我加入的队伍
- `GET /me/contests/{contest_id}/active_team`: 获取我在某竞赛中的活跃队伍

### 题目管理 (`/api/v1/problems`) - 写操作需管理员
- `GET /problems`: 列表
- `GET /problems/{problem_id}`: 详情
- `POST /problems`: 创建（自动分配默认 `lab_id`）
- `PATCH /problems/{problem_id}`: 更新
- `DELETE /problems/{problem_id}`: 删除
- `GET /problems/{problem_id}/testcases`: 测试用例列表（学生只能看到 `is_sample=true`）
- `POST /problems/{problem_id}/testcases`: 添加测试用例
- `DELETE /problems/{problem_id}/testcases/{testcase_id}`: 删除测试用例

### 竞赛管理 (`/api/v1/contests`) - 写操作需管理员
- `GET /contests`: 列表（支持 `status` 过滤）
- `GET /contests/{contest_id}`: 详情
- `POST /contests`: 创建（自动分配默认 `lab_id`，`status` 由时间计算）
- `PATCH /contests/{contest_id}`: 更新（`status` 由时间重新计算）
- `DELETE /contests/{contest_id}`: 删除
- `POST /contests/{contest_id}/problems`: 添加题目到竞赛
- `GET /contests/{contest_id}/scoreboard`: 榜单

### 提交管理 (`/api/v1/submissions`)
- `GET /submissions`: 列表（学生只能看到自己的）
- `GET /submissions/{submission_id}`: 详情（学生只能看到自己的）
- `POST /submissions`: 创建提交（自动关联 `member_id`）
- `POST /submissions/{submission_id}/rejudge`: 重新评测（仅管理员）

### 队伍管理 (`/api/v1/teams`)
- `GET /teams`: 列表
- `POST /teams`: 创建
- `POST /teams/{team_id}/members`: 添加成员

---

## 🎨 前端路由结构

### 用户端（`requiresAuth: true`）
- `/`: 我的主页（`MyProfileView.vue`）
- `/contests`: 竞赛列表（`UserContestsView.vue`）
- `/contests/:id`: 竞赛详情（`ContestDetailView.vue`）
- `/problems/:id`: 题目详情（`ProblemDetailView.vue`，支持 `?contest_id=&team_id=`）
- `/submissions`: 我的提交（`MySubmissionsView.vue`）
- `/teams`: 我的队伍（`TeamsView.vue`）

### 管理端（`adminOnly: true`）
- `/admin/users`: 用户管理（`UsersView.vue`）
- `/admin/problems`: 题库管理（`ProblemsView.vue`）
- `/admin/contests`: 竞赛管理（`ContestsView.vue`）
- `/admin/submissions`: 提交管理（`SubmissionsView.vue`）
- `/admin/pk`: PK 对抗（`PKView.vue`）
- `/admin/external`: 赛历聚合（`ExternalContestsView.vue`）
- `/admin/ai`: AI 面试（`AIInterviewView.vue`）

**注意**：已移除 `/admin/members`（成员管理），因为注册时自动创建。

---

## ⚙️ 关键业务逻辑

### 1. 竞赛状态计算

**位置**：`backend/app/api/routes/contests.py` → `_compute_effective_status()`

**逻辑**：
```python
# 所有时间统一转换为北京时区（UTC+8）进行比较
cn_tz = timezone(timedelta(hours=8))
now = datetime.now(tz=cn_tz).replace(tzinfo=None)
start_at = _as_cn_naive(contest.start_at)  # MySQL DATETIME 按 UTC+8 解释
end_at = _as_cn_naive(contest.end_at)

if end_at and now >= end_at:
    return "finished"
elif start_at and now >= start_at:
    return "running"
elif start_at and now < start_at:
    return "published"
else:
    return "draft"
```

**重要**：
- `status` 字段**不允许手动设置**，必须通过 `start_at` / `end_at` 计算
- 创建/更新竞赛时，自动调用 `_compute_effective_status()` 设置 `status`

### 2. 提交时自动关联 Member

**位置**：`backend/app/api/routes/submissions.py` → `create_submission()`

**逻辑**：
```python
# 根据 user.username 查找对应的 Member（handle = username）
member = db.execute(
    select(Member).where(Member.handle == user.username).limit(1)
).scalars().first()
if member:
    submission.member_id = member.id
```

### 3. 能力画像统计

**位置**：`backend/app/services/member_profile.py` → `build_member_profile_summary()`

**统计逻辑**：
- **提交数**：统计 `Submission.member_id == member_id` 或 `User.username == Member.handle`（兼容旧数据）
- **PK 战绩**：统计 `PKParticipant` 中 `status == "finished"` 的记录
- **参赛场次**：统计 `ContestRegistration.member_id == member_id`

**画像计算**：`backend/app/services/ability_profile.py` → `compute_ability_profile()`
- 竞技强度：基于 `rating`（1200-2400 → 20-95）
- 稳定性：基于 PK 胜率 + 场次
- 表达：基于面试平均分
- 解题：基于 AC 率 + rating

### 4. 评测流程

**位置**：`backend/app/tasks/judge.py` → `judge_submission()`

**流程**：
1. 获取题目的所有测试用例（包括隐藏测试点）
2. 根据 `JUDGE_ENABLE_DOCKER` 选择评测方式：
   - Docker：`backend/app/services/judge_docker.py` → `judge_in_docker()`
   - 本地：`backend/app/services/judge_python3.py` → `judge_python3()`
3. Docker 评测使用 `/usr/bin/time` 捕获 `time_ms` 和 `memory_kb`
4. 更新 `Submission` 记录

---

## 🚨 重要设计决策与约束

### 1. Lab 概念已废弃

- **前端**：不再显示“实验室管理”，所有表单不要求输入 `lab_id`
- **后端**：`lab_id` 字段仍存在（数据库兼容），但：
  - 创建 Problem/Contest/Member 时，自动分配默认 Lab（`init_db()` 确保存在）
  - 所有业务逻辑不再检查 `lab_id` 一致性
  - 用户无需关心 Lab 概念

### 2. 时区统一为 UTC+8

- **Docker Compose**：所有服务设置 `TZ=Asia/Shanghai`
- **后端逻辑**：所有时间比较统一转换为北京时区
- **前端显示**：使用 Element Plus 的日期选择器，默认时区为本地

### 3. 测试用例可见性

- **学生**：只能看到 `is_sample=true` 的测试用例
- **管理员**：可以看到所有测试用例（包括隐藏测试点）
- **评测**：使用所有测试用例（`is_sample` 不影响评测）

### 4. 提交代码可见性

- **学生**：只能查看自己的提交（`/submissions` 自动过滤 `user_id`）
- **管理员**：可以查看所有提交
- **提交详情**：包含 `code` 字段，前端弹窗展示

### 5. 用户主页自动刷新

- **自己的主页**（`/`）：每 30 秒自动刷新一次
- **别人的主页**（`/profile/:memberId`）：不自动刷新

---

## 📁 关键文件位置

### 后端核心

- **模型**：`backend/app/models/`（`user.py`, `member.py`, `problem.py`, `contest.py`, `submission.py`, `team.py`）
- **路由**：`backend/app/api/routes/`（`auth.py`, `users.py`, `members.py`, `problems.py`, `contests.py`, `submissions.py`, `me.py`）
- **服务**：`backend/app/services/`（`member_profile.py`, `ability_profile.py`, `judge_docker.py`）
- **任务**：`backend/app/tasks/judge.py`（Celery 评测任务）
- **依赖**：`backend/app/core/deps.py`（`get_current_user`, `require_admin`）
- **数据库初始化**：`backend/app/core/db.py`（`init_db()` 确保默认 Lab 存在）

### 前端核心

- **路由**：`frontend/src/router/index.ts`
- **布局**：`frontend/src/layouts/AppLayout.vue`（侧边栏菜单）
- **用户主页**：`frontend/src/views/MyProfileView.vue`
- **题目详情**：`frontend/src/views/ProblemDetailView.vue`
- **竞赛管理**：`frontend/src/views/ContestsView.vue`
- **API 客户端**：`frontend/src/api/client.ts`

---

## 🔧 开发约定

### 代码风格

- **Python**：遵循 PEP 8，使用类型注解
- **TypeScript**：使用严格模式，接口定义清晰
- **命名**：后端用 snake_case，前端用 camelCase

### 错误处理

- **后端**：使用 FastAPI 的 `HTTPException`，返回 `{detail: "..."}`
- **前端**：使用 Element Plus 的 `ElMessage.error()` 显示错误

### 数据库迁移

- **当前**：使用 SQLAlchemy 的 `Base.metadata.create_all()`（开发阶段）
- **生产**：建议使用 Alembic 进行迁移管理

### 环境变量

- **后端**：`backend/.env`（参考 `backend/.env.example`）
- **前端**：`VITE_API_BASE_URL`（默认 `http://localhost:8000`）

---

## 🐛 常见问题与解决方案

### 1. 提交后 `member_id` 为 NULL

**原因**：注册时未创建 Member，或 `handle` 与 `username` 不一致  
**解决**：检查注册逻辑，确保 `Member.handle == User.username`

### 2. 竞赛状态显示为 "unknown"

**原因**：前端状态映射不一致  
**解决**：后端返回 `finished`，前端应映射为 `ended`；后端返回 `registration`，前端应映射为 `published`

### 3. 时间比较错误（Timezone）

**原因**：MySQL `DATETIME` 无时区，后端未统一转换  
**解决**：所有时间比较统一转换为北京时区（UTC+8）

### 4. 评测后 `time_ms` / `memory_kb` 为 NULL

**原因**：Docker 评测未安装 `time` 工具，或未正确捕获  
**解决**：确保 `docker/judge-runner/Dockerfile` 包含 `time` 包，`judge_docker.py` 使用 `/usr/bin/time` 捕获

---

## 📝 待办事项（已知限制）

- [ ] 使用 Alembic 进行数据库迁移管理
- [ ] 完善错误日志和监控
- [ ] 添加单元测试和集成测试
- [ ] 优化 Docker 评测性能
- [ ] 支持更多编程语言（Java, Go 等）
- [ ] 实现更复杂的 Elo 变体（K 值动态调整）

---

## 🎯 快速参考

### 创建题目并添加测试用例

```python
# 1. 创建题目（管理员）
POST /api/v1/problems
{
  "title": "A+B Problem",
  "statement": "...",
  "input_desc": "...",
  "output_desc": "..."
}

# 2. 添加样例测试用例
POST /api/v1/problems/{problem_id}/testcases
{
  "input_data": "1 2",
  "expected_output": "3",
  "is_sample": true,
  "sort_order": 1
}

# 3. 添加隐藏测试用例
POST /api/v1/problems/{problem_id}/testcases
{
  "input_data": "100 200",
  "expected_output": "300",
  "is_sample": false,
  "sort_order": 2
}
```

### 创建竞赛并添加题目

```python
# 1. 创建竞赛（管理员）
POST /api/v1/contests
{
  "name": "春季训练赛",
  "start_at": "2024-03-01T10:00:00",
  "end_at": "2024-03-01T14:00:00"
}

# 2. 添加题目到竞赛
POST /api/v1/contests/{contest_id}/problems
{
  "problem_id": 1,
  "sort_order": 1,
  "score": 100
}
```

### 查看用户能力画像

```python
# 自己的画像
GET /api/v1/me/profile

# 别人的画像（公开）
GET /api/v1/members/{member_id}/profile
```

---

**最后更新**：2024-03-XX  
**维护者**：项目团队
