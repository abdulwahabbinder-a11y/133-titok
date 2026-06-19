#!/usr/bin/env python3
"""
Compliant Goethe-Institut appointment availability monitor.

This tool intentionally does not bypass anti-bot protections, rotate residential
proxies, solve CAPTCHAs, hide automation fingerprints, or submit booking forms.
It performs lightweight availability checks and opens the official booking page
for manual completion when a potential slot is detected.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import random
import re
import signal
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import httpx
from bs4 import BeautifulSoup


# TODO: Replace this with the specific Goethe-Institut booking page URL after
# you confirm that automated monitoring is permitted for that endpoint.
DEFAULT_BOOKING_URL = "https://www.goethe.de/REPLACE-WITH-BOOKING-PAGE"

MACOS_CHROME_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class ClientData:
    first_name: str
    last_name: str
    passport: str
    email: str
    phone: str


@dataclass(frozen=True)
class MonitorConfig:
    booking_url: str
    client_json: Path
    min_scan_delay_seconds: float = 15.0
    max_scan_delay_seconds: float = 30.0
    request_timeout_seconds: float = 15.0
    manual_session_minutes: int = 30
    scanner_user_agent: str = MACOS_CHROME_USER_AGENT
    browser_user_agent: str = MACOS_CHROME_USER_AGENT
    unavailable_markers: tuple[str, ...] = (
        "No appointments available",
        "No dates available",
        "fully booked",
    )
    positive_slot_patterns: tuple[str, ...] = (
        r"\bappointments?\s+available\b",
        r"\bavailable\s+appointments?\b",
        r"\bbook\s+now\b",
        r"\bselect\s+(an?\s+)?appointment\b",
    )
    # Optional single outbound proxy for permitted network routing. This is not
    # a residential proxy rotator and should not be used to evade rate limits.
    proxy_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "MonitorConfig":
        return cls(
            booking_url=args.url or os.getenv("BOOKING_URL", DEFAULT_BOOKING_URL),
            client_json=Path(args.client_json),
            min_scan_delay_seconds=args.min_delay,
            max_scan_delay_seconds=args.max_delay,
            request_timeout_seconds=args.timeout,
            manual_session_minutes=args.manual_session_minutes,
            proxy_url=os.getenv("HTTP_PROXY_URL"),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        )


@dataclass(frozen=True)
class ScanResult:
    url: str
    status_code: int
    content_hash: str
    unavailable_marker_found: bool
    positive_slot_signal_found: bool
    potential_slot_found: bool
    reason: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Monitor an appointment page and open a browser for manual booking "
            "when availability is detected."
        )
    )
    parser.add_argument(
        "--url",
        help=(
            "Booking page URL. You can also set BOOKING_URL. "
            "Replace the placeholder before running."
        ),
    )
    parser.add_argument(
        "--client-json",
        default="client.json",
        help="Path to local client data JSON. Defaults to client.json.",
    )
    parser.add_argument(
        "--min-delay",
        type=float,
        default=15.0,
        help="Minimum delay between scans in seconds.",
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=30.0,
        help="Maximum delay between scans in seconds.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="HTTP request timeout in seconds.",
    )
    parser.add_argument(
        "--manual-session-minutes",
        type=int,
        default=30,
        help="How long to keep Chromium open after a slot alert.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one scan and exit without launching Chromium.",
    )
    return parser.parse_args()


def load_client_data(path: Path) -> ClientData:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(
            f"Missing {path}. Copy client.example.json to {path} and fill it in."
        ) from exc

    required_fields = ("first_name", "last_name", "passport", "email", "phone")
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        raise SystemExit(f"{path} is missing required fields: {', '.join(missing)}")

    return ClientData(**{field: str(payload[field]) for field in required_fields})


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def flatten_json(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(flatten_json(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(flatten_json(item) for item in value)
    return str(value)


def response_to_text(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "")
    if "json" in content_type:
        try:
            return normalize_whitespace(flatten_json(response.json()))
        except json.JSONDecodeError:
            return normalize_whitespace(response.text)

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return normalize_whitespace(soup.get_text(" "))


def contains_any_marker(text: str, markers: Iterable[str]) -> bool:
    lowered_text = text.lower()
    return any(marker.lower() in lowered_text for marker in markers)


def contains_any_pattern(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def analyze_response(config: MonitorConfig, response: httpx.Response) -> ScanResult:
    text = response_to_text(response)
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    unavailable_marker_found = contains_any_marker(text, config.unavailable_markers)
    positive_slot_signal_found = contains_any_pattern(text, config.positive_slot_patterns)

    if unavailable_marker_found:
        potential_slot_found = False
        reason = "unavailable marker still present"
    elif positive_slot_signal_found:
        potential_slot_found = True
        reason = "positive availability phrase matched"
    else:
        potential_slot_found = True
        reason = "configured unavailable marker is absent"

    return ScanResult(
        url=str(response.url),
        status_code=response.status_code,
        content_hash=content_hash,
        unavailable_marker_found=unavailable_marker_found,
        positive_slot_signal_found=positive_slot_signal_found,
        potential_slot_found=potential_slot_found,
        reason=reason,
    )


async def send_notification(config: MonitorConfig, message: str) -> None:
    """Telegram placeholder.

    To enable Telegram alerts, export TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.
    The function logs the alert when those variables are not configured.
    """
    if not config.telegram_bot_token or not config.telegram_chat_id:
        logging.warning("ALERT placeholder: %s", message)
        return

    url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
    payload = {"chat_id": config.telegram_chat_id, "text": message}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except httpx.HTTPError:
        logging.exception("Failed to send Telegram notification")


async def fetch_scan_result(
    config: MonitorConfig, client: httpx.AsyncClient
) -> ScanResult:
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "user-agent": config.scanner_user_agent,
    }
    response = await client.get(config.booking_url, headers=headers)
    response.raise_for_status()
    return analyze_response(config, response)


async def open_booking_page_for_manual_completion(
    config: MonitorConfig, client_data: ClientData
) -> None:
    """Open Chromium and leave the session to the user.

    TODO after inspecting the site: keep a private note of the field selectors
    you need while completing the booking manually. This script deliberately
    avoids automated form filling or submission on a third-party booking portal.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise SystemExit(
            "Playwright is not installed. Run: pip install -r requirements.txt "
            "&& python -m playwright install chromium"
        ) from exc

    logging.info(
        "Opening browser for manual booking for %s %s (%s).",
        client_data.first_name,
        client_data.last_name,
        client_data.email,
    )

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=False,
            args=[
                "--start-maximized",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=config.browser_user_agent,
            locale="en-US",
        )
        page = await context.new_page()
        await page.goto(config.booking_url, wait_until="domcontentloaded")
        await page.bring_to_front()
        await send_notification(
            config,
            "Booking page opened. Complete the Goethe-Institut flow manually.",
        )
        logging.info(
            "Chromium will remain open for %s minutes unless you close it first.",
            config.manual_session_minutes,
        )
        await page.wait_for_timeout(config.manual_session_minutes * 60 * 1000)
        await context.close()
        await browser.close()


async def monitor_loop(
    config: MonitorConfig, client_data: ClientData, run_once: bool
) -> None:
    if config.booking_url == DEFAULT_BOOKING_URL:
        raise SystemExit(
            "Set BOOKING_URL or pass --url with the exact Goethe-Institut portal URL."
        )
    if config.min_scan_delay_seconds <= 0 or config.max_scan_delay_seconds <= 0:
        raise SystemExit("Scan delays must be positive.")
    if config.min_scan_delay_seconds > config.max_scan_delay_seconds:
        raise SystemExit("--min-delay cannot be greater than --max-delay.")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signame in ("SIGINT", "SIGTERM"):
        try:
            loop.add_signal_handler(
                getattr(signal, signame),
                stop_event.set,
            )
        except NotImplementedError:
            # Windows event loops do not support add_signal_handler.
            pass

    timeout = httpx.Timeout(config.request_timeout_seconds)
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=timeout,
        proxy=config.proxy_url,
    ) as http_client:
        last_hash: str | None = None
        while not stop_event.is_set():
            try:
                result = await fetch_scan_result(config, http_client)
            except httpx.HTTPStatusError as exc:
                logging.warning(
                    "Scan failed with HTTP %s for %s",
                    exc.response.status_code,
                    exc.request.url,
                )
            except httpx.HTTPError:
                logging.exception("Scan failed due to a network error")
            else:
                changed = last_hash is not None and result.content_hash != last_hash
                logging.info(
                    "Scan status=%s changed=%s potential_slot=%s reason=%s",
                    result.status_code,
                    changed,
                    result.potential_slot_found,
                    result.reason,
                )
                last_hash = result.content_hash

                if result.potential_slot_found:
                    await send_notification(
                        config,
                        (
                            "Potential Goethe-Institut appointment slot detected: "
                            f"{result.reason}. Open {config.booking_url}"
                        ),
                    )
                    if not run_once:
                        await open_booking_page_for_manual_completion(
                            config, client_data
                        )
                    return

            if run_once:
                return

            delay = random.uniform(
                config.min_scan_delay_seconds, config.max_scan_delay_seconds
            )
            logging.info("Next scan in %.1f seconds", delay)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=delay)
            except asyncio.TimeoutError:
                continue


async def async_main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    config = MonitorConfig.from_args(args)
    client_data = load_client_data(config.client_json)
    await monitor_loop(config, client_data, run_once=args.once)


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
