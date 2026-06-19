"""
scanner.py — Lightweight, stealthy HTTP scanner for the Goethe-Institut booking portal.

Design goals:
  • No browser overhead — pure HTTP with httpx (supports HTTP/2).
  • IP rotation via a configurable residential proxy list.
  • Randomised scan intervals to avoid rate-limit patterns.
  • Signals the main orchestrator via an asyncio.Event when a slot is found.
"""

import asyncio
import random
import itertools
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from loguru import logger

import config
import notifier


# ---------------------------------------------------------------------------
# Proxy rotation helpers
# ---------------------------------------------------------------------------

def _load_proxies() -> list[str]:
    """
    Return the active proxy list.

    Priority:
      1. PROXY_FILE (newline-separated file on disk)
      2. PROXY_LIST constant in config.py
      3. Empty list → no proxy (direct connection, use only for testing)
    """
    if config.PROXY_FILE:
        path = Path(config.PROXY_FILE)
        if path.exists():
            proxies = [
                line.strip()
                for line in path.read_text().splitlines()
                if line.strip() and not line.startswith("#")
            ]
            logger.info(f"Loaded {len(proxies)} proxies from {config.PROXY_FILE}.")
            return proxies
        else:
            logger.warning(f"PROXY_FILE '{config.PROXY_FILE}' not found — falling back to PROXY_LIST.")

    if config.PROXY_LIST:
        logger.info(f"Using {len(config.PROXY_LIST)} proxies from config.PROXY_LIST.")
        return config.PROXY_LIST

    logger.warning(
        "No proxies configured. Running without a proxy is acceptable for "
        "local testing but risks an IP ban in production."
    )
    return []


def _proxy_cycle(proxies: list[str]):
    """
    Infinite round-robin iterator over the proxy list.
    Returns None if the list is empty (direct connection).
    """
    if not proxies:
        return itertools.repeat(None)
    return itertools.cycle(proxies)


# ---------------------------------------------------------------------------
# HTTP request helpers
# ---------------------------------------------------------------------------

# Rotate through a small set of realistic Accept-Language values
_ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "en-GB,en;q=0.9",
    "fr-FR,fr;q=0.9,en-US;q=0.8",
]

def _build_headers() -> dict[str, str]:
    """Construct request headers that mimic a real browser."""
    return {
        "User-Agent": config.USER_AGENT,
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": random.choice(_ACCEPT_LANGUAGES),
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }


async def _fetch(url: str, proxy: str | None) -> str | None:
    """
    Perform a single GET request and return the response body as text.
    Returns None on any error so the scan loop can continue gracefully.
    """
    proxy_config = {"http://": proxy, "https://": proxy} if proxy else None

    try:
        async with httpx.AsyncClient(
            headers=_build_headers(),
            proxies=proxy_config,
            follow_redirects=True,
            timeout=20,
            http2=True,         # HTTP/2 is less fingerprintable than HTTP/1.1
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text

    except httpx.ProxyError as exc:
        logger.warning(f"Proxy error ({proxy}): {exc} — rotating to next proxy.")
    except httpx.HTTPStatusError as exc:
        logger.warning(f"HTTP {exc.response.status_code} from server — will retry.")
    except httpx.TimeoutException:
        logger.warning("Request timed out — will retry.")
    except Exception as exc:
        logger.warning(f"Unexpected fetch error: {exc}")

    return None


# ---------------------------------------------------------------------------
# Availability detection
# ---------------------------------------------------------------------------

def _slot_available(html: str) -> bool:
    """
    Return True when the page indicates an appointment slot is available.

    Two independent checks are performed (either is sufficient):
      1. NO_SLOT_MARKER text is absent from the page.
      2. AVAILABLE_SLOT_SELECTOR matches at least one element (if configured).

    ── HOW TO CALIBRATE ────────────────────────────────────────────────────
    Open the booking page in your browser when no slots exist, then:
      • Copy the exact "no availability" message and set it as NO_SLOT_MARKER.
      • When a slot IS available, note any distinctive element (button, link)
        and set its CSS selector as AVAILABLE_SLOT_SELECTOR in config.py.
    ────────────────────────────────────────────────────────────────────────
    """
    soup = BeautifulSoup(html, "lxml")

    # Check 1 — absence of the "no slots" marker text
    page_text = soup.get_text(separator=" ", strip=True)
    marker_absent = config.NO_SLOT_MARKER.lower() not in page_text.lower()

    # Check 2 — presence of a known "slot available" element (optional)
    selector_match = False
    if config.AVAILABLE_SLOT_SELECTOR:
        selector_match = bool(soup.select(config.AVAILABLE_SLOT_SELECTOR))

    if config.AVAILABLE_SLOT_SELECTOR:
        # Both signals configured: either triggers
        return marker_absent or selector_match
    else:
        # Only marker check active
        return marker_absent


def _extract_slot_info(html: str) -> str:
    """
    Attempt to pull a human-readable summary of the available slot(s)
    for inclusion in the alert notification.

    ── CUSTOMISE ───────────────────────────────────────────────────────────
    Update the CSS selector / regex below once you know the page structure.
    ────────────────────────────────────────────────────────────────────────
    """
    soup = BeautifulSoup(html, "lxml")

    # PLACEHOLDER: adjust selector to match the slot date/time element
    slot_elements = soup.select(".appointment-slot, .slot-date, .booking-time")
    if slot_elements:
        slots = [el.get_text(strip=True) for el in slot_elements[:5]]
        return "Available slots: " + " | ".join(slots)

    return "Slot details unavailable — check the booking page directly."


# ---------------------------------------------------------------------------
# Main scan loop
# ---------------------------------------------------------------------------

async def run_scanner(slot_found_event: asyncio.Event) -> None:
    """
    Continuously poll the booking page.

    When a slot is detected:
      • Fires `slot_found_event` to wake the Sniper.
      • Sends a Telegram notification.
      • Stops scanning (the Sniper takes over).

    Args:
        slot_found_event: Shared asyncio.Event; set here, awaited by the Sniper.
    """
    proxies = _load_proxies()
    proxy_iter = _proxy_cycle(proxies)
    scan_count = 0

    logger.info(f"Scanner started. Target: {config.TARGET_URL}")
    logger.info(
        f"Scan interval: {config.SCAN_INTERVAL_MIN}–{config.SCAN_INTERVAL_MAX}s | "
        f"Proxies: {len(proxies) if proxies else 'none (direct)'}"
    )

    while not slot_found_event.is_set():
        scan_count += 1
        proxy = next(proxy_iter)
        proxy_label = proxy.split("@")[-1] if proxy else "direct"

        logger.info(f"[Scan #{scan_count}] Fetching via {proxy_label} …")
        html = await _fetch(config.TARGET_URL, proxy)

        if html is None:
            logger.warning(f"[Scan #{scan_count}] No response received — skipping detection.")
        else:
            if _slot_available(html):
                slot_info = _extract_slot_info(html)
                logger.success(f"[Scan #{scan_count}] SLOT DETECTED! {slot_info}")

                await notifier.notify(
                    f"🎯 <b>Goethe Appointment Slot Found!</b>\n"
                    f"{slot_info}\n"
                    f"URL: {config.TARGET_URL}"
                )

                # Signal the sniper to take over
                slot_found_event.set()
                return
            else:
                logger.info(f"[Scan #{scan_count}] No slots yet — page shows busy/unavailable.")

        # Randomised wait prevents detectable request cadence
        wait = random.uniform(config.SCAN_INTERVAL_MIN, config.SCAN_INTERVAL_MAX)
        logger.debug(f"Next scan in {wait:.1f}s …")
        await asyncio.sleep(wait)
