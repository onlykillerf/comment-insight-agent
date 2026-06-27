from __future__ import annotations

from app.models import Task


class ReportService:
    """Build focused Markdown reports for Hupu match discussions."""

    def build_markdown(self, task: Task) -> str:
        """Return a portable Markdown match-opinion report."""

        insight = task.insight_report
        lines = [
            f"# {task.name}",
            "",
            "## 比赛信息",
            "",
            f"- 运动：{'篮球' if task.domain == 'basketball' else '足球'}",
            f"- 虎扑板块：{task.board or '未指定'}",
            f"- 比赛：{task.match_name or self._versus(task)}",
            f"- 阶段：{task.match_stage or '未指定'}",
            f"- 时间：{task.match_date or '未指定'}",
            f"- 评论来源：虎扑公开帖子 {len(task.thread_urls)} 个",
            f"- 状态：{task.status}",
            "",
            "## 数据质量",
            "",
            *self._quality_lines(task),
            "",
            "## 虎扑帖子上下文",
            "",
            *self._thread_context_lines(task),
            "",
            "## 新闻背景",
            "",
            insight.news_context_summary if insight else "未生成新闻背景摘要。",
            "",
            "## 主帖与权威来源图像证据",
            "",
            *self._image_evidence_lines(task),
            "",
            "## 舆情摘要",
            "",
            insight.summary if insight else "尚未生成洞察。",
            "",
        ]
        if insight:
            lines.extend(self._insight_sections(insight))
        lines.extend(["## 主题聚类", ""])
        for cluster in task.clusters:
            lines.extend(
                [
                    f"### {cluster.cluster_name}",
                    "",
                    f"- 评论数：{cluster.cluster_size}",
                    f"- 占比：{cluster.cluster_ratio:.1%}",
                    f"- 方法：{cluster.method}",
                    f"- 噪声类：{'是' if cluster.is_noise else '否'}",
                    f"- 关键词：{', '.join(cluster.top_keywords)}",
                    *[f"- 代表评论：{comment}" for comment in cluster.representative_comments[:3]],
                    "",
                ]
            )
        lines.extend(
            [
                "## 合规与解释边界",
                "",
                "本报告只处理用户指定的虎扑公开帖子和公开新闻页面，不绕过登录、验证码、付费墙或平台权限。",
                "新闻内容用于补充事实背景；网友评论属于抽样观点，不能替代比赛数据、官方判罚说明或可靠新闻事实。",
            ]
        )
        return "\n".join(lines)

    def _quality_lines(self, task: Task) -> list[str]:
        quality = task.data_quality_report
        if not quality:
            return ["- 暂无数据质量报告。"]
        lines = [
            f"- 原始评论：{quality.raw_count}",
            f"- 清洗后评论：{quality.clean_count}",
            f"- 去重后评论：{quality.dedup_count}",
            f"- 重复率：{quality.duplicate_ratio:.1%}",
            f"- 噪声率：{quality.noise_ratio:.1%}",
            f"- 样本可信度：{quality.sample_confidence_level}",
        ]
        if quality.warning:
            lines.append(f"- 警告：{quality.warning}")
        return lines

    def _image_evidence_lines(self, task: Task) -> list[str]:
        rows: list[str] = []
        media_items = task.insight_report.context_media if task.insight_report else []
        for item in media_items:
            if not item.get("included_in_summary"):
                continue
            rows.extend(
                [
                    f"- 来源：[{item.get('title') or '未命名来源'}]({item.get('source_url') or ''})",
                    f"  - 来源级别：{item.get('authority_level', 'unknown')}",
                    f"  - 筛选理由：{'；'.join(item.get('selection_reasons') or []) or '无'}",
                    f"  - 图片：{', '.join((item.get('image_urls') or [])[:2])}",
                    f"  - 视觉摘要：{item.get('summary', '无')}",
                    f"  - 数据点：{'；'.join(item.get('data_points') or []) or '无'}",
                    f"  - OCR：{item.get('ocr_text') or '无'}",
                    f"  - 相关性：{item.get('relevance', 'unknown')}；信息量：{item.get('information_value', 'unknown')}；置信度：{item.get('confidence', 'unknown')}；模型：{item.get('model', 'unknown')}",
                ]
            )
        excluded = [item for item in media_items if not item.get("included_in_summary")]
        if excluded:
            rows.append(f"- 图像筛选审计：共审查 {len(media_items)} 张，排除 {len(excluded)} 张。")
            rows.extend(
                f"  - 已排除《{item.get('title') or '未命名来源'}》：{item.get('exclusion_reason') or '未通过视觉证据门槛'}"
                for item in excluded
            )
        return rows or ["- 本次没有候选主帖、新闻或官网信息图。"]

    def _thread_context_lines(self, task: Task) -> list[str]:
        threads: dict[str, dict[str, str | int]] = {}
        for comment in task.raw_comments:
            metadata = comment.metadata_json or {}
            key = str(metadata.get("thread_id") or comment.source_url or comment.id)
            item = threads.setdefault(
                key,
                {
                    "title": str(metadata.get("thread_title") or comment.topic or "未命名帖子"),
                    "excerpt": str(metadata.get("thread_excerpt") or ""),
                    "url": comment.source_url,
                    "count": 0,
                },
            )
            item["count"] = int(item["count"]) + 1
        if not threads:
            return ["- 暂无帖子上下文。"]
        lines: list[str] = []
        for item in list(threads.values())[:10]:
            lines.append(f"- [{item['title']}]({item['url']})：采样评论 {item['count']} 条")
            if item["excerpt"]:
                lines.append(f"  - 主帖摘要：{str(item['excerpt'])[:240]}")
        return lines

    @staticmethod
    def _insight_sections(insight: object) -> list[str]:
        sections = [
            ("关键观点", insight.key_viewpoints),
            ("正向评价", insight.positive_insights),
            ("负向评价", insight.negative_insights),
            ("争议焦点", insight.controversies),
            ("新闻与评论对照", insight.context_alignment),
            ("事实与观点缺口", insight.fact_opinion_gaps),
            ("解读风险", insight.risks),
        ]
        lines: list[str] = []
        for title, items in sections:
            lines.extend([f"## {title}", ""])
            lines.extend([f"- {item}" for item in items] or ["- 暂无。"])
            lines.append("")
        return lines

    @staticmethod
    def _versus(task: Task) -> str:
        teams = [team for team in [task.home_team, task.away_team] if team]
        return " vs ".join(teams) if teams else "未指定"
