"""
Central configuration for the Goethe-Institut appointment bot.

Replace placeholder URLs and selectors after inspecting the live portal with
DevTools (Elements tab). All selector constants are consumed by sniper.py.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# SCANNER — lightweight HTTP monitoring target
# ---------------------------------------------------------------------------

# TODO: Insert the exact Goethe-Institut booking / availability page URL here.
# Example shape (verify on your institute's portal):
#   https://www.goethe.de/.../examRegistration/...  or a JSON availability API.
SCANNER_TARGET_URL: str = os.getenv(
    "GOETHE_SCANNER_URL",
    "https://www.goethe.de/REPLACE_WITH_YOUR_INSTITUTE_BOOKING_URL",
)

# Polling interval bounds (seconds). A random value in this range is chosen each cycle.
SCAN_INTERVAL_MIN_SEC: float = 15.0
SCAN_INTERVAL_MAX_SEC: float = 30.0

# Text markers that indicate NO availability (scanner watches for these to disappear).
UNAVAILABLE_MARKERS: tuple[str, ...] = (
    "No appointments available",
    "Keine Termine verfügbar",
    "no appointments available",
)

# Text markers that positively indicate an open slot (any match triggers the sniper).
AVAILABLE_MARKERS: tuple[str, ...] = (
    "Book appointment",
    "Termin buchen",
    "Select date",
    "Jetzt buchen",
)

# Optional JSON keys to inspect when the endpoint returns JSON instead of HTML.
JSON_AVAILABILITY_KEYS: tuple[str, ...] = ("slots", "available", "appointments")

# ---------------------------------------------------------------------------
# SNIPER — Playwright booking portal
# ---------------------------------------------------------------------------

# TODO: Insert the full booking-flow entry URL (may differ from the scanner URL).
SNIPER_BOOKING_URL: str = os.getenv(
    "GOETHE_BOOKING_URL",
    "https://www.goethe.de/REPLACE_WITH_YOUR_INSTITUTE_BOOKING_FLOW_URL",
)

# macOS Chrome fingerprint (keep in sync with your installed Chrome major version).
MACOS_VIEWPORT: dict[str, int] = {"width": 1280, "height": 800}
MACOS_CHROME_USER_AGENT: str = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

CHROMIUM_LAUNCH_ARGS: list[str] = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

# ---------------------------------------------------------------------------
# FORM SELECTORS — replace after inspecting the booking form in DevTools
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FormSelectors:
    """CSS selectors for each field on the Goethe booking form."""

    # TODO: Right-click field in DevTools → Copy → Copy selector
    first_name: str = "#REPLACE_first_name"
    last_name: str = "#REPLACE_last_name"
    passport: str = "#REPLACE_passport"
    email: str = "#REPLACE_email"
    phone: str = "#REPLACE_phone"

    # TODO: Navigation / action buttons through the booking wizard
    continue_button: str = "button[type='submit']"
    confirm_button: str = "#REPLACE_confirm_booking"
    slot_option: str = ".REPLACE_slot-option"  # first available slot row/card


FORM_SELECTORS = FormSelectors()

# ---------------------------------------------------------------------------
# CLIENT DATA
# ---------------------------------------------------------------------------

CLIENT_JSON_PATH: Path = Path(
    os.getenv("GOETHE_CLIENT_JSON", "client.json")
)

# ---------------------------------------------------------------------------
# ROTATING RESIDENTIAL PROXIES
# ---------------------------------------------------------------------------

@dataclass
class ProxyConfig:
    """
    Placeholder for rotating residential proxy credentials.

  Insert your provider details below. Typical formats:
    - Single rotating endpoint: http://user:pass@gate.provider.com:PORT
    - Session-sticky rotation: append session id per request for a fresh IP

  Set enabled=True once credentials are configured.
    """

    enabled: bool = False

    # TODO: Replace with your residential proxy provider endpoint.
    rotating_endpoint: str = os.getenv(
        "GOETHE_PROXY_URL",
        "http://USERNAME:PASSWORD@gate.residential-proxy.example:8080",
    )

    # Some providers require a unique session token per request to rotate IPs.
    session_id_prefix: str = "goethe_scan_"


PROXY = ProxyConfig()

# ---------------------------------------------------------------------------
# TELEGRAM ALERTS
# ---------------------------------------------------------------------------

@dataclass
class TelegramConfig:
    enabled: bool = False
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "REPLACE_BOT_TOKEN")
    chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "REPLACE_CHAT_ID")


TELEGRAM = TelegramConfig()

# ---------------------------------------------------------------------------
# HUMAN SIMULATION TIMING
# ---------------------------------------------------------------------------

KEYSTROKE_DELAY_MIN_MS: int = 50
KEYSTROKE_DELAY_MAX_MS: int = 150
STEP_DELAY_MIN_SEC: float = 0.5
STEP_DELAY_MAX_SEC: float = 1.5

# ---------------------------------------------------------------------------
# RUNTIME
# ---------------------------------------------------------------------------

LOG_LEVEL: str = os.getenv("GOETHE_LOG_LEVEL", "INFO")
STOP_SCANNER_AFTER_TRIGGER: bool = True
SNIPER_TIMEOUT_MS: int = 60_000

REQUIRED_CLIENT_KEYS: tuple[str, ...] = (
    "first_name",
    "last_name",
    "passport",
    "email",
    "phone",
)
