"""
THE SCANNER – lightweight, low-footprint polling layer.

Design goals
------------
* Never spawn a browser; use raw HTTP via `httpx` (HTTP/2 + keep-alive).
* Rotate residential proxy on every request (most providers rotate IP
  automatically per TCP connection, so we open a fresh client each scan).
* Randomised cadence between SCAN_INTERVAL_MIN .. SCAN_INTERVAL_MAX.
* Detect availability either by:
    1. Absence of NEGATIVE_MARKER  (e.g. "Keine Buchung möglich"), OR
    2. Presence of POSITIVE_MARKER (e.g. "Anmelden", a slot button)
* Hand control to the Sniper through an `asyncio.Event`.

Replace `TARGET_URL`, `NEGATIVE_MARKER`, `POSITIVE_MARKER` in `.env`
once you have inspected the real Goethe-Institut endpoint.
"""

from __future__ import annotations

import asyncio
import random
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import settings
from human import random_scan_interval


# --------------------------------------------------------------------------- #
# Browser-like header pool
# --------------------------------------------------------------------------- #
_USER_AGENTS = [
    # Recent macOS Chrome builds – keep this list fresh.
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.5 Safari/605.1.15",
]


def _build_headers() -> dict:
    return {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Connection": "keep-alive",
    }


# --------------------------------------------------------------------------- #
# Core scanner
# --------------------------------------------------------------------------- #
class Scanner:
    def __init__(self, slot_event: asyncio.Event) -> None:
        self._event = slot_event
        self._consecutive_errors = 0

    # ------------------------------------------------------------------ #
    async def _fetch(self) -> Optional[str]:
        """Single GET with proxy rotation and retries."""
        proxy = settings.proxy.as_httpx()
        timeout = httpx.Timeout(20.0, connect=10.0)

        client_kwargs: dict = {
            "timeout": timeout,
            "headers": _build_headers(),
            "follow_redirects": True,
            "http2": True,
        }
        if proxy:
            client_kwargs["proxy"] = proxy

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=8),
            retry=retry_if_exception_type(
                (httpx.TransportError, httpx.RemoteProtocolError, httpx.ReadTimeout)
            ),
            reraise=True,
        ):
            with attempt:
                async with httpx.AsyncClient(**client_kwargs) as client:
                    response = await client.get(settings.target_url)
                    # 403/429 → very likely an IP/bot block; bubble up so the
                    # outer loop counts errors and slows down.
                    if response.status_code in (403, 429, 503):
                        logger.warning(
                            f"Scanner blocked: HTTP {response.status_code} "
                            f"(proxy={'on' if proxy else 'off'})"
                        )
                        return None
                    response.raise_for_status()
                    return response.text
        return None

    # ------------------------------------------------------------------ #
    def _is_available(self, html: str) -> bool:
        """
        Heuristic availability check.

        Replace / extend with the real markers once you have inspected the
        target page. Two complementary strategies are used:

          1. The "no slots" string is *gone*.
          2. A booking CTA / slot button is *present*.
        """
        if not html:
            return False

        try:
            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text(" ", strip=True)
        except Exception:  # noqa: BLE001
            text = html

        negative = settings.negative_marker.lower() in text.lower()
        positive = settings.positive_marker.lower() in text.lower()

        # ───────────────────────────────────────────────────────────────
        # >>> CUSTOMISE ME <<<
        # Add stronger checks here once you know the DOM, e.g.:
        #
        #   button = soup.select_one("a.btn-primary[href*='anmeldung']")
        #   slot_count = len(soup.select("li.appointment-slot"))
        #   return button is not None or slot_count > 0
        # ───────────────────────────────────────────────────────────────

        return positive and not negative

    # ------------------------------------------------------------------ #
    async def run(self) -> None:
        logger.info(
            f"Scanner started — polling {settings.target_url} "
            f"every {settings.scan_interval_min}-{settings.scan_interval_max}s "
            f"(proxy={'ENABLED' if settings.proxy.enabled else 'disabled'})"
        )

        while not self._event.is_set():
            try:
                html = await self._fetch()
                if html and self._is_available(html):
                    logger.success("★ Slot detected! Triggering Sniper.")
                    self._event.set()
                    return
                self._consecutive_errors = 0
            except Exception as exc:  # noqa: BLE001
                self._consecutive_errors += 1
                logger.warning(
                    f"Scan failed ({self._consecutive_errors}): {exc!r}"
                )

            sleep_for = random_scan_interval(
                settings.scan_interval_min, settings.scan_interval_max
            )
            # Cool-off if we are being throttled
            if self._consecutive_errors >= 3:
                sleep_for *= 2 + random.random()
                logger.info(
                    f"Backing off → next scan in {sleep_for:.1f}s "
                    "(too many errors)"
                )

            await asyncio.sleep(sleep_for)
