"""
notifier.py — Alert system for the Goethe-Institut appointment bot.

Currently implements:
  • Telegram Bot API push notification
  • Console / log fallback (always active)

To extend with additional channels (Email, WhatsApp, etc.) add a new
async function following the same signature and call it from notify().
"""

import asyncio
import httpx
from loguru import logger

import config


async def _send_telegram(message: str) -> None:
    """
    Send a Telegram message via the Bot API.

    Prerequisites:
      1. Create a bot with @BotFather and copy the token.
      2. Get your chat / channel ID (use @userinfobot or the getUpdates API).
      3. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your .env file.
    """
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.warning(
            "Telegram credentials not configured — skipping Telegram alert. "
            "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your .env file."
        )
        return

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info("Telegram alert sent successfully.")
    except httpx.HTTPStatusError as exc:
        logger.error(f"Telegram API error {exc.response.status_code}: {exc.response.text}")
    except Exception as exc:
        logger.error(f"Failed to send Telegram alert: {exc}")


# ---------------------------------------------------------------------------
# PLACEHOLDER: add more channels here
# ---------------------------------------------------------------------------

async def _send_email(message: str) -> None:
    """
    PLACEHOLDER — Email notification via SMTP or a transactional API (e.g. SendGrid).
    Implement and wire into notify() when needed.
    """
    # TODO: implement with aiosmtplib or httpx + SendGrid API
    logger.debug("Email notifier placeholder called (not implemented).")


async def _send_whatsapp(message: str) -> None:
    """
    PLACEHOLDER — WhatsApp notification via Twilio or the WhatsApp Business API.
    """
    # TODO: implement with Twilio's async client
    logger.debug("WhatsApp notifier placeholder called (not implemented).")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def notify(message: str) -> None:
    """
    Fire all configured notification channels concurrently.
    Always logs to console regardless of other channel availability.
    """
    logger.success(f"[ALERT] {message}")

    # Run all channel coroutines in parallel so one slow channel
    # does not delay the others.
    await asyncio.gather(
        _send_telegram(message),
        # _send_email(message),      # uncomment when implemented
        # _send_whatsapp(message),   # uncomment when implemented
        return_exceptions=True,
    )
