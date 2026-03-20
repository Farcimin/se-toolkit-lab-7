"""HTTP client for the LMS backend API."""

import httpx

from config import LMS_API_URL, LMS_API_KEY


class LMSClient:
    """Async client for the LMS backend API."""

    def __init__(self) -> None:
        self._base_url = LMS_API_URL.rstrip("/")
        self._headers = {"Authorization": f"Bearer {LMS_API_KEY}"}

    async def health_check(self) -> bool:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{self._base_url}/items/", headers=self._headers, timeout=5.0)
                return resp.status_code == 200
            except httpx.RequestError:
                return False

    async def get_items(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self._base_url}/items/", headers=self._headers, timeout=10.0)
            resp.raise_for_status()
            return resp.json()

    async def get_scores(self, lab: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/analytics/scores",
                params={"lab": lab},
                headers=self._headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()
