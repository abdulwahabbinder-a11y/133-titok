"""
Lightweight HTTP scanner — polls the booking endpoint without launching a browser.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from dataclasses import dataclass
from typing import Awaitable, Callable

import httpx

from goethe_bot.config import (
    AVAILABLE_MARKERS,
    JSON_AVAILABILITY_KEYS,
    SCAN_INTERVAL_MAX_SEC,
    SCAN_INTERVAL_MIN_SEC,
    SCANNER_TARGET_URL,
    UNAVAILABLE_MARKERS,
)
from goethe_bot.proxy import build_rotating_proxy_url

logger = logging.getLogger(__name__)

SlotCallback = Callable[[str], Awaitable[None]]


@dataclass
class ScanResult:
    available: bool
    reason: str
    status_code: int | None = None


class AvailabilityScanner:
    """Continuously monitors the target URL for appointment availability."""

    def __init__(
        self,
        on_slot_found: SlotCallback,
        *,
        target_url: str = SCANNER_TARGET_URL,
    ) -> None:
        self._target_url = target_url
        self._on_slot_found = on_slot_found
        self._running = False
        self._triggered = False

    @property
    def is_running(self) -> bool:
        return self._running

    def stop(self) -> None:
        self._running = False

    async def run(self) -> None:
        """Main scan loop — polls every 15–30 seconds with rotating proxies."""
        self._running = True
        logger.info("Scanner started — target: %s", self._target_url)

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(20.0, connect=10.0),
            headers=self._scanner_headers(),
        ) as client:
            while self._running:
                result = await self._scan_once(client)
                logger.debug(
                    "Scan result: available=%s reason=%s status=%s",
                    result.available,
                    result.reason,
                    result.status_code,
                )

                if result.available and not self._triggered:
                    self._triggered = True
                    logger.warning("SLOT DETECTED — %s", result.reason)
                    await self._on_slot_found(result.reason)

                interval = random.uniform(SCAN_INTERVAL_MIN_SEC, SCAN_INTERVAL_MAX_SEC)
                logger.info("Next scan in %.1f s", interval)
                await asyncio.sleep(interval)

        logger.info("Scanner stopped.")

    async def _scan_once(self, client: httpx.AsyncClient) -> ScanResult:
        proxy = build_rotating_proxy_url()
        try:
            response = await client.get(self._target_url, proxy=proxy)
        except httpx.HTTPError as exc:
            logger.warning("Scan request failed (will retry): %s", exc)
            return ScanResult(available=False, reason=f"network_error: {exc}")

        body = response.text
        return self._evaluate_response(body, response.status_code, response.headers.get("content-type", ""))

    def _evaluate_response(self, body: str, status_code: int, content_type: str) -> ScanResult:
        if status_code >= 400:
            return ScanResult(
                available=False,
                reason=f"http_{status_code}",
                status_code=status_code,
            )

        # JSON API path
        if "json" in content_type.lower() or body.lstrip().startswith(("{", "[")):
            json_result = self._check_json(body)
            if json_result is not None:
                return json_result

        lowered = body.lower()

        # Unavailable text still present → no slot (check before broad "available" markers).
        for marker in UNAVAILABLE_MARKERS:
            if marker.lower() in lowered:
                return ScanResult(
                    available=False,
                    reason=f"still_unavailable:{marker!r}",
                    status_code=status_code,
                )

        # Positive signals
        for marker in AVAILABLE_MARKERS:
            if marker.lower() in lowered:
                return ScanResult(
                    available=True,
                    reason=f"marker_found:{marker!r}",
                    status_code=status_code,
                )

        # Unavailable markers gone but no positive marker — treat as potential change
        return ScanResult(
            available=True,
            reason="unavailable_markers_absent",
            status_code=status_code,
        )

    def _check_json(self, body: str) -> ScanResult | None:
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return None

        if isinstance(data, dict):
            for key in JSON_AVAILABILITY_KEYS:
                value = data.get(key)
                if isinstance(value, list) and len(value) > 0:
                    return ScanResult(available=True, reason=f"json_key:{key}")
                if isinstance(value, bool) and value:
                    return ScanResult(available=True, reason=f"json_key:{key}")
                if isinstance(value, int) and value > 0:
                    return ScanResult(available=True, reason=f"json_key:{key}")

        if isinstance(data, list) and len(data) > 0:
            return ScanResult(available=True, reason="json_nonempty_list")

        return ScanResult(available=False, reason="json_no_slots")

    @staticmethod
    def _scanner_headers() -> dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/json,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
            "Cache-Control": "no-cache",
        }
