from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_MACOS_CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_1) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


@dataclass(slots=True)
class ClientProfile:
    first_name: str
    last_name: str
    passport: str
    email: str
    phone: str

    @classmethod
    def from_file(cls, path: Path) -> "ClientProfile":
        data = json.loads(path.read_text(encoding="utf-8"))
        required_keys = {"first_name", "last_name", "passport", "email", "phone"}
        missing = sorted(required_keys - data.keys())
        if missing:
            raise ValueError(f"Missing required client.json keys: {missing}")
        return cls(
            first_name=str(data["first_name"]).strip(),
            last_name=str(data["last_name"]).strip(),
            passport=str(data["passport"]).strip(),
            email=str(data["email"]).strip(),
            phone=str(data["phone"]).strip(),
        )


@dataclass(slots=True)
class ScanConfig:
    endpoint_url: str = "https://REPLACE_WITH_GOETHE_SCAN_ENDPOINT"
    method: str = "GET"
    payload: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(
        default_factory=lambda: {
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": DEFAULT_MACOS_CHROME_UA,
        }
    )
    unavailable_markers: list[str] = field(
        default_factory=lambda: ["no appointments available", "fully booked"]
    )
    available_markers: list[str] = field(
        default_factory=lambda: ["appointment available", "book now", "select slot"]
    )
    poll_interval_min_seconds: float = 15.0
    poll_interval_max_seconds: float = 30.0
    timeout_seconds: float = 15.0
    residential_proxies: list[str] = field(default_factory=list)
    error_backoff_cap_seconds: float = 120.0


@dataclass(slots=True)
class SniperConfig:
    booking_url: str = "https://REPLACE_WITH_GOETHE_BOOKING_PAGE"
    headless: bool = False
    viewport: dict[str, int] = field(
        default_factory=lambda: {"width": 1280, "height": 800}
    )
    user_agent: str = DEFAULT_MACOS_CHROME_UA
    launch_args: list[str] = field(default_factory=lambda: ["--start-maximized"])
    typing_delay_min_seconds: float = 0.05
    typing_delay_max_seconds: float = 0.15
    interaction_delay_min_seconds: float = 0.5
    interaction_delay_max_seconds: float = 1.5
    selectors: dict[str, str] = field(
        default_factory=lambda: {
            # Replace these with real selectors from the Goethe booking form.
            "start_booking_button": "REPLACE_START_BUTTON_SELECTOR",
            "first_name_input": "REPLACE_FIRST_NAME_SELECTOR",
            "last_name_input": "REPLACE_LAST_NAME_SELECTOR",
            "passport_input": "REPLACE_PASSPORT_SELECTOR",
            "email_input": "REPLACE_EMAIL_SELECTOR",
            "phone_input": "REPLACE_PHONE_SELECTOR",
            "next_step_button": "REPLACE_NEXT_STEP_SELECTOR",
            "submit_button": "REPLACE_FINAL_SUBMIT_SELECTOR",
        }
    )


@dataclass(slots=True)
class AlertConfig:
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None


@dataclass(slots=True)
class BotConfig:
    scan: ScanConfig = field(default_factory=ScanConfig)
    sniper: SniperConfig = field(default_factory=SniperConfig)
    alert: AlertConfig = field(default_factory=AlertConfig)
    client_file: Path = Path("client.json")

    @classmethod
    def from_file(cls, path: Path) -> "BotConfig":
        if not path.exists():
            return cls()

        data = json.loads(path.read_text(encoding="utf-8"))
        scan = ScanConfig(**data.get("scan", {}))
        sniper = SniperConfig(**data.get("sniper", {}))
        alert = AlertConfig(**data.get("alert", {}))
        client_file = Path(data.get("client_file", "client.json"))
        return cls(scan=scan, sniper=sniper, alert=alert, client_file=client_file)

