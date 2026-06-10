from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass
class TavilySearchHit:
    title: str
    url: str
    snippet: str
    score: float


class TavilySearchClient:
    """Small sync Tavily client used by the chat workflow."""

    def __init__(
        self,
        api_key: str,
        *,
        timeout_seconds: float,
        max_results: int,
    ) -> None:
        self._api_key = api_key.strip()
        self._timeout_seconds = max(1.0, float(timeout_seconds))
        self._max_results = max(1, min(int(max_results), 8))

    @property
    def enabled(self) -> bool:
        return bool(self._api_key)

    def search(self, query: str, *, max_results: int | None = None) -> list[TavilySearchHit]:
        if not self.enabled:
            return []

        normalized_query = str(query or "").strip()
        if not normalized_query:
            return []

        limit = self._max_results if max_results is None else max(1, min(int(max_results), 8))
        payload = {
            "api_key": self._api_key,
            "query": normalized_query,
            "search_depth": "basic",
            "max_results": limit,
            "include_answer": False,
            "include_raw_content": False,
        }

        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
            body = response.json()

        results = body.get("results") if isinstance(body, dict) else None
        if not isinstance(results, list):
            return []

        hits: list[TavilySearchHit] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or "").strip()
            snippet = str(item.get("content") or "").strip()
            if not title or not url:
                continue
            score_value = item.get("score")
            try:
                score = float(score_value) if score_value is not None else 0.0
            except (TypeError, ValueError):
                score = 0.0
            hits.append(
                TavilySearchHit(
                    title=title[:300],
                    url=url[:1000],
                    snippet=snippet[:500],
                    score=score,
                )
            )
        return hits
