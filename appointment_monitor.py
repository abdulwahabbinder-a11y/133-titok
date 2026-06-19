#!/usr/bin/env python3
"""Goethe-Institut appointment availability monitor with assisted browser launch.

This script intentionally implements a compliant workflow:

* lightweight HTTP polling for public availability changes;
* randomized, conservative scan intervals;
* optional Telegram notification when a slot appears;
* a visible Playwright browser opened for manual completion.

It does not include proxy rotation, CAPTCHA bypass, anti-bot fingerprint evasion, or
automated form submission against a third-party booking portal.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import random
import signal
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import Browser, Page, async_playwright


LOGGER = logging.getLogger("appointment_monitor")

# Clean, ordinary macOS Chrome user agent for browser compatibility.
MACOS_CHROME_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class MonitorConfig:
    """Runtime configuration for scanning and assisted booking."""

    # TODO: Replace with the Goethe-Institut booking/availability URL you inspect.
    scan_url: str = "https://www.goethe.de/INS/REPLACE_WITH_TARGET_BOOKING_PAGE"

    # TODO: Usually the same as scan_url unless the availability endpoint differs.
    booking_url: str = "https://www.goethe.de/INS/REPLACE_WITH_TARGET_BOOKING_PAGE"

    # Keep scan cadence respectful and jittered.
    min_scan_interval_seconds: float = 15.0
    max_scan_interval_seconds: float = 30.0

    request_timeout_seconds: float = 12.0
    max_consecutive_errors: int = 5

    # TODO: Adjust these after inspecting the real page text for your locale.
    unavailable_markers: tuple[str, ...] = (
        "No appointments available",
        "Keine Termine verfügbar",
        "currently no appointments",
    )

    # TODO: Add CSS selectors that only appear when actual appointment choices exist.
    # Examples after inspection might look like:
    # (".appointment-slot", "button[data-testid='book-appointment']")
    availability_selectors: tuple[str, ...] = ()

    client_json_path: Path = Path("client.json")

    # Optional Telegram alert placeholders. Prefer environment variables for secrets.
    telegram_bot_token_env: str = "TELEGRAM_BOT_TOKEN"
    telegram_chat_id_env: str = "TELEGRAM_CHAT_ID"

    # Visible browser settings for macOS-sized manual intervention.
    browser_headless: bool = False
    browser_viewport: dict[str, int] = field(
        default_factory=lambda: {"width": 1280, "height": 800}
    )


@dataclass(frozen=True)
class ClientData:
    """Locally stored appointment applicant data."""

    first_name: str
    last_name: str
    passport: str
    email: str
    phone: str

    @classmethod
    def from_json(cls, path: Path) -> "ClientData":
        """Load applicant data from client.json."""

        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"Missing {path}. Copy client.example.json to client.json first."
            ) from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"{path} contains invalid JSON: {exc}") from exc

        required_keys = {"first_name", "last_name", "passport", "email", "phone"}
        missing_keys = sorted(required_keys - raw_data.keys())
        if missing_keys:
            raise RuntimeError(
                f"{path} is missing required keys: {', '.join(missing_keys)}"
            )

        return cls(
            first_name=str(raw_data["first_name"]),
            last_name=str(raw_data["last_name"]),
            passport=str(raw_data["passport"]),
            email=str(raw_data["email"]),
            phone=str(raw_data["phone"]),
        )

    def redacted_summary(self) -> str:
        """Return a terminal-safe summary for manual booking reference."""

        return (
            f"{self.first_name} {self.last_name} | "
            f"passport={_redact(self.passport)} | "
            f"email={_redact_email(self.email)} | "
            f"phone={_redact(self.phone)}"
        )


@dataclass(frozen=True)
class ScanResult:
    """Parsed result of one availability scan."""

    available: bool
    changed: bool
    status_code: int
    content_hash: str
    reason: str


class AvailabilityScanner:
    """Lightweight HTTP scanner that avoids launching a browser."""

    def __init__(self, config: MonitorConfig) -> None:
        self._config = config
        self._last_content_hash: str | None = None

    async def scan_once(self) -> ScanResult:
        """Fetch the configured page/endpoint and infer availability."""

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "application/json;q=0.8,*/*;q=0.7",
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
            "Cache-Control": "no-cache",
            "User-Agent": MACOS_CHROME_USER_AGENT,
        }

        async with httpx.AsyncClient(
            timeout=self._config.request_timeout_seconds,
            follow_redirects=True,
            headers=headers,
        ) as client:
            response = await client.get(self._config.scan_url)

        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        text = response.text
        content_hash = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
        changed = content_hash != self._last_content_hash
        self._last_content_hash = content_hash

        available, reason = self._detect_availability(text, content_type)
        return ScanResult(
            available=available,
            changed=changed,
            status_code=response.status_code,
            content_hash=content_hash,
            reason=reason,
        )

    def _detect_availability(self, text: str, content_type: str) -> tuple[bool, str]:
        """Detect availability using JSON fields, selectors, and text markers."""

        if "application/json" in content_type:
            available, reason = self._detect_json_availability(text)
            if available:
                return available, reason

        soup = BeautifulSoup(text, "html.parser")

        for selector in self._config.availability_selectors:
            if soup.select_one(selector):
                return True, f"availability selector matched: {selector}"

        normalized_text = " ".join(soup.get_text(" ", strip=True).split())
        lower_text = normalized_text.lower()
        unavailable_present = any(
            marker.lower() in lower_text
            for marker in self._config.unavailable_markers
        )

        if unavailable_present:
            return False, "unavailable marker still present"

        if normalized_text:
            return True, "unavailable marker disappeared"

        return False, "empty or unparsable response"

    @staticmethod
    def _detect_json_availability(text: str) -> tuple[bool, str]:
        """Look for common availability keys in JSON responses."""

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return False, "JSON content-type but response is not valid JSON"

        stack: list[Any] = [payload]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                for key, value in current.items():
                    lower_key = str(key).lower()
                    if lower_key in {"available", "hasavailability", "slotsavailable"}:
                        if bool(value):
                            return True, f"JSON field {key} is truthy"
                    if lower_key in {"slots", "appointments", "dates", "times"}:
                        if isinstance(value, list) and len(value) > 0:
                            return True, f"JSON field {key} contains entries"
                    stack.append(value)
            elif isinstance(current, list):
                stack.extend(current)

        return False, "no available JSON fields found"


class AssistedBookingBrowser:
    """Visible Playwright browser opened when availability is detected."""

    def __init__(self, config: MonitorConfig, client_data: ClientData) -> None:
        self._config = config
        self._client_data = client_data

    async def open(self) -> None:
        """Launch Chromium and navigate to the booking URL for manual completion."""

        LOGGER.warning("Slot signal detected. Opening assisted browser now.")
        LOGGER.info("Client reference: %s", self._client_data.redacted_summary())

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=self._config.browser_headless,
                args=[],
            )
            try:
                page = await self._new_page(browser)
                await page.goto(self._config.booking_url, wait_until="domcontentloaded")
                await self._show_manual_booking_banner(page)
                LOGGER.warning(
                    "Browser is open. Complete the booking manually in the visible window."
                )

                # Keep the browser alive until the operator stops the script.
                while True:
                    await asyncio.sleep(1)
            finally:
                await browser.close()

    async def _new_page(self, browser: Browser) -> Page:
        context = await browser.new_context(
            viewport=self._config.browser_viewport,
            user_agent=MACOS_CHROME_USER_AGENT,
            locale="en-US",
            timezone_id="Europe/Berlin",
        )
        return await context.new_page()

    async def _show_manual_booking_banner(self, page: Page) -> None:
        """Add an in-page reminder without interacting with protected form fields."""

        summary = self._client_data.redacted_summary().replace("`", "'")
        await page.evaluate(
            """(summary) => {
                const banner = document.createElement('div');
                banner.textContent = `Availability detected. Complete booking manually. ${summary}`;
                banner.style.position = 'fixed';
                banner.style.top = '0';
                banner.style.left = '0';
                banner.style.right = '0';
                banner.style.zIndex = '2147483647';
                banner.style.padding = '10px 14px';
                banner.style.background = '#0f172a';
                banner.style.color = '#fff';
                banner.style.font = '14px system-ui, -apple-system, BlinkMacSystemFont, sans-serif';
                banner.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.25)';
                document.documentElement.appendChild(banner);
            }""",
            summary,
        )


async def send_telegram_alert(config: MonitorConfig, message: str) -> None:
    """Send a Telegram alert if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set."""

    bot_token = os.getenv(config.telegram_bot_token_env)
    chat_id = os.getenv(config.telegram_chat_id_env)
    if not bot_token or not chat_id:
        LOGGER.warning("ALERT PLACEHOLDER: %s", message)
        LOGGER.warning(
            "Set %s and %s to enable Telegram notifications.",
            config.telegram_bot_token_env,
            config.telegram_chat_id_env,
        )
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "disable_web_page_preview": True}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()


async def monitor(config: MonitorConfig) -> None:
    """Run the scanner loop and launch the assisted browser once a slot appears."""

    client_data = ClientData.from_json(config.client_json_path)
    scanner = AvailabilityScanner(config)
    consecutive_errors = 0

    LOGGER.info("Starting scanner for %s", config.scan_url)
    LOGGER.info("Loaded client data: %s", client_data.redacted_summary())

    while True:
        try:
            result = await scanner.scan_once()
            consecutive_errors = 0
            LOGGER.info(
                "scan status=%s available=%s changed=%s reason=%s hash=%s",
                result.status_code,
                result.available,
                result.changed,
                result.reason,
                result.content_hash[:12],
            )

            if result.available:
                await send_telegram_alert(
                    config,
                    f"Appointment availability signal detected: {config.booking_url}",
                )
                browser = AssistedBookingBrowser(config, client_data)
                await browser.open()
                return

        except Exception as exc:  # noqa: BLE001 - keep monitor resilient.
            consecutive_errors += 1
            LOGGER.exception(
                "scan failed (%s/%s): %s",
                consecutive_errors,
                config.max_consecutive_errors,
                exc,
            )
            if consecutive_errors >= config.max_consecutive_errors:
                await send_telegram_alert(
                    config,
                    f"Appointment monitor has repeated scan failures: {exc}",
                )
                consecutive_errors = 0

        sleep_seconds = random.uniform(
            config.min_scan_interval_seconds,
            config.max_scan_interval_seconds,
        )
        LOGGER.info("sleeping %.1f seconds before next scan", sleep_seconds)
        await asyncio.sleep(sleep_seconds)


def build_config_from_env() -> MonitorConfig:
    """Build configuration from environment variables, with placeholders as defaults."""

    default_config = MonitorConfig()
    return MonitorConfig(
        scan_url=os.getenv("GOETHE_SCAN_URL", default_config.scan_url),
        booking_url=os.getenv("GOETHE_BOOKING_URL", default_config.booking_url),
        min_scan_interval_seconds=float(
            os.getenv(
                "MIN_SCAN_INTERVAL_SECONDS",
                str(default_config.min_scan_interval_seconds),
            )
        ),
        max_scan_interval_seconds=float(
            os.getenv(
                "MAX_SCAN_INTERVAL_SECONDS",
                str(default_config.max_scan_interval_seconds),
            )
        ),
        request_timeout_seconds=float(
            os.getenv(
                "REQUEST_TIMEOUT_SECONDS",
                str(default_config.request_timeout_seconds),
            )
        ),
        max_consecutive_errors=int(
            os.getenv("MAX_CONSECUTIVE_ERRORS", str(default_config.max_consecutive_errors))
        ),
        unavailable_markers=tuple(
            marker.strip()
            for marker in os.getenv(
                "UNAVAILABLE_MARKERS",
                "|".join(default_config.unavailable_markers),
            ).split("|")
            if marker.strip()
        ),
        availability_selectors=tuple(
            selector.strip()
            for selector in os.getenv("AVAILABILITY_SELECTORS", "").split("|")
            if selector.strip()
        ),
        client_json_path=Path(
            os.getenv("CLIENT_JSON_PATH", str(default_config.client_json_path))
        ),
        telegram_bot_token_env=default_config.telegram_bot_token_env,
        telegram_chat_id_env=default_config.telegram_chat_id_env,
        browser_headless=False,
        browser_viewport=default_config.browser_viewport,
    )


def configure_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _redact(value: str, visible: int = 3) -> str:
    if len(value) <= visible:
        return "*" * len(value)
    return f"{value[:visible]}{'*' * max(3, len(value) - visible)}"


def _redact_email(email: str) -> str:
    local_part, separator, domain = email.partition("@")
    if not separator:
        return _redact(email)
    return f"{_redact(local_part, visible=2)}@{domain}"


async def _main() -> None:
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for signum in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signum, stop_event.set)

    config = build_config_from_env()
    monitor_task = asyncio.create_task(monitor(config))
    stop_task = asyncio.create_task(stop_event.wait())

    done, pending = await asyncio.wait(
        {monitor_task, stop_task},
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)

    for task in done:
        task.result()


if __name__ == "__main__":
    configure_logging()
    asyncio.run(_main())
