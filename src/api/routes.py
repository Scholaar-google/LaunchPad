"""FastAPI routes for the LaunchPad application."""

from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.api.schemas import Base, Project
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

engine = create_engine(settings.database_url, echo=False)
Base.metadata.create_all(bind=engine)

workflow_app = compile_workflow()


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

    result = await workflow_app.ainvoke(state, config)

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


@app.get("/api/projects", response_model=list[ProjectResponse])
async def list_projects() -> list[dict[str, Any]]:
    configs: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []

    with Session(engine) as session:
        projects = session.execute(select(Project).order_by(Project.created_at.desc())).scalars().all()
        for p in projects:
            items.append({
                "id": str(p.id),
                "title": p.title,
                "status": p.status,
                "phase": p.phase,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "needs_review": p.needs_review,
                "final_decision": p.final_decision,
                "reasoning_chain": p.reasoning_chain or [],
            })

    return items


@app.get("/api/projects/{project_id}/stream")
async def stream_reasoning(project_id: str) -> StreamingResponse:
    async def event_generator() -> Any:
        yield f"data: {json.dumps({'type': 'connected', 'project_id': project_id})}\n\n"

        config = {"configurable": {"thread_id": project_id}}
        seen_steps = 0

        while True:
            current_state = workflow_app.get_state(config)
            if current_state is None or not current_state.values:
                break

            state = current_state.values
            chain = state.get("reasoning_chain", [])
            phase = str(state.get("phase", ""))

            if len(chain) > seen_steps:
                new_steps = chain[seen_steps:]
                for step in new_steps:
                    yield f"data: {json.dumps({'type': 'reasoning_step', 'step': step, 'phase': phase}, default=str)}\n\n"
                seen_steps = len(chain)

            if phase in ("complete", "error"):
                yield f"data: {json.dumps({'type': 'done', 'phase': phase})}\n\n"
                break

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
    return {
        "id": state.get("project_id", ""),
        "title": state.get("project_info", {}).get("title", ""),
        "raw_requirement": state.get("raw_requirement", ""),
        "clarified_requirement": state.get("clarified_requirement", ""),
        "status": str(state.get("phase", "init")),
        "phase": str(state.get("phase", "init")),
        "project_info": state.get("project_info", {}),
        "dialog_history": state.get("dialog_history", []),
        "reasoning_chain": [
            {
                "layer": s.layer if hasattr(s, "layer") else s.get("layer", 0),
                "title": s.title if hasattr(s, "title") else s.get("title", ""),
                "content": s.content if hasattr(s, "content") else s.get("content", ""),
                "timestamp": s.timestamp if hasattr(s, "timestamp") else s.get("timestamp", ""),
                "confidence": s.confidence if hasattr(s, "confidence") else s.get("confidence", 1.0),
            }
            for s in state.get("reasoning_chain", [])
        ],
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
