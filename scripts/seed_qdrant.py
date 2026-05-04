"""Seed Qdrant with initial historical project data.

Usage:
    python scripts/seed_qdrant.py
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.tools.qdrant_search import seed_projects

SAMPLE_PROJECTS: list[dict] = [
    {
        "id": 1,
        "description": "企业内部考勤管理系统：支持打卡、请假、加班申请、考勤统计报表导出。基于微服务架构，前端 React，后端 Java Spring Boot，数据库 MySQL。团队 6 人，工期 5 个月，预算 80 万。",
        "metadata": {"category": "内部管理", "team_size": 6, "timeline_months": 5, "budget": 800000},
    },
    {
        "id": 2,
        "description": "电商平台订单管理系统：支持订单创建、支付集成、物流追踪、售后管理。需要对接微信支付、支付宝、顺丰快递 API。团队 8 人，工期 6 个月，预算 150 万。",
        "metadata": {"category": "电商", "team_size": 8, "timeline_months": 6, "budget": 1500000},
    },
    {
        "id": 3,
        "description": "数据可视化大屏看板：实时展示销售数据、区域分布、用户行为热力图。大屏适配，支持钻取和多维分析。使用 ECharts + Three.js。团队 3 人，工期 2 个月，预算 30 万。",
        "metadata": {"category": "数据分析", "team_size": 3, "timeline_months": 2, "budget": 300000},
    },
    {
        "id": 4,
        "description": "移动端 CRM 客户关系管理：客户资料管理、跟进记录、销售漏斗、商机预测。移动端优先设计，需要离线支持。React Native 开发。团队 4 人，工期 4 个月，预算 70 万。",
        "metadata": {"category": "CRM", "team_size": 4, "timeline_months": 4, "budget": 700000},
    },
    {
        "id": 5,
        "description": "智能客服系统：基于 LLM 的智能问答、意图识别、自动工单分配、知识库管理。需要集成企业微信、钉钉。团队 5 人，工期 6 个月，预算 200 万。AI 项目，技术风险较高。",
        "metadata": {"category": "AI应用", "team_size": 5, "timeline_months": 6, "budget": 2000000},
    },
    {
        "id": 6,
        "description": "ERP 财务管理模块：总账、应收应付、固定资产、财务报表。需要符合中国企业会计准则。SAP 接口对接。团队 10 人，工期 12 个月，预算 500 万。合规要求高。",
        "metadata": {"category": "ERP", "team_size": 10, "timeline_months": 12, "budget": 5000000},
    },
    {
        "id": 7,
        "description": "在线教育直播平台：实时直播、白板互动、课件管理、学员作业批改。低延迟要求高，需要 CDN 加速。团队 7 人，工期 8 个月，预算 250 万。",
        "metadata": {"category": "在线教育", "team_size": 7, "timeline_months": 8, "budget": 2500000},
    },
    {
        "id": 8,
        "description": "供应链管理系统：采购管理、库存管理、供应商管理、物流调度优化。需要物联网设备接入。团队 12 人，工期 10 个月，预算 350 万。",
        "metadata": {"category": "供应链", "team_size": 12, "timeline_months": 10, "budget": 3500000},
    },
    {
        "id": 9,
        "description": "人力资源管理 HRM 系统：招聘管理、组织架构、薪酬绩效、培训管理、员工自助。需要与钉钉/企业微信集成。团队 8 人，工期 7 个月，预算 120 万。",
        "metadata": {"category": "HRM", "team_size": 8, "timeline_months": 7, "budget": 1200000},
    },
    {
        "id": 10,
        "description": "内容管理系统 CMS：文章发布、多站点管理、权限控制、SEO 优化、CDN 静态化。React SSR + Node.js。团队 4 人，工期 3 个月，预算 50 万。",
        "metadata": {"category": "CMS", "team_size": 4, "timeline_months": 3, "budget": 500000},
    },
    {
        "id": 11,
        "description": "物联网设备管理平台：设备注册、固件 OTA 升级、数据采集与存储、告警规则引擎。需要 MQTT 协议支持。时序数据库 InfluxDB。团队 6 人，工期 9 个月，预算 300 万。",
        "metadata": {"category": "IoT", "team_size": 6, "timeline_months": 9, "budget": 3000000},
    },
    {
        "id": 12,
        "description": "风控反欺诈系统：实时风险评估、规则引擎、机器学习模型推理、黑名单管理。需要高吞吐低延迟，日均处理 1000 万笔交易。团队 8 人，工期 10 个月，预算 400 万。",
        "metadata": {"category": "金融风控", "team_size": 8, "timeline_months": 10, "budget": 4000000},
    },
    {
        "id": 13,
        "description": "统一身份认证 SSO 平台：OAuth2.0/OIDC 协议、多租户管理、RBAC 权限模型、审计日志。高可用集群部署。团队 5 人，工期 6 个月，预算 150 万。",
        "metadata": {"category": "基础设施", "team_size": 5, "timeline_months": 6, "budget": 1500000},
    },
    {
        "id": 14,
        "description": "营销自动化 MA 系统：客户分群、自动化营销旅程、AB 测试、效果分析。需要集成微信、短信、邮件三个渠道。团队 6 人，工期 5 个月，预算 120 万。",
        "metadata": {"category": "营销", "team_size": 6, "timeline_months": 5, "budget": 1200000},
    },
    {
        "id": 15,
        "description": "低代码平台：可视化表单设计、工作流引擎、数据模型配置、自定义组件开发。基于 React + Node.js，需支持拖拽式开发。团队 10 人，工期 12 个月，预算 600 万。",
        "metadata": {"category": "平台产品", "team_size": 10, "timeline_months": 12, "budget": 6000000},
    },
    {
        "id": 16,
        "description": "医疗影像 AI 辅助诊断系统：CT/MRI 影像分析、病灶检测、结构化报告。需要医疗器械三类认证。团队 15 人，工期 18 个月，预算 1500 万。合规要求极高，需要临床试验。",
        "metadata": {"category": "医疗AI", "team_size": 15, "timeline_months": 18, "budget": 15000000},
    },
    {
        "id": 17,
        "description": "智慧园区管理平台：访客管理、停车管理、楼宇自控、能耗监测、安防联动。物联网设备接入 5000+ 终端。团队 8 人，工期 8 个月，预算 280 万。",
        "metadata": {"category": "智慧园区", "team_size": 8, "timeline_months": 8, "budget": 2800000},
    },
    {
        "id": 18,
        "description": "报表分析平台 BI：自助式数据探索、仪表盘设计、权限管控、数据预警推送。支持 ClickHouse + Apache Superset 集成。团队 6 人，工期 6 个月，预算 180 万。",
        "metadata": {"category": "BI", "team_size": 6, "timeline_months": 6, "budget": 1800000},
    },
    {
        "id": 19,
        "description": "审批流程引擎：可视化流程设计、动态表单、条件分支、会签/转签/加签。需要集成现有 OA 系统。团队 4 人，工期 3 个月，预算 60 万。",
        "metadata": {"category": "OA", "team_size": 4, "timeline_months": 3, "budget": 600000},
    },
    {
        "id": 20,
        "description": "MES 生产执行系统：工单管理、质量追溯、设备联网、生产看板。需要与 SAP ERP 集成。工业协议 Modbus/OPC UA。团队 10 人，工期 12 个月，预算 450 万。",
        "metadata": {"category": "MES", "team_size": 10, "timeline_months": 12, "budget": 4500000},
    },
    {
        "id": 21,
        "description": "在线文档协作平台：多人实时编辑、版本历史、评论审阅、权限管理。基于 CRDT 算法实现冲突解决。团队 8 人，工期 10 个月，预算 350 万。",
        "metadata": {"category": "协作工具", "team_size": 8, "timeline_months": 10, "budget": 3500000},
    },
    {
        "id": 22,
        "description": "跨境物流追踪系统：海关申报、国际运输追踪、仓储管理、费用结算。需要对接多个国家海关系统 API。团队 7 人，工期 9 个月，预算 280 万。",
        "metadata": {"category": "物流", "team_size": 7, "timeline_months": 9, "budget": 2800000},
    },
    {
        "id": 23,
        "description": "知识管理 KMS 系统：文档库、知识图谱、智能搜索、专家网络。基于 Elasticsearch + Neo4j。团队 5 人，工期 6 个月，预算 120 万。",
        "metadata": {"category": "知识管理", "team_size": 5, "timeline_months": 6, "budget": 1200000},
    },
    {
        "id": 24,
        "description": "API 网关管理平台：API 注册、流量控制、安全认证、调用监控、文档自动生成。基于 Kong 二次开发。团队 4 人，工期 4 个月，预算 80 万。",
        "metadata": {"category": "基础设施", "team_size": 4, "timeline_months": 4, "budget": 800000},
    },
    {
        "id": 25,
        "description": "项目管理 PM 系统：需求管理、任务分解、甘特图、燃尽图、资源负载分析。敏捷/瀑布双模式支持。团队 5 人，工期 5 个月，预算 100 万。",
        "metadata": {"category": "项目管理", "team_size": 5, "timeline_months": 5, "budget": 1000000},
    },
]


def main() -> None:
    count = seed_projects(SAMPLE_PROJECTS)
    print(f"Seeded {count} historical projects into Qdrant.")


if __name__ == "__main__":
    main()
