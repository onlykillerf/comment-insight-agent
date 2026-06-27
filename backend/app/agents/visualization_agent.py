from __future__ import annotations

from typing import Any

from app.services.visualization_service import VisualizationService


class VisualizationAgent:
    """Generate frontend-ready visualization payloads."""

    def __init__(self, service: VisualizationService | None = None) -> None:
        self.service = service or VisualizationService()

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Return chart data and word cloud data."""

        return self.service.build(context)

