## 11. A+B 示例题目与竞赛（联调用）

> 目的：提供一套「从题目 → 测试用例 → 竞赛 → 报名 → 提交 → 榜单」的最小可用样例，方便 FE/BE/测试快速验证闭环。

### 11.1 题目（A + B）

- **标题**：A + B Problem
- **题面（statement）**：
  - 给定两个整数 \\(a, b\\)，输出它们的和 \\(a + b\\)。
- **输入描述（input_desc）**：
  - 输入包含一行，包含两个整数 \\(a, b\\)（以空格分隔）。
  - \\(-10^9 \\le a, b \\le 10^9\\)。
- **输出描述（output_desc）**：
  - 输出一个整数，即 \\(a + b\\) 的值，末尾可有换行。
- **样例 1**：
  - 输入：

    ```text
    1 2
    ```

  - 输出：

    ```text
    3
    ```

- **后端创建约定（ProblemCreate）**：
  - `lab_id`: 使用现有 lab 中任意有效 ID（建议固定一个测试 lab）
  - `title`: `"A + B Problem"`
  - `statement`: 使用上述题面
  - `input_desc` / `output_desc`: 使用上述说明
  - `time_limit_ms`: 2000
  - `memory_limit_mb`: 256
- **样例测试点（TestcaseCreate）**：
  - `is_sample = true`，`input_data = "1 2\n"`，`expected_output = "3\n"`，`sort_order = 1`

> 建议由 **后端** 先用 Swagger 或脚本创建该题与样例，然后在管理端题库中确认可见。

### 11.2 竞赛（A+B 测试赛）

- **名称**：A+B 测试赛
- **类型**：`training`
- **描述**：用于验证整条链路（注册→组队→报名→做题→提交→榜单）的最小测试赛。
- **状态**：
  - 初始：`draft`
  - 联调时：设置为 `running`（或 `published` + 设置开始/结束时间）
- **关联题目**：
  - 仅包含上面的 `A + B Problem` 一道题，作为题号 `A`
- **后端配置流程（建议通过管理端 UI 完成，接口参考）**：
  1. 创建竞赛：`POST /api/v1/contests`
     - `lab_id`: 与题目相同的 lab
     - `name`: `"A+B 测试赛"`
     - `contest_type`: `"training"`
     - `status`: `"draft"`
  2. 将 A+B 题目加入竞赛：`POST /api/v1/contests/{contest_id}/problems`
     - `problem_id`: 上述 A+B 题的 ID
     - `sort_order`: `1`
     - `score`: `100`
  3. 发布竞赛：`PATCH /api/v1/contests/{contest_id}`
     - `status`: `"running"`（或 `"published"` + 合理的 `start_at/end_at`）

> 建议由 **后端 + 管理端前端** 联合完成：后端保证接口可用，前端在 `/admin/contests` 上提供「添加题目」「发布」操作。

### 11.3 学生端联调用例（以 A+B 测试赛为基准）

- **用例 1：完整闭环**
  1. 学生注册登录 → 在 `/teams` 创建队伍 → 复制队伍 ID → 另一个学生通过 ID 加入，同队人数达到 2～3 人
  2. 访问 `/contests`，看到「A+B 测试赛」
  3. 进入 `/contests/:id`，报名队伍参赛（从 `/me/teams` 选择队伍）
  4. 在「题目列表」点击 A → 进入 `/problems/:id?contest_id=...`
  5. 在题面页编写 `print(sum(map(int, input().split())))` 并提交
  6. 在右侧「最近提交」看到评测结果为 AC；回到竞赛详情页，在队伍榜中看到该队 Solved=1

- **用例 2：未配置题目/未发布竞赛**
  - 未添加题目或竞赛仍为 `draft` 时，学生端应看到明确提示（“暂无题目，请联系管理员配置竞赛题目” 或竞赛不可见），避免“空白页 + 不可提交”的困惑。

