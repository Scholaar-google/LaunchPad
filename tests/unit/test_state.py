"""Unit tests for state management."""

from __future__ import annotations

from src.graph.state import create_initial_state, WorkflowPhase


def test_create_initial_state() -> None:
    state = create_initial_state("做一个考勤系统")
    assert state["phase"] == WorkflowPhase.INIT
    assert state["raw_requirement"] == "做一个考勤系统"
    assert state["dialog_turns"] == 0
    assert state["project_id"] != ""
