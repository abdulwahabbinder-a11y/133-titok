"""
Alert placeholders — extend with Telegram, email, Pushover, etc.
"""

from __future__ import annotations

import logging

import httpx

from goethe_bot.config import TELEGRAM

logger = logging.getLogger(__name__)


async def send_telegram_alert(message: str) -> bool:
    """
    Fire a Telegram Bot API ping when a slot is detected.

    Setup:
      1. Create a bot via @BotFather and copy the token.
      2. Send any message to your bot, then visit:
         https://api.telegram.org/bot<TOKEN>/getUpdates to find your chat_id.
      3. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars, or edit config.py.
      4. Set TELEGRAM.enabled = True.
    """
    if not TELEGRAM.enabled:
        logger.info("Telegram alerts disabled — would have sent: %s", message)
        return False

    if "REPLACE" in TELEGRAM.bot_token or "REPLACE" in TELEGRAM.chat_id:
        logger.warning("Telegram credentials are still placeholders; alert skipped.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM.bot_token}/sendMessage"
    payload = {"chat_id": TELEGRAM.chat_id, "text": message, "parse_mode": "HTML"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        logger.info("Telegram alert delivered.")
        return True
    except httpx.HTTPError as exc:
        logger.error("Telegram alert failed: %s", exc)
        return False


async def notify_slot_found(detail: str = "") -> None:
    """Central hook invoked by the scanner when availability is detected."""
    message = (
        "<b>Goethe Bot — Slot Detected</b>\n"
        "An appointment may be available. Sniper is launching now.\n"
    )
    if detail:
        message += f"\n<i>{detail}</i>"
    await send_telegram_alert(message)
