from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


NormalizedComment = dict[str, Any]


@dataclass(slots=True)
class FetchRequest:
    """Connector request describing a compliant public-data fetch."""

    task_id: int
    platform: str
    domain: str
    keywords: list[str]
    semantic_query: str
    time_range: dict[str, Any] = field(default_factory=dict)
    max_comments: int = 100
    source_path: str | None = None
    source_urls: list[str] = field(default_factory=list)
    board: str = ""
    match_name: str = ""
    home_team: str = ""
    away_team: str = ""
    match_stage: str = ""
    match_date: str = ""
    field_mapping: dict[str, str] = field(default_factory=dict)


class PlatformConnector(Protocol):
    """Uniform connector interface for public comment sources."""

    name: str

    def fetch_comments(self, request: FetchRequest) -> list[NormalizedComment]:
        """Return normalized public comments without bypassing platform controls."""
