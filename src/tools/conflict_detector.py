"""Multi-agent conclusion conflict detector.

Identifies contradictions between parallel agent outputs.
"""

from __future__ import annotations

from typing import Any

from src.graph.state import ConflictItem


def detect_conflicts(
    feasibility: dict[str, Any] | None,
    resource: dict[str, Any] | None,
    risk: dict[str, Any] | None,
) -> list[ConflictItem]:
    """Detect conflicts between parallel agent results.

    Returns a list of ConflictItem for any found contradictions.
    Handles partial missing results gracefully.
    """
    conflicts: list[ConflictItem] = []

    if feasibility is None or resource is None or risk is None:
        return conflicts

    # Rule 1: Feasibility says "feasible" but resource says "insufficient"
    feas_conclusion = feasibility.get("conclusion", "").lower()
    res_conclusion = resource.get("conclusion", "").lower()

    if "可行" in feas_conclusion and ("不足" in res_conclusion or "缺乏" in res_conclusion):
        conflicts.append(
            ConflictItem(
                topic="可行性 vs 资源评估",
                source_a="feasibility_agent",
                conclusion_a=feasibility["conclusion"],
                source_b="resource_agent",
                conclusion_b=resource["conclusion"],
                resolution_paths=[
                    "缩小项目范围以匹配现有资源",
                    "申请额外资源预算以支撑可行性目标",
                    "分阶段交付，降低首期资源需求",
                ],
            )
        )

    # Rule 2: Feasibility says feasible but risk is high
    risk_conclusion = risk.get("conclusion", "").lower()
    risk_score = risk.get("risk_score", 0)

    if "可行" in feas_conclusion and (risk_score >= 7.0 or "高" in risk_conclusion):
        conflicts.append(
            ConflictItem(
                topic="可行性 vs 风险评估",
                source_a="feasibility_agent",
                conclusion_a=feasibility["conclusion"],
                source_b="risk_agent",
                conclusion_b=risk["conclusion"],
                resolution_paths=[
                    "制定详细风险缓解计划后推进",
                    "先执行技术预研/POC降低不确定性",
                    "调整技术方案以规避主要风险",
                ],
            )
        )

    # Rule 3: Resource mismatch — team size too large vs timeline
    team_size = resource.get("team_size", 0)
    timeline = resource.get("timeline_months", 0)

    if team_size > 20 and timeline <= 3:
        conflicts.append(
            ConflictItem(
                topic="资源计划一致性",
                source_a="resource_agent",
                conclusion_a=f"团队规模 {team_size} 人",
                source_b="resource_agent",
                conclusion_b=f"工期 {timeline} 个月",
                resolution_paths=[
                    "增加工期至合理范围",
                    "减少团队规模，分期交付",
                    "引入外部合作伙伴加速开发",
                ],
            )
        )

    # Rule 4: Risk mentions compliance/regulatory issues but feasibility doesn't
    risk_risks = risk.get("risks", [])
    has_compliance_risk = any(
        "合规" in str(r.get("description", ""))
        or "监管" in str(r.get("description", ""))
        for r in risk_risks
    )

    if has_compliance_risk and "可行" in feas_conclusion:
        conflicts.append(
            ConflictItem(
                topic="合规风险未被可行性覆盖",
                source_a="feasibility_agent",
                conclusion_a="可行性分析未充分评估合规风险",
                source_b="risk_agent",
                conclusion_b="识别到合规/监管风险",
                resolution_paths=[
                    "补充合规专项评估",
                    "咨询法务/合规部门确认要求",
                    "将合规要求纳入项目范围和排期",
                ],
            )
        )

    return conflicts
