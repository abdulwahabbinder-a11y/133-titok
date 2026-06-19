"""
Central configuration loader.

Values are pulled from environment variables (or a local `.env` file).
Override any of the defaults by editing `.env`  – never commit secrets.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


# --------------------------------------------------------------------------- #
# Dataclasses
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ProxyConfig:
    """Rotating residential proxy settings (placeholder)."""

    url: str = field(default_factory=lambda: _env("PROXY_URL"))
    username: str = field(default_factory=lambda: _env("PROXY_USERNAME"))
    password: str = field(default_factory=lambda: _env("PROXY_PASSWORD"))
    host: str = field(default_factory=lambda: _env("PROXY_HOST"))
    port: str = field(default_factory=lambda: _env("PROXY_PORT"))

    @property
    def enabled(self) -> bool:
        return bool(self.url) or bool(self.host and self.port)

    def as_httpx(self) -> Optional[str]:
        """
        Return a proxy URL suitable for `httpx.AsyncClient(proxy=...)`.

        Most residential providers (BrightData, Oxylabs, IPRoyal, Smartproxy)
        rotate the exit IP automatically on every TCP connection when you hit
        their gateway endpoint, so we simply hand the gateway URL back.
        """
        if self.url:
            return self.url
        if self.host and self.port:
            auth = (
                f"{self.username}:{self.password}@"
                if self.username and self.password
                else ""
            )
            return f"http://{auth}{self.host}:{self.port}"
        return None

    def as_playwright(self) -> Optional[dict]:
        """Return a dict shaped for `browser.new_context(proxy=...)`."""
        if not self.enabled:
            return None
        server = self.url or f"http://{self.host}:{self.port}"
        cfg: dict = {"server": server}
        if self.username:
            cfg["username"] = self.username
        if self.password:
            cfg["password"] = self.password
        return cfg


@dataclass(frozen=True)
class TelegramConfig:
    token: str = field(default_factory=lambda: _env("TELEGRAM_BOT_TOKEN"))
    chat_id: str = field(default_factory=lambda: _env("TELEGRAM_CHAT_ID"))

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat_id)


@dataclass(frozen=True)
class AppConfig:
    target_url: str = field(default_factory=lambda: _env("TARGET_URL"))
    scan_interval_min: int = field(default_factory=lambda: _int("SCAN_INTERVAL_MIN", 15))
    scan_interval_max: int = field(default_factory=lambda: _int("SCAN_INTERVAL_MAX", 30))
    negative_marker: str = field(
        default_factory=lambda: _env("NEGATIVE_MARKER", "Keine Buchung möglich")
    )
    positive_marker: str = field(
        default_factory=lambda: _env("POSITIVE_MARKER", "Anmelden")
    )
    client_file: str = field(default_factory=lambda: _env("CLIENT_FILE", "client.json"))

    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)

    def load_client(self) -> dict:
        path = Path(self.client_file)
        if not path.exists():
            raise FileNotFoundError(
                f"Client data file '{path}' not found. "
                "Copy `client.example.json` to `client.json` and fill it in."
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        required = {"first_name", "last_name", "passport", "email", "phone"}
        missing = required - data.keys()
        if missing:
            raise ValueError(f"client.json missing required keys: {missing}")
        return data


# Singleton-style export
settings = AppConfig()
