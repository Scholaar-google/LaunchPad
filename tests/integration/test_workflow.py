"""Integration tests for multi-agent workflow.

NOTE: These tests require real LLM API calls (DEEPSEEK_API_KEY set).
"""

from __future__ import annotations

import pytest

from src.graph.state import create_initial_state
from src.graph.workflow import compile_workflow


@pytest.mark.integration
async def test_full_workflow_basic() -> None:
    """Basic smoke test for the full workflow."""
    workflow = compile_workflow()

    state = create_initial_state("简单考勤打卡小程序")

    config = {"configurable": {"thread_id": state["project_id"]}}
    result = await workflow.ainvoke(state, config)

    assert result["project_id"] != ""
    assert result["phase"] in ("complete", "review", "document", "error")
