"""HTTP client for the LMS backend API."""

import httpx

from config import LMS_API_URL, LMS_API_KEY


class LMSClient:
    """Async client for the LMS backend API."""

    def __init__(self) -> None:
        self._base_url = LMS_API_URL.rstrip("/")
        self._headers = {"Authorization": f"Bearer {LMS_API_KEY}"}

    async def get_items(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/items/",
                headers=self._headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_pass_rates(self, lab: str) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/analytics/pass-rates",
                params={"lab": lab},
                headers=self._headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()
