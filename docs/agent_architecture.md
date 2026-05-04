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
│Fea ││Res ││Risk│ ← 并行执行
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
     │
     ▼
┌─────────┐
│Document │ 生成 SOAP 立项文档
└─────────┘
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

### 3. DISPATCH
- Dispatch Agent 拆解需求为三个分析维度
- 生成 feasible/resource/risk 三个 focus_points

### 4. PARALLEL_ANALYSIS（并行）
- Feasibility Agent：技术可行性 + 业务可行性
- Resource Agent：人力/时间/预算评估
- Risk Agent：技术/依赖/合规风险识别
- 三个 Agent 并发执行，统一超时 60s
- 任一超时则返回 `None`，综合 Agent 需处理部分缺失

### 5. SYNTHESIS（五步推理链）
- 第1步：汇总三个维度的核心结论
- 第2步：调用 conflict_detector 识别矛盾
- 第3步：推演每个矛盾的 2~3 种解决路径
- 第4步：结合企业战略选择最优路径
- 第5步：输出最终建议 + 关键假设 + 不确定项
- 每步结果写入 `reasoning_chain`，前端通过 SSE 实时展示

### 6. REVIEW（人工介入点）
- Review Agent 检查一致性
- 置信度 < `CONFIDENCE_THRESHOLD` (0.7) 标记 `NEEDS_REVIEW`
- 系统暂停，等待人工确认
- 确认后进入 DOCUMENT

### 7. DOCUMENT
- 生成符合 template_spec 规范的 .docx 立项文档
- 文档末尾附加免责声明
- 保存到 `output/` 目录

### 8. COMPLETE
- 工作流结束，文档可供下载

## 全局状态 (GlobalState)

所有 Agent 通过 GlobalState 共享数据，禁止 Agent 间直接传参。

核心字段：
- `project_id`：唯一项目标识
- `phase`：当前工作流阶段
- `raw_requirement` / `clarified_requirement`：原始/澄清后的需求
- `parallel_results`：三个并行 Agent 的结果
- `reasoning_chain`：推理步骤列表（SSE 推送源）
- `conflicts`：冲突检测结果
- `final_decision`：最终决策 (approve/defer/reject)
- `needs_review` / `human_confirmed`：人工审核状态

## 关键设计决策

1. **并行 -> 汇总**：三个分析 Agent 完全独立，允许阶段间信息不对称
2. **长链推理强制五步**：综合 Agent 必须完成五步，禁止跳过
3. **人工审核嵌入**：不是事后审批，而是流程内嵌的人工判断点
4. **SSE 流式推送**：推理步骤实时更新前端推理面板
