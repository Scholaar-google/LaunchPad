# LaunchPad (Demo)

> **概念验证项目** — 演示多 Agent 协作在需求分析场景中的应用，非生产就绪产品。

---

## 这是什么

LaunchPad 是一个**技术演示项目**，展示了如何使用 LangGraph + DeepSeek V4 Pro 构建多 Agent 协作系统。

**场景**：业务人员用自然语言描述需求 → 8 个 Agent 自动协作 → 输出标准立项文档（Word）

**核心演示点**：
- 多 Agent 任务编排（LangGraph 有状态工作流）
- 并行分析 + 长链推理（五步推理链）
- SSE 流式推送（前端实时可视化推演过程）
- Agent 独立 LLM 配置（不同 Agent 可用不同模型厂商）
- 人工审核嵌入（置信度 < 0.7 自动触发）

---

## 它不是什么

| 不是 | 说明 |
|------|------|
| 生产级产品 | 使用内存存储、伪向量检索、无鉴权、无持久化 |
| 完整的立项工具 | 缺少审批流、权限管理、多租户、审计日志 |
| 商业可用 | 仅供学习 LangGraph/Agent 架构设计参考 |

---

## 架构一览

```
用户输入 → Intake(对话澄清) → Dispatch(任务拆解)
                                    ├── Feasibility(可行性) ──┐
                                    ├── Resource(资源评估) ────┤ → Synthesis(长链推理)
                                    └── Risk(风险评估) ───────┘         │
                                                                        ▼
                                                                 Review(审核)
                                                                   │
                                                              Document(.docx 输出)
```

8 个 Agent：`intake` / `dispatch` / `feasibility` / `resource` / `risk` / `synthesis` / `review` / `document`

---

## 快速启动（开发者）

```bash
cp .env.example .env   # 填入 DEEPSEEK_API_KEY
make dev               # 后端 :8000 + 前端 :3000
```

前端 `http://localhost:3000`，输入项目需求即可体验完整流程。

---

## 已知限制

- 向量检索使用伪嵌入（需要接入真实 Embedding 模型）
- 项目数据存储在内存，服务重启丢失
- 无用户认证 / 权限控制
- 前端无移动端适配
- 文档模板为简化版（非标准字号/行距）

---

## 技术栈

`Python 3.11+` `LangGraph` `DeepSeek V4 Pro` `Qdrant` `FastAPI` `React + TypeScript` `python-docx`

---

## 文档

- [Agent 协作架构](docs/agent_architecture.md)
- [长链推理规范](docs/reasoning_chain.md)
- [立项文档模板](docs/template_spec.md)
- [开发规范](AGENTS.md)
