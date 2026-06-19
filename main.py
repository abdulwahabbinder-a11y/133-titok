from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from goethe_bot.alerts import send_slot_alert
from goethe_bot.config import BotConfig, ClientProfile
from goethe_bot.scanner import AppointmentScanner
from goethe_bot.sniper import BookingSniper


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )


async def run_bot(config_file: Path) -> None:
    config = BotConfig.from_file(config_file)
    client = ClientProfile.from_file(config.client_file)
    scanner = AppointmentScanner(config.scan)
    sniper = BookingSniper(config.sniper, client)

    logging.info("Scanner started. Polling %s", config.scan.endpoint_url)

    while True:
        result = await scanner.wait_for_slot()
        if not result.slot_found:
            continue

        await send_slot_alert(
            config.alert,
            (
                "Potential Goethe slot detected.\n"
                f"Reason: {result.reason}\n"
                f"Status: {result.status_code}\n"
                f"Preview: {result.response_preview}"
            ),
        )

        try:
            await sniper.run()
            await send_slot_alert(config.alert, "Sniper workflow executed. Check the browser.")
            break
        except Exception:  # noqa: BLE001
            await send_slot_alert(
                config.alert,
                "Sniper execution failed. Scanner will continue in case more slots appear.",
            )
            await asyncio.sleep(3)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Goethe appointment scanner + booking sniper framework"
    )
    parser.add_argument(
        "--config",
        default="bot_config.json",
        help="Path to bot config file (default: bot_config.json)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    configure_logging(args.verbose)
    asyncio.run(run_bot(Path(args.config)))

