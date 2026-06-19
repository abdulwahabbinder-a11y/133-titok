"""
Lightweight alert system.

Currently ships a Telegram Bot API placeholder.  Replace `BOT_TOKEN` and
`CHAT_ID` in `.env` to receive pings; the function silently no-ops when
no credentials are configured so the bot keeps running unattended.
"""

from __future__ import annotations

import asyncio

import httpx
from loguru import logger

from config import settings


_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


async def send_alert(message: str) -> None:
    """Fire-and-forget notification."""
    logger.info(f"ALERT: {message}")

    tg = settings.telegram
    if not tg.enabled:
        logger.debug("Telegram disabled (no token/chat_id). Skipping push.")
        return

    url = _TELEGRAM_API.format(token=tg.token)
    payload = {
        "chat_id": tg.chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Telegram notification failed: {exc}")


def send_alert_sync(message: str) -> None:
    """Convenience wrapper for synchronous contexts."""
    try:
        asyncio.run(send_alert(message))
    except RuntimeError:
        # Already inside an event-loop – schedule instead.
        loop = asyncio.get_event_loop()
        loop.create_task(send_alert(message))
