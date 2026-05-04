"""FastAPI routes for the LaunchPad application."""

from __future__ import annotations

import asyncio
import io
import json
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from src.graph.state import create_initial_state
from src.graph.workflow import compile_workflow
from src.prompts.llm_config import get_settings

app = FastAPI(title="LaunchPad API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()
workflow_app = compile_workflow()
_in_memory_projects: dict[str, dict[str, Any]] = {}


def _persist_project_state(state: dict[str, Any]) -> None:
    project_id = str(state.get("project_id", ""))
    if project_id:
        _in_memory_projects[project_id] = dict(state)


# ---- Request/Response models ----


class CreateProjectRequest(BaseModel):
    requirement: str = Field(..., min_length=1, description="原始需求描述")


class ProjectResponse(BaseModel):
    id: str
    title: str
    status: str
    phase: str
    created_at: str | None
    needs_review: bool
    final_decision: str | None
    reasoning_chain: list[dict[str, Any]] = Field(default_factory=list)


class HumanConfirmRequest(BaseModel):
    project_id: str
    confirmed: bool = True
    feedback: str = ""


class DialogResponse(BaseModel):
    project_id: str
    questions: list[dict[str, Any]] = Field(default_factory=list)
    status: str
    phase: str


class ProjectDetailResponse(BaseModel):
    id: str
    title: str
    raw_requirement: str
    clarified_requirement: str | None
    status: str
    phase: str
    project_info: dict[str, Any]
    dialog_history: list[dict[str, Any]]
    reasoning_chain: list[dict[str, Any]]
    feasibility_result: dict[str, Any] | None
    resource_result: dict[str, Any] | None
    risk_result: dict[str, Any] | None
    final_decision: str | None
    final_recommendation: str | None
    key_assumptions: list[str]
    uncertainties: list[str]
    document_path: str | None
    needs_review: bool
    human_confirmed: bool
    review_confidence: float | None
    created_at: str | None
    updated_at: str | None


# ---- Routes ----


@app.post("/api/projects", response_model=DialogResponse)
async def create_project(request: CreateProjectRequest) -> dict[str, Any]:
    state = create_initial_state(request.requirement)
    config = {"configurable": {"thread_id": state["project_id"]}}

    result = await workflow_app.ainvoke(state, config)
    _persist_project_state(result)

    return {
        "project_id": result.get("project_id", ""),
        "questions": result.get("dialog_history", []),
        "status": "created",
        "phase": str(result.get("phase", "intake")),
    }


@app.post("/api/projects/{project_id}/dialog", response_model=DialogResponse)
async def continue_dialog(
    project_id: str,
    answers: dict[str, str],
) -> dict[str, Any]:
    config = {"configurable": {"thread_id": project_id}}

    current_state = workflow_app.get_state(config)
    if current_state is None or not current_state.values:
        raise HTTPException(status_code=404, detail="Project not found")

    state = dict(current_state.values)
    state["dialog_history"] = state.get("dialog_history", []) + [
        {"role": "user", "answers": answers}
    ]
    state["human_confirmed"] = True
    state["needs_review"] = False
    state["messages"] = state.get("messages", []) + [
        {"role": "user", "content": json.dumps(answers, ensure_ascii=False)}
    ]

    result = await workflow_app.ainvoke(state, config)
    _persist_project_state(result)

    return {
        "project_id": project_id,
        "questions": result.get("dialog_history", []),
        "status": "active",
        "phase": str(result.get("phase", "intake")),
    }


@app.post("/api/projects/{project_id}/confirm", response_model=dict[str, Any])
async def human_confirm(
    project_id: str,
    request: HumanConfirmRequest,
) -> dict[str, Any]:
    config = {"configurable": {"thread_id": project_id}}

    current_state = workflow_app.get_state(config)
    if current_state is None or not current_state.values:
        raise HTTPException(status_code=404, detail="Project not found")

    state = dict(current_state.values)
    state["human_confirmed"] = request.confirmed
    if request.feedback:
        state["dialog_history"] = state.get("dialog_history", []) + [
            {"role": "human_review", "feedback": request.feedback}
        ]

    result = await workflow_app.ainvoke(state, config)
    _persist_project_state(result)

    return {
        "project_id": project_id,
        "phase": str(result.get("phase", "complete")),
        "final_decision": str(result.get("final_decision", "")),
        "final_recommendation": result.get("final_recommendation", ""),
        "document_path": result.get("document_path"),
    }


@app.get("/api/projects/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: str) -> dict[str, Any]:
    config = {"configurable": {"thread_id": project_id}}
    current_state = workflow_app.get_state(config)

    if current_state is None or not current_state.values:
        raise HTTPException(status_code=404, detail="Project not found")

    state = current_state.values
    return _serialize_state(state)


@app.get("/api/projects/{project_id}/download")
async def download_document(project_id: str) -> Any:
    config = {"configurable": {"thread_id": project_id}}
    current_state = workflow_app.get_state(config)

    if current_state is None or not current_state.values:
        raise HTTPException(status_code=404, detail="Project not found")

    state = current_state.values
    doc_path = state.get("document_path")

    if not doc_path or not os.path.exists(doc_path):
        raise HTTPException(status_code=404, detail="Document not found or not yet generated")

    filename = os.path.basename(doc_path)
    return FileResponse(
        path=doc_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.get("/api/projects", response_model=list[ProjectResponse])
async def list_projects() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    for pid, state in _in_memory_projects.items():
        reasoning_chain = []
        for s in state.get("reasoning_chain", []):
            if hasattr(s, "layer"):
                reasoning_chain.append({
                    "layer": s.layer,
                    "title": s.title,
                    "content": s.content,
                    "timestamp": s.timestamp,
                    "confidence": s.confidence,
                })
            elif isinstance(s, dict):
                reasoning_chain.append(s)

        items.append({
            "id": str(pid),
            "title": state.get("project_info", {}).get("title", ""),
            "status": str(state.get("phase", "init")),
            "phase": str(state.get("phase", "init")),
            "created_at": None,
            "needs_review": state.get("needs_review", False),
            "final_decision": str(state.get("final_decision", "")),
            "reasoning_chain": reasoning_chain,
        })

    return sorted(items, key=lambda x: x["id"], reverse=True)


@app.get("/api/projects/{project_id}/stream")
async def stream_reasoning(project_id: str) -> StreamingResponse:
    async def event_generator() -> Any:
        yield f"data: {json.dumps({'type': 'connected', 'project_id': project_id})}\n\n"

        config = {"configurable": {"thread_id": project_id}}
        seen_steps = 0

        while True:
            try:
                current_state = workflow_app.get_state(config)
            except Exception:
                break

            if current_state is None or not current_state.values:
                break

            state = current_state.values
            chain = state.get("reasoning_chain", [])
            phase = str(state.get("phase", ""))

            if len(chain) > seen_steps:
                new_steps = chain[seen_steps:]
                for step in new_steps:
                    step_data: dict[str, Any]
                    if hasattr(step, "layer"):
                        step_data = {
                            "layer": step.layer,
                            "title": step.title,
                            "content": step.content,
                            "timestamp": step.timestamp,
                            "confidence": step.confidence,
                        }
                    elif isinstance(step, dict):
                        step_data = step
                    else:
                        step_data = {}
                    yield f"data: {json.dumps({'type': 'reasoning_step', 'step': step_data, 'phase': phase}, default=str)}\n\n"
                seen_steps = len(chain)

            if phase in ("complete", "error"):
                yield f"data: {json.dumps({'type': 'done', 'phase': phase})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _serialize_state(state: dict[str, Any]) -> dict[str, Any]:
    reasoning_chain: list[dict[str, Any]] = []
    for s in state.get("reasoning_chain", []):
        if hasattr(s, "layer"):
            reasoning_chain.append({
                "layer": s.layer,
                "title": s.title,
                "content": s.content,
                "timestamp": s.timestamp,
                "confidence": s.confidence,
            })
        elif isinstance(s, dict):
            reasoning_chain.append({
                "layer": s.get("layer", 0),
                "title": s.get("title", ""),
                "content": s.get("content", ""),
                "timestamp": s.get("timestamp", ""),
                "confidence": s.get("confidence", 1.0),
            })

    return {
        "id": state.get("project_id", ""),
        "title": state.get("project_info", {}).get("title", ""),
        "raw_requirement": state.get("raw_requirement", ""),
        "clarified_requirement": state.get("clarified_requirement", ""),
        "status": str(state.get("phase", "init")),
        "phase": str(state.get("phase", "init")),
        "project_info": state.get("project_info", {}),
        "dialog_history": state.get("dialog_history", []),
        "reasoning_chain": reasoning_chain,
        "feasibility_result": state.get("feasibility_result"),
        "resource_result": state.get("resource_result"),
        "risk_result": state.get("risk_result"),
        "final_decision": str(state.get("final_decision", "")),
        "final_recommendation": state.get("final_recommendation", ""),
        "key_assumptions": state.get("key_assumptions", []),
        "uncertainties": state.get("uncertainties", []),
        "document_path": state.get("document_path"),
        "needs_review": state.get("needs_review", False),
        "human_confirmed": state.get("human_confirmed", False),
        "review_confidence": state.get("review_confidence"),
        "created_at": None,
        "updated_at": None,
    }
