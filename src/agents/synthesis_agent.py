"""Synthesis Agent: Long-chain reasoning for conflict resolution and final decision.

Implements the 5-step reasoning chain:
1. Summary layer
2. Conflict identification layer
3. Path exploration layer
4. Decision layer (incorporates corporate strategy)
5. Output layer
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from src.graph.state import AgentResult, ConflictItem, FinalDecision, GlobalState, ReasoningStep
from src.prompts.llm_config import get_settings, llm_call
from src.prompts.templates import AGENT_SYSTEM_PROMPTS, SYNTHESIS_PROMPT
from src.tools.conflict_detector import detect_conflicts

logger = structlog.get_logger(__name__)


def _get_corporate_strategy_context(strategy: str) -> str:
    strategies: dict[str, str] = {
        "growth": "企业当前战略优先级为：快速增长、抢占市场。优先选择高投入高产出的路径，容忍适度风险。",
        "balanced": "企业当前战略优先级为：稳健发展、风险平衡。优先选择性价比最优的路径，中等风险偏好。",
        "conservative": "企业当前战略优先级为：成本控制、安全第一。优先选择低风险低成本的路径，保守策略。",
    }
    return strategies.get(strategy, strategies["balanced"])


async def run_synthesis(state: GlobalState) -> dict[str, Any]:
    settings = get_settings()
    corporate_strategy = _get_corporate_strategy_context(settings.corporate_strategy)

    feasibility = state.get("feasibility_result")
    resource = state.get("resource_result")
    risk = state.get("risk_result")
    requirement = state.get("clarified_requirement", state.get("raw_requirement", ""))

    reasoning_chain: list[ReasoningStep] = []

    # ---- Step 1: Summary Layer ----
    step1 = ReasoningStep(
        layer=1,
        title="汇总层 - 提取核心结论",
        content=_build_summary(feasibility, resource, risk),
    )
    reasoning_chain.append(step1)

    # ---- Step 2: Conflict Identification Layer ----
    conflicts = detect_conflicts(feasibility, resource, risk)
    step2 = ReasoningStep(
        layer=2,
        title="冲突识别层 - 检测结论矛盾",
        content=_format_conflicts(conflicts),
    )
    reasoning_chain.append(step2)

    # ---- Step 3: Path Exploration Layer ----
    step3_content = _explore_paths(conflicts)
    step3 = ReasoningStep(
        layer=3,
        title="路径推演层 - 推演解决路径",
        content=step3_content,
    )
    reasoning_chain.append(step3)

    # ---- Step 4 & 5: LLM-based Decision and Output ----
    prompt = SYNTHESIS_PROMPT.format(
        corporate_strategy=corporate_strategy,
        requirement=requirement,
        feasibility_result=json.dumps(feasibility, ensure_ascii=False, default=str),
        resource_result=json.dumps(resource, ensure_ascii=False, default=str),
        risk_result=json.dumps(risk, ensure_ascii=False, default=str),
        conflicts=json.dumps(
            [_conflict_to_dict(c) for c in conflicts], ensure_ascii=False
        ),
    )

    response = await llm_call(
        AGENT_SYSTEM_PROMPTS["synthesis"], prompt, agent_name="synthesis", max_tokens=4096
    )

    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        logger.error("synthesis_json_parse_error")
        data = _build_fallback_decision(feasibility, resource, risk)

    # ---- Step 4: Decision Layer ----
    step4 = ReasoningStep(
        layer=4,
        title="决策层 - 结合企业战略选择最优路径",
        content=f"{corporate_strategy}\n\n{data.get('decision_reasoning', '结合企业战略优先级进行决策')}",
    )
    reasoning_chain.append(step4)

    # ---- Step 5: Output Layer ----
    recommendation = data.get("recommendation", "")
    step5 = ReasoningStep(
        layer=5,
        title="输出层 - 最终建议",
        content=recommendation,
    )
    reasoning_chain.append(step5)

    final_decision_str = data.get("final_decision", "defer")
    try:
        final_decision = FinalDecision(final_decision_str)
    except ValueError:
        final_decision = FinalDecision.DEFER

    return {
        "final_decision": final_decision,
        "final_recommendation": recommendation,
        "key_assumptions": data.get("key_assumptions", []),
        "uncertainties": data.get("uncertainties", []),
        "conflicts": [_conflict_to_dict(c) for c in conflicts],
        "reasoning_chain": reasoning_chain,
        "synthesis_agent_result": AgentResult(
            conclusion=f"最终建议: {final_decision.value}",
            confidence=0.85,
            reasoning=recommendation,
            missing_info=[],
        ),
        "phase": "review",
    }


def _build_summary(
    feasibility: dict[str, Any] | None,
    resource: dict[str, Any] | None,
    risk: dict[str, Any] | None,
) -> str:
    lines: list[str] = []

    if feasibility:
        lines.append(
            f"可行性分析: {feasibility.get('conclusion', '无')} "
            f"(置信度: {feasibility.get('confidence', 0):.0%})"
        )
    else:
        lines.append("可行性分析: 无数据（超时或失败）")

    if resource:
        lines.append(
            f"资源评估: {resource.get('conclusion', '无')} "
            f"(置信度: {resource.get('confidence', 0):.0%})"
        )
    else:
        lines.append("资源评估: 无数据（超时或失败）")

    if risk:
        lines.append(
            f"风险评估: {risk.get('conclusion', '无')} "
            f"(置信度: {risk.get('confidence', 0):.0%})"
        )
    else:
        lines.append("风险评估: 无数据（超时或失败）")

    return "\n".join(lines)


def _format_conflicts(conflicts: list[ConflictItem]) -> str:
    if not conflicts:
        return "未发现结论间矛盾。"
    lines = [f"发现 {len(conflicts)} 个矛盾点:"]
    for i, c in enumerate(conflicts, 1):
        lines.append(
            f"{i}. {c.topic}: {c.source_a}认为'{c.conclusion_a}', "
            f"但{c.source_b}认为'{c.conclusion_b}'"
        )
    return "\n".join(lines)


def _explore_paths(conflicts: list[ConflictItem]) -> str:
    if not conflicts:
        return "无矛盾需要推演路径。"
    lines: list[str] = []
    for i, c in enumerate(conflicts, 1):
        lines.append(f"矛盾 {i} ({c.topic}):")
        for j, path in enumerate(c.resolution_paths, 1):
            lines.append(f"  路径 {j}: {path}")
    return "\n".join(lines)


def _conflict_to_dict(c: ConflictItem) -> dict[str, Any]:
    return {
        "topic": c.topic,
        "source_a": c.source_a,
        "conclusion_a": c.conclusion_a,
        "source_b": c.source_b,
        "conclusion_b": c.conclusion_b,
        "resolution_paths": c.resolution_paths,
    }


def _build_fallback_decision(
    feasibility: dict[str, Any] | None,
    resource: dict[str, Any] | None,
    risk: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "final_decision": "defer",
        "recommendation": "由于部分分析模块未能正常返回结果，建议补充信息后重新评估。",
        "decision_reasoning": "综合合成失败，按保守策略建议缓议。",
        "key_assumptions": ["各分析模块评估结果可能不完整"],
        "uncertainties": ["可行性分析数据缺失", "资源评估数据缺失", "风险评估数据缺失"],
    }
