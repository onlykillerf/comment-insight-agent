# Roadmap

## MVP

- FastAPI API 和 SQLAlchemy models
- MockConnector、CSVConnector、JsonConnector
- MediaCrawlerExportConnector，用于导入真实采集器的合规导出数据
- 13 个 Agent 的基础可运行逻辑
- LangGraph 工作流与顺序 fallback
- MockLLM 洞察和策略卡片
- Next.js 看板、任务创建、报告、策略卡片页
- Markdown 导出

## Phase 2

- Celery 异步任务状态流
- PostgreSQL 迁移脚本
- Qdrant 真实向量检索
- Playwright/httpx 公开页面采集插件
- OpenAI、DeepSeek、Qwen Provider

## Phase 3

- 实验结果回流
- 策略胜率模型
- 多租户权限
- Connector 合规审计日志
