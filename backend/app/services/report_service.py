from __future__ import annotations

from app.models import Task


class ReportService:
    """Build Markdown reports from persisted task results."""

    def build_markdown(self, task: Task) -> str:
        """Return a portable Markdown analysis report."""

        insight = task.insight_report
        lines = [
            f"# {task.name} 评论洞察报告",
            "",
            f"- 领域：{task.domain}",
            f"- 平台：{', '.join(task.platforms)}",
            f"- 状态：{task.status}",
            f"- 原始评论数：{len(task.raw_comments)}",
            f"- 清洗后评论数：{len(task.clean_comments)}",
            "",
            "## 数据质量",
            "",
            *self._quality_lines(task),
            "",
            "## LLM 洞察总结",
            "",
            insight.summary if insight else "尚未生成洞察。",
            "",
            "## 帖子上下文样本",
            "",
            *self._source_note_lines(task),
            "",
            "## 主题聚类",
            "",
        ]
        for cluster in task.clusters:
            lines.extend(
                [
                    f"### {cluster.cluster_name}",
                    "",
                    f"- 评论数：{cluster.cluster_size}",
                    f"- 占比：{cluster.cluster_ratio:.1%}",
                    f"- 方法：{cluster.method}",
                    f"- 噪声类：{'是' if cluster.is_noise else '否'}",
                    f"- 高频词：{', '.join(cluster.top_keywords)}",
                    "",
                ]
            )
        lines.extend(["## 策略卡片", ""])
        for card in task.strategy_cards:
            lines.extend(
                [
                    f"### {card.title}",
                    "",
                    f"- 类型：{card.type}",
                    f"- 优先级：{card.priority}",
                    f"- 影响范围：{card.affected_ratio}",
                    f"- 证据数/样本量：{card.evidence_count} / {card.sample_size}",
                    f"- 置信度：{card.confidence}",
                    f"- 置信度原因：{card.confidence_reason}",
                    f"- 问题/机会：{card.problem_or_opportunity}",
                    "- 证据评论：",
                    *[f"  - {comment}" for comment in card.evidence_comments],
                    "- 建议动作：",
                    *[f"  - {action}" for action in card.suggested_actions],
                    f"- 预期收益：{card.expected_impact}",
                    "",
                ]
            )
        lines.extend(
            [
                "## 合规说明",
                "",
                "本报告仅基于样例数据、用户上传数据或公开可访问数据生成；系统不绕过登录、验证码、付费墙或平台权限控制。",
            ]
        )
        return "\n".join(lines)

    def _quality_lines(self, task: Task) -> list[str]:
        quality = task.data_quality_report
        if not quality:
            return ["- 暂无数据质量报告。"]
        lines = [
            f"- raw_count：{quality.raw_count}",
            f"- clean_count：{quality.clean_count}",
            f"- dedup_count：{quality.dedup_count}",
            f"- duplicate_ratio：{quality.duplicate_ratio:.1%}",
            f"- noise_ratio：{quality.noise_ratio:.1%}",
            f"- language_distribution：{quality.language_distribution}",
            f"- sample_confidence_level：{quality.sample_confidence_level}",
        ]
        if quality.warning:
            lines.append(f"- warning：{quality.warning}")
        return lines

    def _source_note_lines(self, task: Task) -> list[str]:
        notes: dict[str, dict] = {}
        for comment in task.raw_comments:
            metadata = comment.metadata_json or {}
            key = str(metadata.get("source_id") or comment.source_url or comment.topic or comment.id)
            note = notes.setdefault(
                key,
                {
                    "title": metadata.get("note_title") or comment.topic or "未命名帖子",
                    "desc": metadata.get("note_desc") or "",
                    "media_type": metadata.get("note_media_type") or "unknown",
                    "image_count": metadata.get("note_image_count") or 0,
                    "video_count": metadata.get("note_video_count") or 0,
                    "source_query": metadata.get("source_query") or metadata.get("source_keyword") or "",
                    "count": 0,
                },
            )
            note["count"] += 1
        if not notes:
            return ["暂无帖子上下文。"]
        lines: list[str] = []
        for note in list(notes.values())[:8]:
            media = f"{note['media_type']}，图 {note['image_count']} / 视频 {note['video_count']}"
            lines.append(
                f"- **{note['title']}**（样本评论 {note['count']} 条，{media}，搜索词：{note['source_query'] or '未知'}）"
            )
            if note["desc"]:
                lines.append(f"  - 正文摘录：{str(note['desc'])[:140]}")
        return lines
