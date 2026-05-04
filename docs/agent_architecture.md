# Agent 协作架构与状态流转详细说明

## 架构概览

本系统采用 **分层多 Agent 协作架构**，基于 LangGraph 有状态工作流。

```
┌─────────────┐
│  业务人员    │ 输入模糊需求
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Intake Agent│ 多轮对话澄清需求
└──────┬──────┘
       │ 结构化需求
       ▼
┌─────────────┐
│Dispatch Agent│ 任务拆解为3个并行维度
└──────┬──────┘
       │
   ┌───┼───┐
   ▼   ▼   ▼
┌────┐┌────┐┌────┐
│Fea ││Res ││Risk│ ← 并行执行（asyncio.wait_for 60s 超时）
└──┬─┘└──┬─┘└──┬─┘
   └──┬──┴──┬──┘
      │     │
      ▼     │
┌─────────┐ │
│Synthesis│◄┘ 长链推理 + 冲突解决
└────┬────┘
     │
     ▼
┌─────────┐
│ Review  │ 一致性检查 + 人工审核
└────┬────┘
     │ (confidence < 0.7 → 等待人工确认)
     ▼
┌─────────┐
│Document │ 生成 SOAP 立项文档 → output/ 目录
└────┬────┘
     │
     ▼
  COMPLETE → 可通过 API 下载
```

## 状态流转

### 1. INIT -> INTAKE
- 用户提交原始需求描述
- 系统创建 `GlobalState`，分配 `project_id`

### 2. INTAKE（循环）
- Intake Agent 分析需求信息缺口
- 每次追问 1-2 个关键问题
- 最多 `MAX_DIALOG_TURNS` 轮（默认 3 轮）
- 达到上限或用户确认后进入 DISPATCH
- 返回值：`intake_agent_result` (AgentResult)

### 3. DISPATCH
- Dispatch Agent 拆解需求为三个分析维度
- 生成 feasible/resource/risk 三个 focus_points
- 返回值：`dispatch_agent_result` (AgentResult)

### 4. PARALLEL_ANALYSIS（并行）
- Feasibility Agent：技术可行性 + 业务可行性
- Resource Agent：人力/时间/预算评估（含历史数据量下调置信度）
- Risk Agent：技术/依赖/合规风险识别
- 三个 Agent 并发执行，通过 `asyncio.wait_for()` 强制执行 60s 超时
- 任一超时则返回 `None`，综合 Agent 需处理部分缺失
- 每个 Agent 返回 `{name}_result` (LLM 原始 dict) + `{name}_agent_result` (AgentResult)

### 5. SYNTHESIS（五步推理链）
- 第1步：汇总三个维度的核心结论
- 第2步：调用 conflict_detector 识别矛盾
- 第3步：推演每个矛盾的 2~3 种解决路径
- 第4步：结合企业战略优先级（`CORPORATE_STRATEGY` 配置）选择最优路径
  - `growth`：快速增长，高投入高产出，容忍风险
  - `balanced`：稳健发展，性价比优先，中等风险偏好（默认）
  - `conservative`：成本控制，安全第一，保守策略
- 第5步：输出最终建议 + 关键假设 + 不确定项
- 构建本地 `reasoning_chain` 列表通过返回 dict 写入 state（避免原地修改）
- 返回值：`synthesis_agent_result` (AgentResult)
- 每步结果写入 `reasoning_chain`，前端通过 SSE 实时展示

### 6. REVIEW（人工介入点）
- Review Agent 检查一致性
- 置信度 < `CONFIDENCE_THRESHOLD` (0.7) 标记 `NEEDS_REVIEW`
- 系统暂停，等待人工确认
- 确认后进入 DOCUMENT
- 返回值：`review_agent_result` (AgentResult)

### 7. DOCUMENT
- 生成符合 template_spec 规范的 .docx 立项文档
- 文档末尾附加免责声明
- 文档版本号 v1.0
- 保存到项目相对路径 `output/` 目录（已在 .gitignore 中排除）
- 可通过 `/api/projects/{id}/download` 接口下载
- 返回值：`document_agent_result` (AgentResult)

### 8. COMPLETE
- 工作流结束，文档可供下载

## 全局状态 (GlobalState)

所有 Agent 通过 GlobalState 共享数据，禁止 Agent 间直接传参。
Workflow 节点返回 dict 由 LangGraph 自动合并入 state，**禁止在节点函数内原地修改 state 对象**。

核心字段：
- `project_id`：唯一项目标识
- `phase`：当前工作流阶段
- `raw_requirement` / `clarified_requirement`：原始/澄清后的需求
- `project_info`：结构化项目信息（含 scope_in/scope_out）
- `dialog_history` / `dialog_turns`：对话历史与轮次计数
- `feasibility_focus` / `resource_focus` / `risk_focus`：各 Agent 的关注点
- `feasibility_result` / `resource_result` / `risk_result`：三个并行 Agent 的 LLM 原始结果
- `*_agent_result`：各 Agent 的 AgentResult 对象
- `reasoning_chain`：推理步骤列表（SSE 推送源）
- `conflicts`：冲突检测结果
- `final_decision`：最终决策 (approve/defer/reject)
- `review_flags` / `needs_review` / `human_confirmed`：审核状态
- `document_path`：生成的文档路径

## 项目持久化

- LangGraph 使用 `MemorySaver` 内存检查点
- API 层维护 `_in_memory_projects` 字典缓存项目状态
- `GET /api/projects` 从内存字典读取项目列表
- PostgreSQL ORM 模型 (`schemas.py`) 已定义，可用于后续迁移到数据库持久化

## 关键设计决策

1. **并行 -> 汇总**：三个分析 Agent 完全独立，允许阶段间信息不对称
2. **长链推理强制五步**：综合 Agent 必须完成五步，禁止跳过
3. **人工审核嵌入**：不是事后审批，而是流程内嵌的人工判断点
4. **SSE 流式推送**：推理步骤实时更新前端推理面板，轮询间隔 0.5s
5. **Strategy 可配置**：企业战略优先级通过 `CORPORATE_STRATEGY` 环境变量配置，影响综合决策层
6. **Prompt 集中管理**：`templates.py` 分为 `SYSTEM_PROMPTS`（任务 prompt）和 `AGENT_SYSTEM_PROMPTS`（Agent 系统 prompt），Agent 代码通过字典引用
