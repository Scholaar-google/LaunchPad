"""Intake Agent: Multi-turn dialogue for requirement clarification."""

from __future__ import annotations

import json
from typing import Any

import structlog

from src.graph.state import AgentResult, GlobalState, ProjectInfo, WorkflowPhase
from src.prompts.llm_config import get_settings, llm_call
from src.prompts.templates import (
    AGENT_SYSTEM_PROMPTS,
    INTAKE_CLARIFY_PROMPT,
    INTAKE_SUMMARIZE_PROMPT,
)

logger = structlog.get_logger(__name__)


async def run_intake(state: GlobalState) -> dict[str, Any]:
    settings = get_settings()
    max_turns = settings.max_dialog_turns
    current_turns = state.get("dialog_turns", 0)
    raw_requirement = state.get("raw_requirement", "")

    if not raw_requirement or not raw_requirement.strip():
        return {
            "phase": WorkflowPhase.ERROR,
            "error": "需求描述不能为空",
        }

    if current_turns >= max_turns or state.get("human_confirmed", False):
        summary = await _summarize_requirement(
            raw_requirement,
            state.get("dialog_history", []),
        )
        result = AgentResult(
            conclusion=summary.get("title", "需求已澄清"),
            confidence=0.8,
            reasoning=f"经过 {current_turns} 轮对话完成需求澄清",
            missing_info=summary.get("missing_info", []),
        )
        return {
            "clarified_requirement": json.dumps(summary, ensure_ascii=False),
            "project_info": _parse_to_project_info(summary),
            "intake_agent_result": result,
            "phase": WorkflowPhase.DISPATCH,
            "questions": [],
        }

    dialog_history = state.get("dialog_history", [])
    new_history = list(dialog_history)

    if current_turns == 0:
        questions = await _generate_clarifying_questions(raw_requirement, [])
    else:
        messages = state.get("messages", [])
        latest_answer = ""
        if messages:
            last_msg = messages[-1]
            if isinstance(last_msg, str):
                latest_answer = last_msg
            elif hasattr(last_msg, "content"):
                latest_answer = str(last_msg.content)
            elif isinstance(last_msg, dict):
                latest_answer = str(last_msg.get("content", last_msg))
        new_history = list(dialog_history) + [
            {"role": "user", "content": latest_answer}
        ]
        questions = await _generate_clarifying_questions(
            raw_requirement,
            new_history,
        )

    new_turns = current_turns + 1
    return {
        "dialog_turns": new_turns,
        "dialog_history": new_history,
        "questions": questions,
        "phase": WorkflowPhase.INTAKE,
    }


async def _generate_clarifying_questions(
    requirement: str,
    dialogue_history: list[dict[str, str]],
) -> list[dict[str, str]]:
    prompt = INTAKE_CLARIFY_PROMPT.format(
        requirement=requirement,
        dialogue_history=json.dumps(dialogue_history, ensure_ascii=False),
    )
    response = await llm_call(
        AGENT_SYSTEM_PROMPTS["intake_clarify"], prompt, agent_name="intake", max_tokens=1024
    )

    try:
        data = json.loads(response)
        return data.get("questions", [])
    except json.JSONDecodeError:
        logger.warning("intake_clarify_json_parse_error")
        return [
            {
                "id": "q1",
                "text": "请更详细地描述您的项目需求，包括预期目标和约束条件。",
                "dimension": "general",
            }
        ]


async def _summarize_requirement(
    requirement: str,
    dialogue_history: list[dict[str, str]],
) -> dict[str, Any]:
    prompt = INTAKE_SUMMARIZE_PROMPT.format(
        requirement=requirement,
        dialogue_history=json.dumps(dialogue_history, ensure_ascii=False),
    )
    response = await llm_call(
        AGENT_SYSTEM_PROMPTS["intake_summarize"], prompt, agent_name="intake", max_tokens=2048
    )

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        logger.error("intake_summarize_json_parse_error")
        return {
            "title": "未命名项目",
            "description": requirement[:200],
            "objectives": [],
            "scope_in": [],
            "scope_out": [],
            "constraints": [],
            "stakeholders": [],
            "priority": "medium",
        }


def _parse_to_project_info(data: dict[str, Any]) -> ProjectInfo:
    return ProjectInfo(
        title=data.get("title", "未命名项目"),
        description=data.get("description", ""),
        background=data.get("background", ""),
        objectives=data.get("objectives", []),
        scope_in=data.get("scope_in", []),
        scope_out=data.get("scope_out", []),
        constraints=data.get("constraints", []),
        stakeholders=data.get("stakeholders", []),
        priority=data.get("priority", "medium"),
    )
