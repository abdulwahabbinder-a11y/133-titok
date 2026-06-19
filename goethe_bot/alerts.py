from __future__ import annotations

import logging

import httpx

from goethe_bot.config import AlertConfig

logger = logging.getLogger(__name__)


async def send_slot_alert(config: AlertConfig, message: str) -> None:
    """
    Telegram placeholder alert.
    Provide token/chat_id in bot_config.json to enable real notifications.
    """
    if not config.telegram_bot_token or not config.telegram_chat_id:
        logger.info("Alert placeholder: %s", message)
        return

    endpoint = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
    payload = {"chat_id": config.telegram_chat_id, "text": message}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
        logger.info("Telegram alert sent successfully.")
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send Telegram alert.")

