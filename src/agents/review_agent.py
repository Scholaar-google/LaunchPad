"""Review Agent: Consistency and completeness check with human-in-the-loop."""

from __future__ import annotations

import json
from typing import Any

import structlog

from src.graph.state import AgentResult, GlobalState
from src.prompts.llm_config import get_settings, llm_call
from src.prompts.templates import AGENT_SYSTEM_PROMPTS, REVIEW_PROMPT

logger = structlog.get_logger(__name__)


async def run_review(state: GlobalState) -> dict[str, Any]:
    settings = get_settings()
    threshold = settings.confidence_threshold

    requirement = state.get("clarified_requirement", state.get("raw_requirement", ""))
    recommendation = state.get("final_recommendation", "")
    feasibility = state.get("feasibility_result", {})
    resource = state.get("resource_result", {})
    risk = state.get("risk_result", {})

    prompt = REVIEW_PROMPT.format(
        requirement=requirement,
        recommendation=recommendation,
        feasibility_result=json.dumps(feasibility, ensure_ascii=False, default=str),
        resource_result=json.dumps(resource, ensure_ascii=False, default=str),
        risk_result=json.dumps(risk, ensure_ascii=False, default=str),
        confidence_threshold=threshold,
    )

    response = await llm_call(
        AGENT_SYSTEM_PROMPTS["review"], prompt, max_tokens=2048
    )

    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        logger.error("review_json_parse_error")
        data = {
            "approved": False,
            "flags": [],
            "overall_confidence": 0.5,
            "needs_human_review": True,
        }

    overall_confidence = float(data.get("overall_confidence", 0.5))
    needs_review = data.get("needs_human_review", False) or (
        overall_confidence < threshold
    )
    approved = data.get("approved", False) and not needs_review

    result = AgentResult(
        conclusion="审核通过" if approved else "需要人工审核",
        confidence=overall_confidence,
        reasoning=(
            f"审核置信度 {overall_confidence:.0%}, "
            f"阀值 {threshold:.0%}, "
            f"标记数: {len(data.get('flags', []))}"
        ),
        missing_info=[],
    )

    return {
        "review_flags": data.get("flags", []),
        "needs_review": needs_review,
        "review_confidence": overall_confidence,
        "review_approved": approved,
        "review_agent_result": result,
        "phase": "document" if not needs_review else "review",
    }
