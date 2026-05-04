"""Document Agent: Generate SOAP-format project initiation document."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import structlog

from src.graph.state import AgentResult, FinalDecision, GlobalState
from src.tools.template_renderer import render_document

logger = structlog.get_logger(__name__)

_OUTPUT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "output")
)


async def run_document(state: GlobalState) -> dict[str, Any]:
    project_info = dict(state.get("project_info", {}))
    feasibility = state.get("feasibility_result") or {}
    resource = state.get("resource_result") or {}
    risk = state.get("risk_result") or {}
    recommendation = state.get("final_recommendation", "")
    final_decision = state.get("final_decision", "defer")
    if isinstance(final_decision, FinalDecision):
        final_decision = final_decision.value
    key_assumptions = state.get("key_assumptions", [])
    uncertainties = state.get("uncertainties", [])

    now = datetime.now(timezone.utc)

    doc_bytes = render_document(
        project_info=project_info,
        feasibility_result=feasibility,
        resource_result=resource,
        risk_result=risk,
        recommendation=recommendation,
        final_decision=str(final_decision),
        key_assumptions=list(key_assumptions),
        uncertainties=list(uncertainties),
        generated_at=now,
    )

    os.makedirs(_OUTPUT_DIR, exist_ok=True)

    project_name = project_info.get("title", "project")
    safe_name = "".join(
        c if c.isalnum() or c in "._- " else "_" for c in project_name
    )
    filename = f"{safe_name}_{now.strftime('%Y%m%d_%H%M%S')}.docx"
    filepath = os.path.join(_OUTPUT_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(doc_bytes)

    logger.info("document_generated", path=filepath)

    result = AgentResult(
        conclusion=f"立项文档已生成: {filename}",
        confidence=1.0,
        reasoning=f"文档路径: {filepath}",
        missing_info=[],
    )

    return {
        "document_path": filepath,
        "document_agent_result": result,
        "phase": "complete",
    }
