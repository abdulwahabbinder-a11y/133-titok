"""
Human-like interaction helpers for Playwright form filling.
"""

from __future__ import annotations

import asyncio
import random

from playwright.async_api import Locator, Page

from goethe_bot.config import (
    KEYSTROKE_DELAY_MAX_MS,
    KEYSTROKE_DELAY_MIN_MS,
    STEP_DELAY_MAX_SEC,
    STEP_DELAY_MIN_SEC,
)


async def random_step_delay() -> None:
    """Pause between navigation steps or button clicks (0.5–1.5 s)."""
    delay = random.uniform(STEP_DELAY_MIN_SEC, STEP_DELAY_MAX_SEC)
    await asyncio.sleep(delay)


async def human_type(locator: Locator, text: str) -> None:
    """
    Type text character-by-character with random inter-key delays (50–150 ms).

    Avoids instant `.fill()` on critical fields, which many anti-bot systems flag.
    """
    await locator.click()
    await locator.fill("")  # clear any prefilled value without simulating paste

    for char in text:
        await locator.press_sequentially(char, delay=0)
        delay_ms = random.randint(KEYSTROKE_DELAY_MIN_MS, KEYSTROKE_DELAY_MAX_MS)
        await asyncio.sleep(delay_ms / 1000.0)


async def human_click(page: Page, selector: str) -> None:
    """Click an element after a natural pause."""
    await random_step_delay()
    await page.locator(selector).click()
