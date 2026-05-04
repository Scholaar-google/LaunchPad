"""Feasibility Agent: Technical and business feasibility assessment."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog

from src.graph.state import AgentResult, GlobalState
from src.prompts.llm_config import get_settings, llm_call
from src.prompts.templates import AGENT_SYSTEM_PROMPTS, FEASIBILITY_PROMPT
from src.tools.qdrant_search import search_similar_projects

logger = structlog.get_logger(__name__)


async def run_feasibility(state: GlobalState) -> dict[str, Any]:
    requirement = state.get("clarified_requirement", state.get("raw_requirement", ""))
    focus_points = state.get("feasibility_focus", ["技术可行性", "业务可行性"])
    similar = search_similar_projects(requirement, limit=5)

    prompt = FEASIBILITY_PROMPT.format(
        requirement=requirement,
        focus_points=json.dumps(focus_points, ensure_ascii=False),
        similar_projects=json.dumps(similar, ensure_ascii=False),
    )

    response = await llm_call(
        AGENT_SYSTEM_PROMPTS["feasibility"], prompt, max_tokens=2048
    )

    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        logger.error("feasibility_json_parse_error")
        data = {
            "conclusion": "无法评估",
            "confidence": 0.1,
            "reasoning": "LLM响应解析失败",
            "technical_feasibility": "未知",
            "business_feasibility": "未知",
            "key_blockers": [],
            "missing_info": ["需要更多信息"],
        }

    result = AgentResult(
        conclusion=data.get("conclusion", ""),
        confidence=float(data.get("confidence", 0.5)),
        reasoning=data.get("reasoning", ""),
        missing_info=data.get("missing_info", []),
    )

    return {
        "feasibility_result": data,
        "feasibility_agent_result": result,
    }


async def run_feasibility_with_timeout(state: GlobalState, timeout: int = 60) -> dict[str, Any]:
    try:
        return await asyncio.wait_for(run_feasibility(state), timeout=timeout)
    except asyncio.TimeoutError:
        logger.error("feasibility_timeout", timeout_seconds=timeout)
        return {"feasibility_result": None, "feasibility_agent_result": None}
    except Exception as e:
        logger.error("feasibility_error", error=str(e))
        return {"feasibility_result": None, "feasibility_agent_result": None}
