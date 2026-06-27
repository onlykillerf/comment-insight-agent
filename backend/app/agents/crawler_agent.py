from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class CommentCrawlerAgent:
    """Collect public or sample comments through selected connectors."""

    def run(self, connector_plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Fetch and normalize comments from connector plans."""

        comments: list[dict[str, Any]] = []
        for plan in connector_plans:
            connector = plan["connector"]
            request = plan["request"]
            logger.info("Fetching comments from %s using %s", request.platform, connector.name)
            comments.extend(connector.fetch_comments(request))
        deduped: dict[str, dict[str, Any]] = {}
        for comment in comments:
            if comment.get("id"):
                deduped[str(comment["id"])] = comment
        return list(deduped.values())

