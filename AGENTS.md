# 企业智能需求分析与项目立项 Agent 系统

## 项目概述

本系统通过多 Agent 协作，将业务人员的模糊需求描述自动转化为标准立项文档。
核心价值：替代立项前 80% 的人工工作，缩短需求到立项周期从 2~4 周到数小时。

**用户角色**：业务人员（需求提出方）、产品/研发负责人（评审方）
**输出物**：符合 SOAP 格式的标准立项文档（含可行性、资源、风险三维评估）

## 技术栈

- **运行时**：Python 3.11+
- **Agent 框架**：LangGraph（有状态多 Agent 工作流）
- **LLM**：DeepSeek V4 Pro API（deepseek-v4-pro）
- **向量数据库**：Qdrant（历史项目相似案例检索）
- **文档生成**：python-docx
- **后端 API**：FastAPI
- **前端**：React + TypeScript
- **数据库**：PostgreSQL（项目状态持久化）

## 目录结构

```
src/
├── agents/              # 各 Agent 实现
│   ├── intake_agent.py       # 接收 Agent：多轮对话、需求澄清
│   ├── dispatch_agent.py     # 调度 Agent：任务拆解、并行分发
│   ├── feasibility_agent.py  # 可行性 Agent：技术+业务可行性
│   ├── resource_agent.py     # 资源评估 Agent：人力/时间/预算
│   ├── risk_agent.py         # 风险 Agent：技术/依赖/合规风险
│   ├── synthesis_agent.py    # 综合 Agent：长链推理、冲突解决
│   ├── document_agent.py     # 文档生成 Agent：立项文档输出
│   └── review_agent.py       # 审核 Agent：一致性检查
├── graph/               # LangGraph 工作流定义
│   ├── workflow.py           # 主工作流图（节点 + 边）
│   └── state.py              # 全局状态 Schema
├── tools/               # Agent 工具函数
│   ├── qdrant_search.py      # 历史项目相似案例检索
│   ├── template_renderer.py  # 立项文档模板渲染
│   └── conflict_detector.py  # 多 Agent 结论冲突检测
├── api/                 # FastAPI 接口层
│   ├── routes.py
│   └── schemas.py
└── frontend/            # React 前端
    ├── components/
    │   ├── ChatPanel.tsx      # 对话界面
    │   └── ReasoningPanel.tsx # 推理过程可视化（侧边栏）
    └── pages/
```

辅助目录：
```
docs/
├── agent_architecture.md   # Agent 协作架构详细说明
├── reasoning_chain.md      # 长链推理设计规范
└── template_spec.md        # 立项文档模板规范
tests/
├── unit/                   # 单 Agent 单元测试
└── integration/            # 多 Agent 协作集成测试
```

## 常用命令

```bash
# 启动开发环境
make dev                    # 同时启动后端 + 前端
uvicorn src.api.routes:app --reload  # 仅后端

# 测试
pytest tests/unit/          # 单元测试
pytest tests/integration/   # 集成测试（需要真实 LLM 调用）
pytest --cov=src            # 覆盖率报告

# 数据库
alembic upgrade head        # 执行迁移
alembic revision --autogenerate -m "描述"  # 生成新迁移

# 向量数据库
python scripts/seed_qdrant.py  # 导入初始历史项目数据
```

## Agent 协作设计规范

本项目的核心是 LangGraph 有状态工作流，开发时必须遵守以下规范：

**状态管理**：所有 Agent 共享 `GlobalState`（定义在 `graph/state.py`），禁止 Agent 之间直接传参，所有中间结果必须写入全局状态。

**并行执行**：可行性、资源、风险三个 Agent 通过 LangGraph 的 `parallel` 节点并发运行，综合 Agent 等待三者全部完成后再启动。

**推理可追溯**：综合 Agent 的每一步推理必须写入 `state.reasoning_chain`（列表结构），前端 `ReasoningPanel` 实时展示，不允许跳过中间步骤直接输出结论。

**人工介入点**：审核 Agent 标记置信度 < 0.7 的判断为 `NEEDS_REVIEW`，系统暂停并等待人工确认后继续，不允许自动通过。

## 长链推理规范

综合 Agent 的推理必须严格按照以下五步结构输出，每步写入 `state.reasoning_chain`：

1. **汇总层**：提取三个并行 Agent 的核心结论与置信度
2. **冲突识别层**：调用 `conflict_detector` 找出结论间矛盾点
3. **路径推演层**：针对每个矛盾推演 2~3 种解决路径
4. **决策层**：结合企业战略优先级（从配置读取）选择最优路径
5. **输出层**：生成最终建议（立项/缓议/拒绝）+ 关键假设 + 不确定项清单

禁止跳过任何一步，即使前序步骤结论已经非常明确。

## 代码规范

- **类型注解**：所有函数必须有完整类型注解，使用 `mypy --strict` 检查
- **Agent 返回值**：统一返回 `AgentResult` dataclass，包含 `conclusion`、`confidence`、`reasoning`、`missing_info` 四个字段
- **错误处理**：LLM 调用必须有 retry 逻辑（指数退避，最多 3 次），超时统一设为 30s
- **日志**：使用 `structlog`，每个 Agent 调用记录输入 token、输出 token、耗时
- **禁止**：不允许在 Agent 实现中硬编码 prompt，所有 prompt 模板放在 `src/prompts/` 目录

## 环境变量

```bash
DEEPSEEK_API_KEY=           # 必填：DeepSeek API Key
QDRANT_URL=                 # 必填：Qdrant 服务地址
DATABASE_URL=               # 必填：PostgreSQL 连接串
MAX_DIALOG_TURNS=3          # 接收 Agent 最大追问轮次，默认 3
CONFIDENCE_THRESHOLD=0.7    # 低于此值触发人工审核
ENABLE_REASONING_STREAM=true # 是否流式输出推理过程
```

敏感文件禁止提交：`.env`、`.env.*`、`secrets/`

## 重要注意事项

- **定位边界**：系统输出始终是"辅助建议"而非"最终决策"，文档生成 Agent 的每份报告末尾必须附加免责声明
- **历史数据飞轮**：资源评估 Agent 依赖 Qdrant 中的历史项目数据，初始数据量不足 20 条时，置信度会显著偏低，这是正常现象
- **并行 Agent 超时**：三个并行 Agent 设置统一超时（默认 60s），任一超时则该 Agent 返回空结果，综合 Agent 必须能处理部分缺失的情况
- **前端推理面板**：`ReasoningPanel` 通过 SSE 实时接收 `state.reasoning_chain` 更新，后端必须在每步推理完成后立即 flush

## 参考文档

- See docs/agent_architecture.md - Agent 协作架构与状态流转详细说明
- See docs/reasoning_chain.md - 长链推理五步结构规范与示例
- See docs/template_spec.md - 立项文档模板字段规范
