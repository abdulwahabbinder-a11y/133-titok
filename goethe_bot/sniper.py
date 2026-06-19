"""
Playwright booking engine — launches a visible Chromium session with stealth patches.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from playwright_stealth import stealth_async

from goethe_bot.config import (
    CHROMIUM_LAUNCH_ARGS,
    CLIENT_JSON_PATH,
    FORM_SELECTORS,
    MACOS_CHROME_USER_AGENT,
    MACOS_VIEWPORT,
    REQUIRED_CLIENT_KEYS,
    SNIPER_BOOKING_URL,
    SNIPER_TIMEOUT_MS,
)
from goethe_bot.human_sim import human_click, human_type, random_step_delay
from goethe_bot.notifications import send_telegram_alert

logger = logging.getLogger(__name__)


class ClientDataError(ValueError):
    """Raised when client.json is missing or incomplete."""


def load_client_data(path: Path = CLIENT_JSON_PATH) -> dict[str, str]:
    """Read applicant data from the local client.json file."""
    if not path.exists():
        raise ClientDataError(f"client.json not found at {path.resolve()}")

    with path.open(encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)

    missing = [key for key in REQUIRED_CLIENT_KEYS if not data.get(key)]
    if missing:
        raise ClientDataError(f"client.json missing required keys: {missing}")

    return {key: str(data[key]).strip() for key in REQUIRED_CLIENT_KEYS}


class BookingSniper:
    """
    Async Playwright engine that completes the booking form once a slot is found.

    All form selectors live in config.FORM_SELECTORS — update them after inspecting
    the Goethe-Institut portal with browser DevTools.
    """

    def __init__(self, client_path: Path = CLIENT_JSON_PATH) -> None:
        self._client_path = client_path
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def execute(self) -> bool:
        """
        Launch Chromium (headless=False), apply stealth, and run the booking flow.

        Returns True if the flow completed without unhandled errors.
        The browser stays open on failure so you can intervene manually (captcha, etc.).
        """
        client = load_client_data(self._client_path)
        logger.info("Sniper launching for %s %s", client["first_name"], client["last_name"])

        playwright = await async_playwright().start()
        try:
            self._browser = await playwright.chromium.launch(
                headless=False,
                args=CHROMIUM_LAUNCH_ARGS,
            )
            self._context = await self._browser.new_context(
                viewport=MACOS_VIEWPORT,
                user_agent=MACOS_CHROME_USER_AGENT,
                locale="en-US",
                timezone_id="Europe/Berlin",
            )
            page = await self._context.new_page()
            page.set_default_timeout(SNIPER_TIMEOUT_MS)

            # playwright-stealth patches navigator.webdriver and related fingerprints
            await stealth_async(page)

            await self._run_booking_flow(page, client)
            await send_telegram_alert(
                "<b>Goethe Bot</b>\nBooking flow finished — verify confirmation in the browser."
            )
            return True

        except Exception:
            logger.exception("Sniper encountered an error — browser left open for manual intervention.")
            await send_telegram_alert(
                "<b>Goethe Bot — Error</b>\nSniper failed. Check the open browser window."
            )
            return False
        finally:
            # Intentionally do NOT close the browser on success/error so you can
            # complete captchas or confirm payment manually. Uncomment to auto-close:
            # if self._browser:
            #     await self._browser.close()
            # await playwright.stop()
            pass

    async def _run_booking_flow(self, page: Page, client: dict[str, str]) -> None:
        """
        Multi-step booking wizard.

        TODO: Adjust navigation steps to match your institute's actual flow.
        Each section below is marked where you must paste portal-specific selectors.
        """
        # --- STEP 1: Navigate to booking portal ---
        # TODO: Confirm SNIPER_BOOKING_URL in config.py points to the live portal.
        logger.info("Navigating to booking URL: %s", SNIPER_BOOKING_URL)
        await page.goto(SNIPER_BOOKING_URL, wait_until="domcontentloaded")
        await random_step_delay()

        # --- STEP 2: Select an available slot ---
        # TODO: Replace FORM_SELECTORS.slot_option with the CSS selector for a slot row/card.
        slot = page.locator(FORM_SELECTORS.slot_option).first
        if await slot.count() > 0:
            await human_click(page, FORM_SELECTORS.slot_option)
            logger.info("Slot selected.")
        else:
            logger.warning("No slot element matched %s — continue manually if needed.", FORM_SELECTORS.slot_option)

        # --- STEP 3: Fill personal details (human-typed, not instant fill) ---
        # TODO: Verify each selector in config.FormSelectors matches the live form.
        await human_type(page.locator(FORM_SELECTORS.first_name), client["first_name"])
        await random_step_delay()

        await human_type(page.locator(FORM_SELECTORS.last_name), client["last_name"])
        await random_step_delay()

        await human_type(page.locator(FORM_SELECTORS.passport), client["passport"])
        await random_step_delay()

        await human_type(page.locator(FORM_SELECTORS.email), client["email"])
        await random_step_delay()

        await human_type(page.locator(FORM_SELECTORS.phone), client["phone"])
        await random_step_delay()

        # --- STEP 4: Advance through wizard / submit ---
        # TODO: Add intermediate steps (exam level, location, payment) as extra clicks here.
        await human_click(page, FORM_SELECTORS.continue_button)
        await random_step_delay()

        # TODO: Final confirmation button — inspect portal for the exact selector.
        confirm = page.locator(FORM_SELECTORS.confirm_button)
        if await confirm.count() > 0:
            await human_click(page, FORM_SELECTORS.confirm_button)
            logger.info("Confirmation submitted.")
        else:
            logger.warning(
                "Confirm button %s not found — complete submission manually.",
                FORM_SELECTORS.confirm_button,
            )

        await page.wait_for_load_state("networkidle")
        logger.info("Booking flow reached final step. Verify success in the browser.")
