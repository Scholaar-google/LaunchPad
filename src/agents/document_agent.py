"""Document Agent: Generate SOAP-format project initiation document."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

import structlog

from src.graph.state import GlobalState
from src.tools.template_renderer import render_document

logger = structlog.get_logger(__name__)


async def run_document(state: GlobalState) -> dict[str, Any]:
    project_info = dict(state.get("project_info", {}))
    feasibility = state.get("feasibility_result") or {}
    resource = state.get("resource_result") or {}
    risk = state.get("risk_result") or {}
    recommendation = state.get("final_recommendation", "")
    final_decision = state.get("final_decision", "defer")
    if hasattr(final_decision, "value"):
        final_decision = str(final_decision.value)  # type: ignore[union-attr]
    key_assumptions = state.get("key_assumptions", [])
    uncertainties = state.get("uncertainties", [])

    doc_bytes = render_document(
        project_info=project_info,
        feasibility_result=feasibility,
        resource_result=resource,
        risk_result=risk,
        recommendation=recommendation,
        final_decision=str(final_decision),
        key_assumptions=list(key_assumptions),
        uncertainties=list(uncertainties),
    )

    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)

    project_name = project_info.get("title", "project")
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in project_name)
    filename = f"{safe_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.docx"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "wb") as f:
        f.write(doc_bytes)

    logger.info("document_generated", path=filepath)

    return {
        "document_path": filepath,
        "phase": "complete",
    }
