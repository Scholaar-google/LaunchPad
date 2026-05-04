"""Document template renderer for generating SOAP-format project initiation documents."""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor


def render_document(
    project_info: dict[str, Any],
    feasibility_result: dict[str, Any],
    resource_result: dict[str, Any],
    risk_result: dict[str, Any],
    recommendation: str,
    final_decision: str,
    key_assumptions: list[str],
    uncertainties: list[str],
    generated_at: datetime | None = None,
) -> bytes:
    now = generated_at or datetime.now(timezone.utc)
    doc = Document()

    # ---- Styles ----
    style = doc.styles["Normal"]
    font = style.font
    font.name = "SimSun"
    font.size = Pt(12)

    # ---- Title ----
    title = doc.add_heading("项目立项文档", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(f"文档编号: PROJ-{now.strftime('%Y%m%d-%H%M%S')}")
    doc.add_paragraph(f"文档版本: v1.0")
    doc.add_paragraph(f"生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    # ---- 1. 项目概述 ----
    doc.add_heading("一、项目概述", level=1)
    doc.add_paragraph(f"项目名称: {project_info.get('title', '未命名')}")
    doc.add_paragraph(f"优先级: {project_info.get('priority', '待定')}")
    doc.add_paragraph(f"项目描述: {project_info.get('description', '无')}")

    doc.add_heading("业务目标", level=2)
    for obj in project_info.get("objectives", []):
        doc.add_paragraph(obj, style="List Bullet")

    doc.add_heading("干系人", level=2)
    for stakeholder in project_info.get("stakeholders", []):
        doc.add_paragraph(stakeholder, style="List Bullet")

    # ---- 2. 需求分析 ----
    doc.add_heading("二、需求分析", level=1)
    doc.add_paragraph(f"需求背景: {project_info.get('background', '无')}")
    doc.add_paragraph(f"需求描述: {project_info.get('description', '无')}")

    if project_info.get("scope_in"):
        doc.add_heading("包含范围", level=2)
        for item in project_info["scope_in"]:
            doc.add_paragraph(item, style="List Bullet")

    if project_info.get("scope_out"):
        doc.add_heading("排除范围", level=2)
        for item in project_info["scope_out"]:
            doc.add_paragraph(item, style="List Bullet")

    # ---- 3. 可行性评估 ----
    doc.add_heading("三、可行性评估", level=1)

    if feasibility_result:
        doc.add_paragraph(f"总体结论: {feasibility_result.get('conclusion', '无')}")
        doc.add_paragraph(f"置信度: {feasibility_result.get('confidence', 0):.0%}")
        doc.add_paragraph(f"技术可行性: {feasibility_result.get('technical_feasibility', '无')}")
        doc.add_paragraph(f"业务可行性: {feasibility_result.get('business_feasibility', '无')}")

        blockers = feasibility_result.get("key_blockers", [])
        if blockers:
            doc.add_heading("关键障碍", level=2)
            for b in blockers:
                doc.add_paragraph(b, style="List Bullet")

    # ---- 4. 资源需求 ----
    doc.add_heading("四、资源需求", level=1)

    if resource_result:
        doc.add_paragraph(f"资源评估结论: {resource_result.get('conclusion', '无')}")
        doc.add_paragraph(f"置信度: {resource_result.get('confidence', 0):.0%}")
        doc.add_paragraph(f"预计团队规模: {resource_result.get('team_size', '待定')} 人")
        doc.add_paragraph(f"预计工期: {resource_result.get('timeline_months', '待定')} 个月")
        doc.add_paragraph(f"预算范围: {resource_result.get('budget_range', '待定')}")

        deps = resource_result.get("dependencies", [])
        if deps:
            doc.add_heading("资源依赖", level=2)
            for d in deps:
                doc.add_paragraph(d, style="List Bullet")

    # ---- 5. 风险评估 ----
    doc.add_heading("五、风险评估", level=1)

    if risk_result:
        doc.add_paragraph(f"风险等级: {risk_result.get('conclusion', '无')}")
        doc.add_paragraph(f"置信度: {risk_result.get('confidence', 0):.0%}")
        doc.add_paragraph(f"风险评分: {risk_result.get('risk_score', '无')} / 10")

        risks = risk_result.get("risks", [])
        if risks:
            doc.add_heading("风险清单", level=2)
            for i, r in enumerate(risks, 1):
                doc.add_heading(f"风险 {i}", level=3)
                doc.add_paragraph(f"描述: {r.get('description', '无')}")
                doc.add_paragraph(f"概率: {r.get('probability', '无')}")
                doc.add_paragraph(f"影响: {r.get('impact', '无')}")
                doc.add_paragraph(f"应对措施: {r.get('mitigation', '无')}")

    # ---- 6. 综合建议 ----
    doc.add_heading("六、综合建议", level=1)

    decision_map = {
        "approve": "建议立项",
        "defer": "建议缓议",
        "reject": "建议拒绝",
    }
    doc.add_paragraph(f"最终决定: {decision_map.get(final_decision, final_decision)}")
    doc.add_paragraph(f"综合建议: {recommendation}")

    if key_assumptions:
        doc.add_heading("关键假设", level=2)
        for a in key_assumptions:
            doc.add_paragraph(a, style="List Bullet")

    if uncertainties:
        doc.add_heading("不确定项", level=2)
        for u in uncertainties:
            doc.add_paragraph(u, style="List Bullet")

    # ---- Disclaimer ----
    doc.add_paragraph("")
    p = doc.add_paragraph()
    run = p.add_run("免责声明: 本报告由AI辅助生成，仅供参考，最终决策需由项目评审委员会确认。")
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(128, 128, 128)
    run.italic = True

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
