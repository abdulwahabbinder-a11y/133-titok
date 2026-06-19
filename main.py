"""
Orchestrator – wires the Scanner and the Sniper together.

Run:
    python main.py

Stop with Ctrl-C.  The Scanner polls continuously; the Sniper fires once
a slot is detected, then the script exits (or re-arms if the booking
fails — see RETRY_ON_FAILURE below).
"""

from __future__ import annotations

import asyncio
import signal
import sys

from loguru import logger

from config import settings
from notifier import send_alert
from scanner import Scanner
from sniper import Sniper


RETRY_ON_FAILURE = True   # set to False to exit after one booking attempt


# --------------------------------------------------------------------------- #
def _configure_logging() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan> - <level>{message}</level>",
    )
    logger.add(
        "goethe_sniper.log",
        level="DEBUG",
        rotation="10 MB",
        retention=5,
        enqueue=True,
    )


# --------------------------------------------------------------------------- #
async def _run_once(client_data: dict) -> bool:
    slot_event = asyncio.Event()
    scanner = Scanner(slot_event)

    scanner_task = asyncio.create_task(scanner.run(), name="scanner")
    try:
        await slot_event.wait()
    finally:
        scanner_task.cancel()
        try:
            await scanner_task
        except (asyncio.CancelledError, Exception):
            pass

    await send_alert("🚨 Goethe slot detected – Sniper engaging!")
    sniper = Sniper(client_data)
    return await sniper.book()


async def main() -> None:
    _configure_logging()
    logger.info("=== Goethe-Institut Appointment Sniper ===")

    if not settings.target_url or "CHANGE-ME" in settings.target_url:
        logger.error(
            "TARGET_URL is not configured. Edit `.env` and set the real "
            "Goethe-Institut booking page URL before launching."
        )
        sys.exit(2)

    try:
        client_data = settings.load_client()
    except (FileNotFoundError, ValueError) as exc:
        logger.error(str(exc))
        sys.exit(2)

    logger.info(
        f"Loaded client: {client_data['first_name']} "
        f"{client_data['last_name']} ({client_data['email']})"
    )

    # Graceful shutdown on SIGINT / SIGTERM
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            # Windows fallback – Ctrl-C still raises KeyboardInterrupt.
            pass

    while not stop_event.is_set():
        try:
            success = await _run_once(client_data)
            if success or not RETRY_ON_FAILURE:
                logger.info("Done. Exiting.")
                return
            logger.warning("Booking did not succeed. Re-arming Scanner…")
        except asyncio.CancelledError:
            break
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"Unhandled error in main loop: {exc}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user – bye.")
