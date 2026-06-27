from __future__ import annotations

from typing import Any

from app.connectors import CSVConnector, JsonConnector, MediaCrawlerAdapter, MediaCrawlerExportConnector, MockConnector
from app.connectors.base import FetchRequest, PlatformConnector


class PlatformRouterAgent:
    """Select connectors and compliant collection strategies for platforms."""

    def __init__(self) -> None:
        self._connectors: dict[str, PlatformConnector] = {
            "mock": MockConnector(),
            "csv": CSVConnector(),
            "json": JsonConnector(),
            "mediacrawler": MediaCrawlerExportConnector(),
            "mediacrawler_adapter": MediaCrawlerAdapter(),
        }

    def run(self, config: dict[str, Any]) -> dict[str, Any]:
        """Return connector plans for the workflow."""

        data_source = config.get("data_source", "mock")
        connector = self._connectors.get(data_source, self._connectors["mock"])
        plans = []
        platforms = config["platforms"]
        if data_source in {"csv", "json"}:
            platforms = [platforms[0] if platforms else "sample"]
        for platform in platforms:
            request = FetchRequest(
                task_id=config["task_id"],
                platform=platform,
                domain=config["domain"],
                keywords=config["keywords"],
                semantic_query=config["semantic_query"],
                time_range=config["time_range"],
                max_comments=config["max_comments"] if data_source in {"csv", "json"} else max(1, config["max_comments"] // max(1, len(config["platforms"]))),
                source_path=config.get("source_path"),
            )
            plans.append(
                {
                    "platform": platform,
                    "connector": connector,
                    "request": request,
                    "strategy": "sample_or_public_data_only",
                }
            )
        return {"connector_plans": plans}
