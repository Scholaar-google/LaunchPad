"""Unit tests for conflict detector."""

from __future__ import annotations

from src.tools.conflict_detector import detect_conflicts


def test_detect_feasibility_resource_conflict() -> None:
    feasibility = {"conclusion": "技术可行", "confidence": 0.85}
    resource = {"conclusion": "人力严重不足", "confidence": 0.6, "team_size": 3, "timeline_months": 2}
    risk = {"conclusion": "中等风险", "confidence": 0.75, "risk_score": 5.0, "risks": []}

    conflicts = detect_conflicts(feasibility, resource, risk)
    assert len(conflicts) >= 1
    assert any("可行性 vs 资源" in c.topic for c in conflicts)


def test_detect_feasibility_risk_conflict() -> None:
    feasibility = {"conclusion": "技术可行", "confidence": 0.85}
    resource = {"conclusion": "资源充足", "confidence": 0.8, "team_size": 5, "timeline_months": 6}
    risk = {"conclusion": "高风险", "confidence": 0.7, "risk_score": 8.0, "risks": []}

    conflicts = detect_conflicts(feasibility, resource, risk)
    assert any("可行性 vs 风险" in c.topic for c in conflicts)


def test_detect_compliance_gap() -> None:
    feasibility = {"conclusion": "技术可行", "confidence": 0.85}
    resource = {"conclusion": "资源充足", "confidence": 0.8, "team_size": 5, "timeline_months": 6}
    risk = {
        "conclusion": "中等风险",
        "confidence": 0.7,
        "risk_score": 5.0,
        "risks": [{"description": "数据隐私合规风险评估缺失"}],
    }

    conflicts = detect_conflicts(feasibility, resource, risk)
    assert any("合规" in c.topic for c in conflicts)


def test_no_conflicts() -> None:
    feasibility = {"conclusion": "基本可行", "confidence": 0.75}
    resource = {"conclusion": "资源合理", "confidence": 0.8, "team_size": 5, "timeline_months": 6}
    risk = {"conclusion": "低风险", "confidence": 0.8, "risk_score": 3.0, "risks": []}

    conflicts = detect_conflicts(feasibility, resource, risk)
    assert len(conflicts) == 0


def test_missing_agent_result() -> None:
    conflicts = detect_conflicts(None, None, None)
    assert len(conflicts) == 0
