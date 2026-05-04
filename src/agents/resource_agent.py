"""Resource Agent: Human/time/budget resource assessment."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog

from src.graph.state import AgentResult, GlobalState
from src.prompts.llm_config import get_settings, llm_call
from src.prompts.templates import AGENT_SYSTEM_PROMPTS, RESOURCE_PROMPT
from src.tools.qdrant_search import get_project_count, search_similar_projects

logger = structlog.get_logger(__name__)


async def run_resource(state: GlobalState) -> dict[str, Any]:
    requirement = state.get("clarified_requirement", state.get("raw_requirement", ""))
    focus_points = state.get("resource_focus", ["人力评估", "时间评估", "预算评估"])
    similar = search_similar_projects(requirement, limit=5)

    project_count = get_project_count()
    data_confidence = min(project_count / 20.0, 1.0) if project_count < 20 else 1.0

    prompt = RESOURCE_PROMPT.format(
        requirement=requirement,
        focus_points=json.dumps(focus_points, ensure_ascii=False),
        similar_projects=json.dumps(similar, ensure_ascii=False),
    )

    response = await llm_call(
        AGENT_SYSTEM_PROMPTS["resource"], prompt, max_tokens=2048
    )

    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        logger.error("resource_json_parse_error")
        data = {
            "conclusion": "无法评估",
            "confidence": 0.1,
            "reasoning": "LLM响应解析失败",
            "team_size": 0,
            "timeline_months": 0,
            "budget_range": "未知",
            "dependencies": [],
            "missing_info": ["需要更多信息"],
        }

    raw_confidence = float(data.get("confidence", 0.5))
    adjusted_confidence = raw_confidence * data_confidence

    result = AgentResult(
        conclusion=data.get("conclusion", ""),
        confidence=adjusted_confidence,
        reasoning=data.get("reasoning", ""),
        missing_info=data.get("missing_info", []),
    )

    return {
        "resource_result": data,
        "resource_agent_result": result,
    }


async def run_resource_with_timeout(state: GlobalState, timeout: int = 60) -> dict[str, Any]:
    try:
        return await asyncio.wait_for(run_resource(state), timeout=timeout)
    except asyncio.TimeoutError:
        logger.error("resource_timeout", timeout_seconds=timeout)
        return {"resource_result": None, "resource_agent_result": None}
    except Exception as e:
        logger.error("resource_error", error=str(e))
        return {"resource_result": None, "resource_agent_result": None}
