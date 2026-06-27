from __future__ import annotations

from typing import Any

from app.services.vision_service import SiliconFlowVisionService


class MediaUnderstandingAgent:
    """Enrich a bounded set of image comments with multimodal evidence."""

    def __init__(self, service: SiliconFlowVisionService | None = None) -> None:
        self.service = service or SiliconFlowVisionService()

    def run(self, comments: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
        """Attach image analysis without failing the full comment workflow."""

        candidates = [comment for comment in comments if comment.get("image_urls")]
        candidates.sort(key=lambda item: int(item.get("like_count") or 0), reverse=True)
        limit = int(config.get("max_image_comments") or 0)
        selected: list[dict[str, Any]] = []
        seen_images: set[str] = set()
        duplicate_image_ids: set[int] = set()
        for comment in candidates:
            image_key = str((comment.get("image_urls") or [""])[0])
            if not image_key or image_key in seen_images:
                duplicate_image_ids.add(id(comment))
                continue
            seen_images.add(image_key)
            selected.append(comment)
            if len(selected) >= limit:
                break
        selected_ids = {id(comment) for comment in selected}
        enabled = bool(config.get("enable_image_analysis", True)) and limit > 0

        for comment in comments:
            if not comment.get("image_urls"):
                continue
            if not enabled:
                analysis = {"status": "disabled", "model": self.service.settings.siliconflow_vision_model}
            elif id(comment) in duplicate_image_ids:
                analysis = {"status": "skipped_duplicate", "model": self.service.settings.siliconflow_vision_model}
            elif id(comment) not in selected_ids:
                analysis = {"status": "skipped_limit", "model": self.service.settings.siliconflow_vision_model}
            else:
                analysis = self.service.analyze_comment(comment, config)
            comment["image_analysis"] = analysis
            if (
                analysis.get("status") == "completed"
                and analysis.get("summary")
                and analysis.get("relevance") in {"high", "medium"}
            ):
                media_text = f"配图内容：{analysis['summary']}"
                if analysis.get("ocr_text"):
                    media_text += f"；图中文字：{analysis['ocr_text']}"
                comment["analysis_content"] = f"{comment.get('content', '')} {media_text}".strip()
        return comments
