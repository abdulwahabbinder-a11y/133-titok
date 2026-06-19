"""
Scanner -- lightweight async monitor for the Goethe-Institut booking page.

Design goals
------------
* No browser is launched here. We only do plain HTTP requests with `httpx`
  to keep RAM/CPU usage low and avoid heating up bot-detection signals.
* Every request goes through a fresh rotating residential proxy (when
  configured) so we never hammer the site from the same IP.
* A randomised polling interval (15-30 s by default, see `config.py`) makes
  the traffic pattern look organic.
* The detection logic is *content based*: we look for known "sold out"
  copy on the page and for positive markers like "book now".

The Scanner exposes a single async coroutine, `run_scanner(...)`, that yields
control back to the orchestrator via an `asyncio.Event` as soon as slots are
detected.
"""

from __future__ import annotations

import asyncio
import itertools
import logging
import random
from dataclasses import dataclass
from typing import Iterator, List, Optional

import httpx

import config

log = logging.getLogger("scanner")


# ---------------------------------------------------------------------------
# Proxy rotation helpers
# ---------------------------------------------------------------------------

def _proxy_iterator() -> Iterator[Optional[str]]:
    """Infinite iterator that yields a proxy URL for each request.

    Behaviour:
    * If a rotating *gateway* is set, return it every time (the upstream
      gateway handles IP rotation on its end).
    * If a *pool* is set, cycle through it.
    * Otherwise yield `None` (direct connection).
    """
    proxy_cfg = config.PROXY

    if proxy_cfg.gateway:
        log.info("Using rotating proxy gateway.")
        while True:
            yield proxy_cfg.gateway

    if proxy_cfg.pool:
        log.info("Using proxy pool of %d entries.", len(proxy_cfg.pool))
        for prx in itertools.cycle(proxy_cfg.pool):
            yield prx

    log.warning(
        "No proxy configured. Running with the host IP -- not recommended "
        "for production sniping."
    )
    while True:
        yield None


# ---------------------------------------------------------------------------
# Request layer
# ---------------------------------------------------------------------------

# A small pool of realistic browser headers. We randomise per-request to
# avoid an obvious "same headers every poll" signature.
_ACCEPT_LANGS = ["de-DE,de;q=0.9,en;q=0.7", "en-US,en;q=0.9,de;q=0.6"]


def _build_headers() -> dict:
    return {
        "User-Agent":      config.USER_AGENT,
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,"
                           "application/json;q=0.8,*/*;q=0.5",
        "Accept-Language": random.choice(_ACCEPT_LANGS),
        "Cache-Control":   "no-cache",
        "Pragma":          "no-cache",
        "Sec-Fetch-Dest":  "document",
        "Sec-Fetch-Mode":  "navigate",
        "Sec-Fetch-Site":  "none",
        "Sec-Fetch-User":  "?1",
        "Upgrade-Insecure-Requests": "1",
    }


@dataclass
class ScanResult:
    available: bool
    status_code: int
    body_excerpt: str
    proxy_used: Optional[str]


async def _scan_once(client: httpx.AsyncClient, proxy: Optional[str]) -> ScanResult:
    """Perform a single scan request.

    httpx 0.27 still creates a fresh transport per `proxies=` value, so the
    cleanest way to swap proxies between requests is to pass the proxy to a
    *new* short-lived client. We do this in `run_scanner` below.

    This helper purely interprets the response.
    """
    resp = await client.get(config.TARGET_URL, headers=_build_headers())
    body = resp.text or ""

    lowered = body.lower()

    sold_out_hit = any(
        marker.lower() in lowered for marker in config.SOLD_OUT_MARKERS
    )
    available_hit = any(
        marker.lower() in lowered for marker in config.AVAILABLE_MARKERS
    )

    available = available_hit or (not sold_out_hit and resp.status_code == 200)

    return ScanResult(
        available=available,
        status_code=resp.status_code,
        body_excerpt=body[:160].replace("\n", " "),
        proxy_used=proxy,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def run_scanner(slot_open_event: asyncio.Event) -> None:
    """Continuously poll the target URL until a slot is detected.

    Sets `slot_open_event` and *returns* (does not raise) once availability
    is detected so the orchestrator can hand off to the Sniper.
    """
    proxies = _proxy_iterator()
    poll_counter = 0
    consecutive_errors = 0

    log.info("Scanner armed. Target: %s", config.TARGET_URL)

    while not slot_open_event.is_set():
        poll_counter += 1
        proxy = next(proxies)

        try:
            # NOTE: a *fresh* AsyncClient per request because we want a new
            # TCP/TLS session for each rotated proxy (avoids re-using a
            # previously fingerprinted connection).
            async with httpx.AsyncClient(
                http2=True,
                timeout=config.SCAN_TIMEOUT,
                follow_redirects=True,
                proxy=proxy,
            ) as client:
                result = await _scan_once(client, proxy)

            consecutive_errors = 0

            log.info(
                "Scan #%d  ->  status=%s  available=%s  proxy=%s",
                poll_counter,
                result.status_code,
                result.available,
                _redact_proxy(proxy),
            )
            log.debug("Body excerpt: %s", result.body_excerpt)

            if result.available:
                log.warning("!!! SLOT DETECTED -- waking the Sniper !!!")
                slot_open_event.set()
                return

        except httpx.HTTPError as exc:
            consecutive_errors += 1
            log.warning(
                "Scan #%d failed (%s). consecutive_errors=%d",
                poll_counter, exc, consecutive_errors,
            )
            if consecutive_errors >= 5:
                # backoff to avoid blasting a broken upstream
                log.error("Too many errors in a row; backing off for 60 s")
                await asyncio.sleep(60)
                consecutive_errors = 0
                continue

        # randomised cool-down between polls
        delay = random.uniform(config.SCAN_INTERVAL_MIN, config.SCAN_INTERVAL_MAX)
        log.debug("Sleeping %.2fs before next scan ...", delay)
        await asyncio.sleep(delay)


def _redact_proxy(proxy: Optional[str]) -> str:
    """Avoid printing credentials in logs."""
    if not proxy:
        return "direct"
    try:
        # crude but safe: strip the userinfo segment
        if "@" in proxy:
            scheme, rest = proxy.split("://", 1)
            return f"{scheme}://***@{rest.split('@', 1)[1]}"
    except Exception:                                          # noqa: BLE001
        pass
    return proxy


# ---------------------------------------------------------------------------
# CLI smoke-test:   python -m scanner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    async def _main() -> None:
        config.configure_logging(logging.DEBUG)
        evt = asyncio.Event()
        await run_scanner(evt)
        log.info("Scanner exited; slot_open=%s", evt.is_set())

    asyncio.run(_main())
