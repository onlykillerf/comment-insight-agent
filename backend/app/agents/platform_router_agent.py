from __future__ import annotations

from typing import Any

from app.connectors import (
    CSVConnector,
    HupuPublicConnector,
    JsonConnector,
    MockConnector,
)
from app.connectors.base import FetchRequest, PlatformConnector


class PlatformRouterAgent:
    """Select connectors and compliant collection strategies for platforms."""

    def __init__(self) -> None:
        self._connectors: dict[str, PlatformConnector] = {
            "mock": MockConnector(),
            "hupu_public": HupuPublicConnector(),
            "csv": CSVConnector(),
            "json": JsonConnector(),
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
                source_urls=config.get("thread_urls") or [],
                board=config.get("board", ""),
                match_name=config.get("match_name", ""),
                home_team=config.get("home_team", ""),
                away_team=config.get("away_team", ""),
                match_stage=config.get("match_stage", ""),
                match_date=config.get("match_date", ""),
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
