"""
Orchestrator -- wires the Scanner and Sniper together.

Flow
----
1. Load client data + configure logging.
2. Start the Scanner coroutine; it polls the target URL every 15-30 s.
3. As soon as the Scanner sets the `slot_open` event:
      a. Push a Telegram / macOS notification.
      b. Hand off to the Sniper, which performs the booking in Playwright.
4. After the Sniper finishes, optionally loop back to scanning (in case the
   first attempt didn't actually secure a slot -- the site sometimes shows
   ghost availability).

Usage
-----
    python main.py            # full pipeline
    python -m scanner         # scanner only
    python -m sniper          # sniper only (uses client.json)
    python -m notifier "hi"   # notification smoke-test
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

import config
import notifier
from scanner import run_scanner
from sniper import book_appointment

log = logging.getLogger("main")


async def pipeline(loop_forever: bool) -> None:
    client_data = config.load_client_data()
    log.info(
        "Loaded client data for %s %s",
        client_data["first_name"], client_data["last_name"],
    )

    attempt = 0
    while True:
        attempt += 1
        log.info("=== Attempt #%d ===", attempt)

        slot_open = asyncio.Event()
        await run_scanner(slot_open)

        if not slot_open.is_set():
            log.error("Scanner exited without setting the event. Aborting.")
            return

        await notifier.notify(
            f"Slot detected on {config.TARGET_URL}. Engaging Sniper."
        )

        booked = await book_appointment(client_data)

        if booked:
            await notifier.notify(
                "Goethe appointment looks BOOKED. Verify by email / portal."
            )
            return

        await notifier.notify(
            "Sniper finished without a confirmed booking. "
            + ("Re-arming Scanner." if loop_forever else "Stopping.")
        )

        if not loop_forever:
            return


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="goethe-sniper",
        description="Goethe-Institut appointment scanner + sniper.",
    )
    p.add_argument(
        "--once",
        action="store_true",
        help="Stop after the first Sniper attempt (default: keep retrying).",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help="Verbose logging.",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    config.configure_logging(logging.DEBUG if args.debug else logging.INFO)

    try:
        asyncio.run(pipeline(loop_forever=not args.once))
    except KeyboardInterrupt:
        log.info("Interrupted by user -- bye.")
        sys.exit(0)


if __name__ == "__main__":
    main()
