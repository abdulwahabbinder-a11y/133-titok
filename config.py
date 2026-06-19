"""
config.py — Central configuration for the Goethe-Institut appointment bot.

HOW TO USE:
  1. Copy .env.example to .env and fill in your secrets.
  2. Edit the TARGET_* constants below to match the exact booking portal URL
     and the CSS/XPath selectors you discover by inspecting the page.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# TARGET — fill these in after inspecting the Goethe-Institut booking portal
# ---------------------------------------------------------------------------

# Full URL of the appointment-search or calendar page.
# Example: "https://www.goethe.de/en/spr/kup/prf/ter.html"
#          or a JSON API endpoint the page calls via XHR.
TARGET_URL: str = "https://REPLACE_WITH_GOETHE_BOOKING_URL"

# Text or pattern that appears when NO slots are free.
# The scanner watches for its disappearance / change.
NO_SLOT_MARKER: str = "No appointments available"

# Optional: a CSS selector whose presence indicates an *available* slot.
# Leave empty ("") to rely solely on NO_SLOT_MARKER disappearing.
AVAILABLE_SLOT_SELECTOR: str = ""  # e.g. "button.book-slot" or "a.appointment-link"

# ---------------------------------------------------------------------------
# SCAN TIMING
# ---------------------------------------------------------------------------

SCAN_INTERVAL_MIN: float = 15.0   # seconds — minimum wait between scans
SCAN_INTERVAL_MAX: float = 30.0   # seconds — maximum wait between scans

# ---------------------------------------------------------------------------
# PROXY CONFIGURATION (Rotating Residential Proxies)
# ---------------------------------------------------------------------------
# Format expected by httpx: "http://user:pass@host:port"
# Set PROXY_LIST to a list of proxy strings, or load them from a file/env.
# The scanner will rotate through these on every request.
#
# If you use a smart rotating endpoint (e.g. Bright Data / Oxylabs),
# just put that single endpoint here and it handles rotation server-side.

PROXY_LIST: list[str] = [
    # "http://USERNAME:PASSWORD@gate.smartproxy.com:7000",
    # "http://USERNAME:PASSWORD@residential.proxy-provider.com:8080",
]

# Path to a newline-separated proxy list file (optional, overrides PROXY_LIST).
PROXY_FILE: str = ""  # e.g. "proxies.txt"

# ---------------------------------------------------------------------------
# BROWSER / SNIPER SETTINGS
# ---------------------------------------------------------------------------

HEADLESS: bool = False          # Keep False — allows manual CAPTCHA solving
BROWSER_TIMEOUT: int = 30_000   # milliseconds for Playwright waits

VIEWPORT: dict = {"width": 1280, "height": 800}

# macOS Chrome 124 User-Agent — update to the latest stable version as needed
USER_AGENT: str = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Extra Chromium launch args to suppress automation signals
CHROMIUM_ARGS: list[str] = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-extensions",
    "--disable-popup-blocking",
    "--start-maximized",
]

# ---------------------------------------------------------------------------
# HUMAN SIMULATION TIMING
# ---------------------------------------------------------------------------

# Per-keystroke delay range (milliseconds) for the typing simulation
TYPE_DELAY_MIN_MS: int = 50
TYPE_DELAY_MAX_MS: int = 150

# Sleep range (seconds) between navigation steps / button clicks
STEP_SLEEP_MIN: float = 0.5
STEP_SLEEP_MAX: float = 1.5

# ---------------------------------------------------------------------------
# FORM SELECTORS — fill in after inspecting the portal's HTML
# ---------------------------------------------------------------------------
# These are the CSS selectors (or XPath) for each input field on the booking
# form.  Open DevTools → Inspector on the Goethe portal and note the id/class
# of each field, then paste them here.

SELECTORS: dict[str, str] = {
    # Step 1 — search / calendar page
    "search_button":    "#REPLACE_search_button_selector",

    # Step 2 — slot selection (first available slot link or button)
    "first_slot":       "#REPLACE_first_available_slot_selector",

    # Step 3 — participant / contact form
    "first_name":       "#REPLACE_first_name_field_selector",
    "last_name":        "#REPLACE_last_name_field_selector",
    "passport":         "#REPLACE_passport_field_selector",
    "email":            "#REPLACE_email_field_selector",
    "phone":            "#REPLACE_phone_field_selector",

    # Step 4 — confirmation / submit
    "confirm_button":   "#REPLACE_confirm_button_selector",
    "submit_button":    "#REPLACE_submit_button_selector",
}

# ---------------------------------------------------------------------------
# NOTIFICATIONS (Telegram)
# ---------------------------------------------------------------------------

# Set these via environment variables or in your .env file:
#   TELEGRAM_BOT_TOKEN=123456:ABC-...
#   TELEGRAM_CHAT_ID=-100...
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------------------------------------------------------------------------
# CLIENT DATA
# ---------------------------------------------------------------------------

CLIENT_JSON_PATH: str = "client.json"
