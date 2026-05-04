"""Unit tests for prompt templates."""

from __future__ import annotations

from src.prompts.templates import (
    AGENT_SYSTEM_PROMPTS,
    FEASIBILITY_PROMPT,
    RESOURCE_PROMPT,
    RISK_PROMPT,
    SYNTHESIS_PROMPT,
    get_prompt,
    format_prompt,
)


def test_all_prompts_exist() -> None:
    for name in [
        "intake", "dispatch", "feasibility", "resource",
        "risk", "synthesis", "review", "document",
    ]:
        prompt = get_prompt(name)
        assert len(prompt) > 0


def test_all_system_prompts_exist() -> None:
    for name in [
        "intake_clarify", "intake_summarize", "dispatch",
        "feasibility", "resource", "risk", "synthesis", "review",
    ]:
        assert name in AGENT_SYSTEM_PROMPTS
        assert len(AGENT_SYSTEM_PROMPTS[name]) > 0


def test_format_feasibility_prompt() -> None:
    result = format_prompt(
        "feasibility",
        requirement="测试需求",
        focus_points="[]",
        similar_projects="[]",
    )
    assert "测试需求" in result


def test_format_resource_prompt() -> None:
    result = format_prompt(
        "resource",
        requirement="测试需求",
        focus_points="[]",
        similar_projects="[]",
    )
    assert "测试需求" in result


def test_format_risk_prompt() -> None:
    result = format_prompt(
        "risk",
        requirement="测试需求",
        focus_points="[]",
        similar_projects="[]",
    )
    assert "测试需求" in result


def test_format_synthesis_prompt() -> None:
    result = format_prompt(
        "synthesis",
        requirement="测试需求",
        feasibility_result="{}",
        resource_result="{}",
        risk_result="{}",
        conflicts="[]",
    )
    assert "测试需求" in result
