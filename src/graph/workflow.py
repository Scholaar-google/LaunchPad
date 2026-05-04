"""Main LangGraph workflow definition.

Nodes: intake -> dispatch -> [feasibility || resource || risk] -> synthesis -> review -> document
"""

from __future__ import annotations

from typing import Any, Literal

import structlog
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.agents.dispatch_agent import run_dispatch
from src.agents.document_agent import run_document
from src.agents.feasibility_agent import run_feasibility_with_timeout
from src.agents.intake_agent import run_intake
from src.agents.resource_agent import run_resource_with_timeout
from src.agents.review_agent import run_review
from src.agents.risk_agent import run_risk_with_timeout
from src.agents.synthesis_agent import run_synthesis
from src.graph.state import GlobalState, WorkflowPhase
from src.prompts.llm_config import get_settings

logger = structlog.get_logger(__name__)

_PARALLEL_TIMEOUT = get_settings().parallel_agent_timeout


async def _intake_node(state: GlobalState) -> dict[str, Any]:
    logger.info("workflow_intake_start", project_id=state.get("project_id"))
    result = await run_intake(state)
    return result


async def _dispatch_node(state: GlobalState) -> dict[str, Any]:
    logger.info("workflow_dispatch_start", project_id=state.get("project_id"))
    return await run_dispatch(state)


async def _feasibility_node(state: GlobalState) -> dict[str, Any]:
    logger.info("workflow_feasibility_start", project_id=state.get("project_id"))
    return await run_feasibility_with_timeout(state, timeout=_PARALLEL_TIMEOUT)


async def _resource_node(state: GlobalState) -> dict[str, Any]:
    logger.info("workflow_resource_start", project_id=state.get("project_id"))
    return await run_resource_with_timeout(state, timeout=_PARALLEL_TIMEOUT)


async def _risk_node(state: GlobalState) -> dict[str, Any]:
    logger.info("workflow_risk_start", project_id=state.get("project_id"))
    return await run_risk_with_timeout(state, timeout=_PARALLEL_TIMEOUT)


async def _parallel_results_node(state: GlobalState) -> dict[str, Any]:
    logger.info(
        "workflow_parallel_collect",
        has_feasibility=state.get("feasibility_result") is not None,
        has_resource=state.get("resource_result") is not None,
        has_risk=state.get("risk_result") is not None,
    )
    return {}


async def _synthesis_node(state: GlobalState) -> dict[str, Any]:
    logger.info("workflow_synthesis_start", project_id=state.get("project_id"))
    return await run_synthesis(state)


async def _review_node(state: GlobalState) -> dict[str, Any]:
    logger.info("workflow_review_start", project_id=state.get("project_id"))
    return await run_review(state)


async def _document_node(state: GlobalState) -> dict[str, Any]:
    logger.info("workflow_document_start", project_id=state.get("project_id"))
    return await run_document(state)


def _should_continue_intake(state: GlobalState) -> Literal["intake", "dispatch"]:
    if state.get("phase") == WorkflowPhase.DISPATCH:
        return "dispatch"
    return "intake"


def _should_continue_review(state: GlobalState) -> Literal["review", "document"]:
    needs_review = state.get("needs_review", False)
    human_confirmed = state.get("human_confirmed", False)
    review_attempts = state.get("review_attempts", 0)

    if needs_review and not human_confirmed:
        if review_attempts >= 3:
            logger.warning("review_max_attempts_reached", attempts=review_attempts)
            return "document"
        return "review"
    return "document"


def build_workflow() -> StateGraph:
    workflow = StateGraph(GlobalState)

    # Add nodes
    workflow.add_node("intake", _intake_node)
    workflow.add_node("dispatch", _dispatch_node)
    workflow.add_node("feasibility", _feasibility_node)
    workflow.add_node("resource", _resource_node)
    workflow.add_node("risk", _risk_node)
    workflow.add_node("parallel_results", _parallel_results_node)
    workflow.add_node("synthesis", _synthesis_node)
    workflow.add_node("review", _review_node)
    workflow.add_node("document", _document_node)

    # Entry point
    workflow.set_entry_point("intake")

    # Intake -> (loop until done) -> dispatch
    workflow.add_conditional_edges(
        "intake",
        _should_continue_intake,
        {"intake": "intake", "dispatch": "dispatch"},
    )

    # Dispatch -> parallel agents (fan-out)
    workflow.add_edge("dispatch", "feasibility")
    workflow.add_edge("dispatch", "resource")
    workflow.add_edge("dispatch", "risk")

    # Parallel agents -> parallel_results (fan-in)
    workflow.add_edge("feasibility", "parallel_results")
    workflow.add_edge("resource", "parallel_results")
    workflow.add_edge("risk", "parallel_results")

    # parallel_results -> synthesis
    workflow.add_edge("parallel_results", "synthesis")

    # synthesis -> review
    workflow.add_edge("synthesis", "review")

    # review -> (needs_review loop) -> document
    workflow.add_conditional_edges(
        "review",
        _should_continue_review,
        {"review": "review", "document": "document"},
    )

    # document -> END
    workflow.add_edge("document", END)

    return workflow


def compile_workflow() -> Any:
    wf = build_workflow()
    memory = MemorySaver()
    return wf.compile(checkpointer=memory)
