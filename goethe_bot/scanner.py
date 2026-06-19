from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
from dataclasses import dataclass
from itertools import cycle
from typing import Any

import httpx

from goethe_bot.config import ScanConfig

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ScanResult:
    slot_found: bool
    reason: str
    status_code: int | None
    response_preview: str
    response_hash: str


class ProxyRotator:
    """Simple round-robin proxy rotation placeholder."""

    def __init__(self, proxies: list[str]) -> None:
        clean = [proxy.strip() for proxy in proxies if proxy and proxy.strip()]
        self._iterator = cycle(clean) if clean else None

    def next_proxy(self) -> str | None:
        if self._iterator is None:
            return None
        return next(self._iterator)


class AppointmentScanner:
    def __init__(self, config: ScanConfig) -> None:
        self.config = config
        self.proxy_rotator = ProxyRotator(config.residential_proxies)
        self._previous_hash: str | None = None
        self._consecutive_errors = 0

    async def _request(self, proxy: str | None) -> httpx.Response:
        client_kwargs: dict[str, Any] = {
            "timeout": self.config.timeout_seconds,
            "follow_redirects": True,
        }
        if proxy:
            # Rotating-residential proxy placeholder. Replace with your own provider URLs.
            client_kwargs["proxy"] = proxy

        async with httpx.AsyncClient(**client_kwargs) as client:
            method = self.config.method.upper()
            if method == "GET":
                return await client.get(
                    self.config.endpoint_url,
                    headers=self.config.headers,
                    params=self.config.payload,
                )
            if method == "POST":
                return await client.post(
                    self.config.endpoint_url,
                    headers=self.config.headers,
                    json=self.config.payload,
                )
            raise ValueError(f"Unsupported HTTP method: {self.config.method}")

    def _normalize_response(self, response: httpx.Response) -> str:
        content_type = response.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            try:
                return json.dumps(response.json(), sort_keys=True).lower()
            except Exception:  # noqa: BLE001
                return response.text.lower()
        return response.text.lower()

    def _detect_slot(self, normalized_response: str) -> tuple[bool, str]:
        unavailable_hit = any(
            marker.lower() in normalized_response
            for marker in self.config.unavailable_markers
        )
        available_hit = any(
            marker.lower() in normalized_response
            for marker in self.config.available_markers
        )

        if available_hit and not unavailable_hit:
            return True, "Availability marker detected and no unavailable marker matched."
        if unavailable_hit:
            return False, "Unavailable marker still present."
        return False, "No positive availability marker matched."

    async def check_once(self) -> ScanResult:
        proxy = self.proxy_rotator.next_proxy()
        response = await self._request(proxy=proxy)
        normalized = self._normalize_response(response)
        body_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        changed = body_hash != self._previous_hash
        self._previous_hash = body_hash

        slot_found, reason = self._detect_slot(normalized)
        preview = normalized[:180].replace("\n", " ").strip()

        if changed:
            logger.info("Scan response changed. status=%s, proxy=%s", response.status_code, proxy)

        self._consecutive_errors = 0
        return ScanResult(
            slot_found=slot_found,
            reason=reason,
            status_code=response.status_code,
            response_preview=preview,
            response_hash=body_hash,
        )

    async def wait_for_slot(self) -> ScanResult:
        while True:
            try:
                result = await self.check_once()
                if result.slot_found:
                    logger.warning(
                        "Potential slot found. status=%s reason=%s",
                        result.status_code,
                        result.reason,
                    )
                    return result

                sleep_for = random.uniform(
                    self.config.poll_interval_min_seconds,
                    self.config.poll_interval_max_seconds,
                )
                logger.info(
                    "No slot yet (%s). Sleeping %.2f seconds.",
                    result.reason,
                    sleep_for,
                )
                await asyncio.sleep(sleep_for)

            except Exception as exc:  # noqa: BLE001
                self._consecutive_errors += 1
                backoff = min(
                    self.config.error_backoff_cap_seconds,
                    2 ** min(self._consecutive_errors, 8),
                )
                logger.exception(
                    "Scanner error (%s consecutive). Backing off %.2f seconds: %s",
                    self._consecutive_errors,
                    backoff,
                    exc,
                )
                await asyncio.sleep(backoff)

