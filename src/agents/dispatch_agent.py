"""Dispatch Agent: Task decomposition and parallel distribution."""

from __future__ import annotations

import json
from typing import Any

import structlog

from src.graph.state import AgentResult, GlobalState
from src.prompts.llm_config import llm_call
from src.prompts.templates import AGENT_SYSTEM_PROMPTS, DISPATCH_PROMPT

logger = structlog.get_logger(__name__)


async def run_dispatch(state: GlobalState) -> dict[str, Any]:
    clarified = state.get("clarified_requirement", state.get("raw_requirement", ""))

    prompt = DISPATCH_PROMPT.format(clarified_requirement=clarified)

    response = await llm_call(
        AGENT_SYSTEM_PROMPTS["dispatch"], prompt, agent_name="dispatch", max_tokens=2048
    )

    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        logger.error("dispatch_json_parse_error")
        data = {
            "tasks": [
                {"agent": "feasibility", "focus_points": ["技术可行性", "业务可行性"]},
                {"agent": "resource", "focus_points": ["人力评估", "时间评估", "预算评估"]},
                {"agent": "risk", "focus_points": ["技术风险", "依赖风险", "合规风险"]},
            ]
        }

    feasibility_points = _extract_focus_points(data, "feasibility")
    resource_points = _extract_focus_points(data, "resource")
    risk_points = _extract_focus_points(data, "risk")

    logger.info(
        "dispatch_complete",
        feasibility_count=len(feasibility_points),
        resource_count=len(resource_points),
        risk_count=len(risk_points),
    )

    result = AgentResult(
        conclusion=f"已拆解为 3 个并行维度：可行性({len(feasibility_points)}项)、资源({len(resource_points)}项)、风险({len(risk_points)}项)",
        confidence=0.9,
        reasoning=f"根据澄清需求自动拆解分析任务",
        missing_info=[],
    )

    return {
        "feasibility_focus": feasibility_points,
        "resource_focus": resource_points,
        "risk_focus": risk_points,
        "dispatch_agent_result": result,
        "phase": "parallel_analysis",
    }


def _extract_focus_points(data: dict[str, Any], agent: str) -> list[str]:
    tasks = data.get("tasks", [])
    for task in tasks:
        if task.get("agent") == agent:
            return task.get("focus_points", [])
    return []
