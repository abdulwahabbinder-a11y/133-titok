from __future__ import annotations

import asyncio
import logging
import random
from typing import Iterable

from playwright.async_api import Page, async_playwright

from goethe_bot.config import ClientProfile, SniperConfig

logger = logging.getLogger(__name__)


class BookingSniper:
    def __init__(self, config: SniperConfig, client: ClientProfile) -> None:
        self.config = config
        self.client = client

    async def _human_pause(self) -> None:
        await asyncio.sleep(
            random.uniform(
                self.config.interaction_delay_min_seconds,
                self.config.interaction_delay_max_seconds,
            )
        )

    async def _human_type(self, page: Page, selector: str, value: str) -> None:
        locator = page.locator(selector)
        await locator.click()
        await locator.clear()
        for char in value:
            await locator.type(
                char,
                delay=random.uniform(
                    self.config.typing_delay_min_seconds * 1000,
                    self.config.typing_delay_max_seconds * 1000,
                ),
            )

    def _validate_selectors(self, keys: Iterable[str]) -> None:
        missing = [
            key
            for key in keys
            if not self.config.selectors.get(key)
            or self.config.selectors[key].startswith("REPLACE_")
        ]
        if missing:
            raise ValueError(
                "Update bot_config.json with real selectors before booking. "
                f"Missing/unconfigured selector keys: {missing}"
            )

    async def run(self) -> None:
        self._validate_selectors(
            [
                "start_booking_button",
                "first_name_input",
                "last_name_input",
                "passport_input",
                "email_input",
                "phone_input",
                "submit_button",
            ]
        )

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=self.config.headless,
                args=self.config.launch_args,
            )
            context = await browser.new_context(
                viewport=self.config.viewport,
                user_agent=self.config.user_agent,
                locale="en-US",
            )
            page = await context.new_page()

            try:
                # Insert your actual Goethe booking page URL in bot_config.json -> sniper.booking_url.
                await page.goto(self.config.booking_url, wait_until="domcontentloaded")
                await self._human_pause()

                # Selector placeholders must be replaced in bot_config.json.
                await page.locator(self.config.selectors["start_booking_button"]).click()
                await self._human_pause()

                await self._human_type(
                    page, self.config.selectors["first_name_input"], self.client.first_name
                )
                await self._human_pause()
                await self._human_type(
                    page, self.config.selectors["last_name_input"], self.client.last_name
                )
                await self._human_pause()

                if "next_step_button" in self.config.selectors and not self.config.selectors[
                    "next_step_button"
                ].startswith("REPLACE_"):
                    await page.locator(self.config.selectors["next_step_button"]).click()
                    await self._human_pause()

                await self._human_type(
                    page, self.config.selectors["passport_input"], self.client.passport
                )
                await self._human_pause()
                await self._human_type(
                    page, self.config.selectors["email_input"], self.client.email
                )
                await self._human_pause()
                await self._human_type(
                    page, self.config.selectors["phone_input"], self.client.phone
                )
                await self._human_pause()

                await page.locator(self.config.selectors["submit_button"]).click()
                logger.warning("Booking flow reached submit click. Check browser for confirmation.")

                # Keep browser open for emergency manual captcha/intervention handling.
                await page.wait_for_timeout(120000)

            except Exception:
                await page.screenshot(path="sniper_error.png", full_page=True)
                logger.exception("Sniper failed; screenshot captured at sniper_error.png")
                raise
            finally:
                await context.close()
                await browser.close()

