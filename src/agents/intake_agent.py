"""Intake Agent: Multi-turn dialogue for requirement clarification."""

from __future__ import annotations

import json
from typing import Any

import structlog

from src.graph.state import AgentResult, GlobalState, ProjectInfo
from src.prompts.llm_config import get_settings, llm_call
from src.prompts.templates import (
    INTAKE_CLARIFY_PROMPT,
    INTAKE_SUMMARIZE_PROMPT,
)

logger = structlog.get_logger(__name__)


async def run_intake(state: GlobalState) -> dict[str, Any]:
    settings = get_settings()
    max_turns = settings.max_dialog_turns
    current_turns = state.get("dialog_turns", 0)
    raw_requirement = state.get("raw_requirement", "")

    if current_turns >= max_turns or state.get("human_confirmed", False):
        result = await _summarize_requirement(
            raw_requirement,
            state.get("dialog_history", []),
        )
        return {
            "clarified_requirement": json.dumps(result, ensure_ascii=False),
            "project_info": _parse_to_project_info(result),
            "phase": "dispatch",
        }

    if current_turns == 0:
        questions = await _generate_clarifying_questions(raw_requirement, [])
    else:
        latest_answer = state.get("messages", [])[-1].content if state.get("messages") else ""
        state["dialog_history"].append({"content": latest_answer})
        questions = await _generate_clarifying_questions(
            raw_requirement,
            state.get("dialog_history", []),
        )

    state["dialog_turns"] = current_turns + 1
    return {
        "dialog_turns": state["dialog_turns"],
        "needs_review": True,
    }


async def _generate_clarifying_questions(
    requirement: str,
    dialogue_history: list[dict[str, str]],
) -> list[dict[str, str]]:
    prompt = INTAKE_CLARIFY_PROMPT.format(
        requirement=requirement,
        dialogue_history=json.dumps(dialogue_history, ensure_ascii=False),
    )
    system_prompt = "你是一个需求分析专家，请以JSON格式输出。"
    response = await llm_call(system_prompt, prompt, max_tokens=1024)

    try:
        data = json.loads(response)
        return data.get("questions", [])
    except json.JSONDecodeError:
        logger.warning("intake_clarify_json_parse_error")
        return [{"id": "q1", "text": "请更详细地描述您的项目需求，包括预期目标和约束条件。", "dimension": "general"}]


async def _summarize_requirement(
    requirement: str,
    dialogue_history: list[dict[str, str]],
) -> dict[str, Any]:
    prompt = INTAKE_SUMMARIZE_PROMPT.format(
        requirement=requirement,
        dialogue_history=json.dumps(dialogue_history, ensure_ascii=False),
    )
    system_prompt = "你是一个需求分析专家，请以JSON格式输出总结。"
    response = await llm_call(system_prompt, prompt, max_tokens=2048)

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
        constraints=data.get("constraints", []),
        stakeholders=data.get("stakeholders", []),
        priority=data.get("priority", "medium"),
    )
