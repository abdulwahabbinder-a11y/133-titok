"""
Central configuration for the Goethe-Institut appointment sniper.

All tunables (URLs, selectors, intervals, proxy pool, secrets) live here so
that the Scanner and Sniper modules stay focused on logic.

Anything that must be edited *once you have inspected the real Goethe portal*
is clearly marked with `# TODO:` markers.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Scanner / Sniper tuning
# ---------------------------------------------------------------------------

# Polling interval (seconds). A random value in this range is picked between
# every scan to look more human and avoid an obvious 1/min signature.
SCAN_INTERVAL_MIN: float = 15.0
SCAN_INTERVAL_MAX: float = 30.0

# How long the Scanner waits for an HTTP response before retrying.
SCAN_TIMEOUT: float = 12.0

# Human-typing delay (milliseconds). Each keystroke gets a random value in
# this range. Anything below ~40ms starts to look mechanical.
TYPING_DELAY_MIN_MS: int = 50
TYPING_DELAY_MAX_MS: int = 150

# Sleep (seconds) injected between high-level UI steps (click, navigate, ...).
STEP_PAUSE_MIN_S: float = 0.5
STEP_PAUSE_MAX_S: float = 1.5


# ---------------------------------------------------------------------------
# Target site -- EDIT after inspecting the real Goethe portal
# ---------------------------------------------------------------------------

# TODO: paste the precise URL of the appointment listing page (or the JSON
#       endpoint the front-end calls) once you've inspected the site.
TARGET_URL: str = os.getenv(
    "GOETHE_TARGET_URL",
    "https://www.goethe.de/ins/xx/xx/spr/prf/REPLACE_ME.html",
)

# TODO: these strings are what the Scanner *looks for* in the response body
#       to decide whether slots are open. Adjust them to match the real wording
#       used by the Goethe portal in your language.
SOLD_OUT_MARKERS: List[str] = [
    "Keine Termine verfügbar",      # de
    "No appointments available",    # en
    "Aucun rendez-vous disponible", # fr
]

# Optional: positive markers. If any of these appear, we assume slots are open
# even if the SOLD_OUT_MARKERS still happen to appear elsewhere on the page.
AVAILABLE_MARKERS: List[str] = [
    "Jetzt anmelden",   # "Register now"
    "Book now",
    "Anmelden",
]

# TODO: form-field selectors. Inspect the booking form in DevTools and fill in.
#       Prefer stable IDs over class names. Use CSS selectors.
SELECTORS = {
    # the appointment row / "book" button on the listing page
    "appointment_book_button": "button[data-test='book-appointment']",   # TODO

    # personal-data form
    "first_name":  "input#firstName",       # TODO
    "last_name":   "input#lastName",        # TODO
    "passport":    "input#passportNumber",  # TODO
    "email":       "input#email",           # TODO
    "phone":       "input#phone",           # TODO

    # terms checkbox + final submit
    "tos_checkbox":  "input#acceptTerms",   # TODO
    "submit_button": "button#submit",       # TODO
}


# ---------------------------------------------------------------------------
# Browser fingerprint (macOS Chrome)
# ---------------------------------------------------------------------------

VIEWPORT = {"width": 1280, "height": 800}

# Clean macOS Chrome user-agent. Update the Chrome major version periodically
# so it matches a *current* release of Chrome on macOS.
USER_AGENT: str = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/127.0.0.0 Safari/537.36"
)

LOCALE: str = "de-DE"
TIMEZONE: str = "Europe/Berlin"

# Chromium launch flags that hide automation traces.
CHROMIUM_ARGS: List[str] = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--no-default-browser-check",
    "--no-first-run",
    "--start-maximized",
]


# ---------------------------------------------------------------------------
# Proxy rotation
# ---------------------------------------------------------------------------

@dataclass
class ProxyConfig:
    """Rotating residential proxy configuration.

    Two modes are supported:

    1.  A single *rotating gateway* (e.g. BrightData / Oxylabs / Smartproxy
        gateways that already rotate IPs per request). Set `gateway`.

    2.  A list of individual proxies that we cycle through manually. Set
        `pool` to something like ``["http://user:pass@host:port", ...]``.
    """

    gateway: Optional[str] = None
    pool: List[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "ProxyConfig":
        gateway = os.getenv("PROXY_GATEWAY") or None
        raw_list = os.getenv("PROXY_LIST", "")
        pool = [p.strip() for p in raw_list.split(",") if p.strip()]
        return cls(gateway=gateway, pool=pool)

    @property
    def enabled(self) -> bool:
        return bool(self.gateway or self.pool)


PROXY = ProxyConfig.from_env()


# ---------------------------------------------------------------------------
# Telegram alerts
# ---------------------------------------------------------------------------

TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN") or None
TELEGRAM_CHAT_ID:   Optional[str] = os.getenv("TELEGRAM_CHAT_ID") or None


# ---------------------------------------------------------------------------
# Client data
# ---------------------------------------------------------------------------

CLIENT_FILE: Path = ROOT_DIR / "client.json"


def load_client_data(path: Path = CLIENT_FILE) -> dict:
    """Load and validate `client.json`.

    Raises FileNotFoundError or ValueError with a helpful message if the
    file is missing keys.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Client data file not found: {path}. "
            "Copy `client.example.json` to `client.json` and fill it in."
        )

    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    required = {"first_name", "last_name", "passport", "email", "phone"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"client.json is missing required keys: {sorted(missing)}")
    return data


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging with colour output when available."""
    try:
        import colorlog

        handler = colorlog.StreamHandler()
        handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%H:%M:%S",
                log_colors={
                    "DEBUG":    "cyan",
                    "INFO":     "white",
                    "WARNING":  "yellow",
                    "ERROR":    "red",
                    "CRITICAL": "bold_red",
                },
            )
        )
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)
        root.setLevel(level)
    except ImportError:
        logging.basicConfig(
            level=level,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
