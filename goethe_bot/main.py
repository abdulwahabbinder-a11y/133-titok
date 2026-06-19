#!/usr/bin/env python3
"""
Goethe-Institut Appointment Bot — entry point.

Runs the lightweight HTTP scanner and triggers the Playwright sniper on detection.

Usage:
    python -m goethe_bot.main

Prerequisites:
    pip install -r requirements.txt
    playwright install chromium
    cp client.json.example client.json   # then fill in your details
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from goethe_bot.config import LOG_LEVEL, STOP_SCANNER_AFTER_TRIGGER
from goethe_bot.notifications import notify_slot_found
from goethe_bot.scanner import AvailabilityScanner
from goethe_bot.sniper import BookingSniper

logger = logging.getLogger("goethe_bot")


class GoetheBot:
    """Orchestrates scanner → alert → sniper with a single-fire lock."""

    def __init__(self) -> None:
        self._sniper_lock = asyncio.Lock()
        self._sniper_started = False
        self._scanner = AvailabilityScanner(on_slot_found=self._handle_slot_found)
        self._sniper = BookingSniper()

    async def _handle_slot_found(self, reason: str) -> None:
        """Callback invoked by the scanner when availability changes."""
        if self._sniper_started:
            return

        async with self._sniper_lock:
            if self._sniper_started:
                return
            self._sniper_started = True

        await notify_slot_found(detail=reason)

        if STOP_SCANNER_AFTER_TRIGGER:
            self._scanner.stop()

        # Fire sniper without blocking the scanner shutdown coroutine
        asyncio.create_task(self._run_sniper())

    async def _run_sniper(self) -> None:
        logger.info("Handing off to Playwright sniper...")
        success = await self._sniper.execute()
        if success:
            logger.info("Sniper completed.")
        else:
            logger.error("Sniper finished with errors — check the browser window.")

    async def run(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._scanner.stop)

        await self._scanner.run()


def _configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> int:
    _configure_logging()
    logger.info("Goethe appointment bot starting.")

    try:
        asyncio.run(GoetheBot().run())
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
