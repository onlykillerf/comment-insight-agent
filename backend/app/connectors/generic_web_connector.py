from __future__ import annotations

from app.connectors.base import FetchRequest, NormalizedComment


class GenericWebConnector:
    """Placeholder connector for compliant public pages.

    The MVP intentionally does not scrape protected platforms. Real connectors
    should only request public pages, obey robots/terms, and avoid login,
    captcha, paywall or anti-abuse bypasses.
    """

    name = "generic_web"

    def fetch_comments(self, request: FetchRequest) -> list[NormalizedComment]:
        """Return an empty result until a compliant parser is explicitly added."""

        return []

