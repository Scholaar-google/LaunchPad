"""Unit tests for template renderer."""

from __future__ import annotations

from src.tools.template_renderer import render_document


def test_render_document_generates_bytes() -> None:
    project_info = {
        "title": "测试项目",
        "description": "这是一个测试项目的描述",
        "background": "测试背景",
        "objectives": ["目标1", "目标2"],
        "stakeholders": ["张三", "李四"],
        "priority": "high",
        "scope_in": ["模块A", "模块B"],
        "scope_out": ["模块C"],
    }

    feasibility = {
        "conclusion": "技术可行",
        "confidence": 0.85,
        "technical_feasibility": "使用成熟技术栈",
        "business_feasibility": "符合战略方向",
        "key_blockers": ["关键技术人才不足"],
    }

    resource = {
        "conclusion": "资源可支撑",
        "confidence": 0.7,
        "team_size": 6,
        "timeline_months": 5,
        "budget_range": "80-120万",
        "dependencies": ["运维团队", "第三方API"],
    }

    risk = {
        "conclusion": "中等风险",
        "confidence": 0.75,
        "risk_score": 5.5,
        "risks": [
            {
                "description": "第三方API不稳定",
                "probability": "中",
                "impact": "高",
                "mitigation": "增加降级方案",
            }
        ],
    }

    result = render_document(
        project_info=project_info,
        feasibility_result=feasibility,
        resource_result=resource,
        risk_result=risk,
        recommendation="建议立项",
        final_decision="approve",
        key_assumptions=["假设1", "假设2"],
        uncertainties=["不确定项1"],
    )

    assert isinstance(result, bytes)
    assert len(result) > 0
