"""Global state schema for the LangGraph multi-agent workflow."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Sequence, TypedDict

from langgraph.graph.message import add_messages


class WorkflowPhase(str, Enum):
    INIT = "init"
    INTAKE = "intake"
    DISPATCH = "dispatch"
    PARALLEL_ANALYSIS = "parallel_analysis"
    SYNTHESIS = "synthesis"
    REVIEW = "review"
    DOCUMENT = "document"
    COMPLETE = "complete"
    ERROR = "error"


class FinalDecision(str, Enum):
    APPROVE = "approve"
    DEFER = "defer"
    REJECT = "reject"


@dataclass
class AgentResult:
    conclusion: str
    confidence: float
    reasoning: str
    missing_info: list[str] = field(default_factory=list)


@dataclass
class ReasoningStep:
    layer: int
    title: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: float = 1.0


@dataclass
class ConflictItem:
    topic: str
    source_a: str
    conclusion_a: str
    source_b: str
    conclusion_b: str
    resolution_paths: list[str] = field(default_factory=list)
    resolved_path: str | None = None


class ParallelResults(TypedDict, total=False):
    feasibility: AgentResult | None
    resource: AgentResult | None
    risk: AgentResult | None


class ProjectInfo(TypedDict, total=False):
    title: str
    description: str
    background: str
    objectives: list[str]
    scope_in: list[str]
    scope_out: list[str]
    constraints: list[str]
    stakeholders: list[str]
    priority: str


class GlobalState(TypedDict, total=False):
    project_id: str
    phase: WorkflowPhase
    messages: Annotated[list[Any], add_messages]
    project_info: ProjectInfo
    raw_requirement: str
    clarified_requirement: str | None
    dialog_history: list[dict[str, str]]
    dialog_turns: int
    questions: list[dict[str, str]]
    feasibility_focus: list[str]
    resource_focus: list[str]
    risk_focus: list[str]
    parallel_results: ParallelResults
    similar_projects: list[dict[str, Any]]
    rationale: list[dict[str, Any]]
    feasibility_result: dict[str, Any] | None
    resource_result: dict[str, Any] | None
    risk_result: dict[str, Any] | None
    feasibility_agent_result: AgentResult | None
    resource_agent_result: AgentResult | None
    risk_agent_result: AgentResult | None
    dispatch_agent_result: AgentResult | None
    intake_agent_result: AgentResult | None
    synthesis_agent_result: AgentResult | None
    review_agent_result: AgentResult | None
    document_agent_result: AgentResult | None
    reasoning_chain: list[ReasoningStep]
    conflicts: list[ConflictItem]
    review_flags: list[dict[str, Any]]
    needs_review: bool
    review_attempts: int
    final_decision: FinalDecision | None
    final_recommendation: str
    key_assumptions: list[str]
    uncertainties: list[str]
    document_path: str | None
    error: str | None
    human_confirmed: bool
    created_at: str | None


def create_initial_state(raw_requirement: str) -> GlobalState:
    return GlobalState(
        project_id=str(uuid.uuid4()),
        phase=WorkflowPhase.INIT,
        messages=[],
        project_info={},
        raw_requirement=raw_requirement,
        clarified_requirement=None,
        dialog_history=[],
        dialog_turns=0,
        parallel_results={},
        similar_projects=[],
        reasoning_chain=[],
        conflicts=[],
        review_flags=[],
        needs_review=False,
        final_decision=None,
        final_recommendation="",
        key_assumptions=[],
        uncertainties=[],
        document_path=None,
        error=None,
        human_confirmed=False,
    )
