from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import httpx


@dataclass(frozen=True)
class JSearchClient:
    base_url: str
    rapidapi_key: str
    rapidapi_host: str

    async def search(self, query: str, page: int = 1, num_pages: int = 1) -> List[Dict[str, Any]]:
        """
        RapidAPI JSearch endpoint is commonly:
          GET {base_url}/search?query=...&page=1&num_pages=1
        Headers:
          X-RapidAPI-Key
          X-RapidAPI-Host
        """
        url = f"{self.base_url}/search"
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": self.rapidapi_host,
        }
        params = {
            "query": query,
            "page": page,
            "num_pages": num_pages,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()

        # JSearch commonly returns {"data": [...]}.
        results = data.get("data")
        if isinstance(results, list):
            return results

        # fallback: sometimes APIs return list directly
        if isinstance(data, list):
            return data

        return []