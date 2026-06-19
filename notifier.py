"""
Simple notification helpers.

Right now we ship a Telegram-Bot implementation. Plug other channels
(Discord, Slack, ntfy.sh, macOS `osascript`) into the same `notify()`
function if you want to fan-out alerts.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import sys
from typing import Optional

import httpx

import config

log = logging.getLogger("notifier")


async def _send_telegram(message: str) -> bool:
    """Fire-and-forget a Telegram message. Returns True on HTTP 200."""
    token = config.TELEGRAM_BOT_TOKEN
    chat  = config.TELEGRAM_CHAT_ID
    if not (token and chat):
        log.debug("Telegram credentials missing -- skipping push.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id":    chat,
        "text":       message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(url, data=payload)
            if r.status_code == 200:
                log.info("Telegram alert delivered.")
                return True
            log.warning("Telegram returned HTTP %s: %s", r.status_code, r.text[:200])
    except Exception as exc:                                      # noqa: BLE001
        log.warning("Telegram alert failed: %s", exc)
    return False


def _send_macos_banner(title: str, message: str) -> None:
    """Best-effort native macOS notification via `osascript`."""
    if sys.platform != "darwin":
        return
    try:
        subprocess.run(
            [
                "osascript",
                "-e",
                f'display notification "{message}" with title "{title}"',
            ],
            check=False,
            timeout=3,
        )
    except Exception:                                             # noqa: BLE001
        pass


async def notify(message: str, *, title: str = "Goethe Sniper") -> None:
    """Send the alert through every configured channel concurrently."""
    log.info("ALERT: %s", message)
    _send_macos_banner(title, message)
    await _send_telegram(f"<b>{title}</b>\n{message}")


# ---------------------------------------------------------------------------
# CLI smoke-test:   python -m notifier "hello world"
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    config.configure_logging()
    msg = " ".join(sys.argv[1:]) or "Test notification from Goethe Sniper"
    asyncio.run(notify(msg))
