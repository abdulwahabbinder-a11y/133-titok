"""
main.py — Orchestrator for the Goethe-Institut appointment bot.

Startup sequence
────────────────
1. Validate the configuration (URL set, client.json readable).
2. Launch the Scanner in the background — it polls the booking page
   every 15–30 seconds using lightweight httpx requests.
3. Block until the Scanner signals that a slot is available.
4. Immediately hand off to the Sniper — a full Playwright session
   that fills the booking form with human-like timing.

Usage:
    python main.py

Requirements:
    pip install -r requirements.txt
    playwright install chromium
"""

import asyncio
import sys
from loguru import logger

import config
import notifier
from scanner import run_scanner
from sniper import run_sniper


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _configure_logging() -> None:
    logger.remove()     # Remove default handler

    # Console — colourised, concise
    logger.add(
        sys.stderr,
        level="DEBUG",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # Persistent log file — keeps full history
    logger.add(
        "bot.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} — {message}",
    )


# ---------------------------------------------------------------------------
# Pre-flight validation
# ---------------------------------------------------------------------------

def _validate_config() -> None:
    """
    Abort early with a clear error message if critical config values
    are still set to their placeholder values.
    """
    errors: list[str] = []

    if "REPLACE_WITH_GOETHE_BOOKING_URL" in config.TARGET_URL:
        errors.append(
            "config.TARGET_URL is still a placeholder. "
            "Set it to the actual Goethe-Institut booking page URL."
        )

    try:
        from sniper import load_client_data
        load_client_data()
    except FileNotFoundError as exc:
        errors.append(str(exc))
    except ValueError as exc:
        errors.append(str(exc))

    if errors:
        for err in errors:
            logger.error(f"Configuration error: {err}")
        logger.error(
            "Fix the errors above before running the bot. "
            "See config.py and client.json for instructions."
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main coroutine
# ---------------------------------------------------------------------------

async def main() -> None:
    _configure_logging()
    logger.info("=" * 60)
    logger.info("  Goethe-Institut Appointment Bot — starting up")
    logger.info("=" * 60)

    _validate_config()

    # Shared event: Scanner sets it, main() awaits it to start the Sniper.
    slot_found = asyncio.Event()

    # Run the scanner concurrently
    scanner_task = asyncio.create_task(
        run_scanner(slot_found),
        name="scanner",
    )

    logger.info("Scanner running in background. Waiting for an available slot …")

    try:
        # Block until the scanner finds a slot (or the scanner task crashes)
        done, pending = await asyncio.wait(
            {scanner_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Re-raise any exception from the scanner so it doesn't silently vanish
        for task in done:
            if task.exception():
                raise task.exception()

    except asyncio.CancelledError:
        logger.warning("Main task cancelled — shutting down.")
        scanner_task.cancel()
        return

    if not slot_found.is_set():
        # Scanner exited without finding a slot (unexpected)
        logger.error("Scanner exited without detecting a slot. Check logs for errors.")
        return

    logger.info("Slot signal received! Launching the Sniper …")
    await run_sniper()

    logger.info("Bot run complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user — exiting cleanly.")
