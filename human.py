"""
Human-behaviour simulation helpers for Playwright.

The Goethe portal (and the Cloudflare/Turnstile layer that protects it)
profiles mouse and keyboard cadence.  Any input that arrives faster than
~30 ms/char or in perfectly even intervals is flagged as automated.

Every helper here introduces small, *non-uniform* randomness:
    – per-keystroke delay  50 – 150 ms
    – inter-step delay     0.5 – 1.5 s
    – random pre-click hover with tiny mouse jitter
"""

from __future__ import annotations

import asyncio
import random
from typing import Optional

from playwright.async_api import Locator, Page


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
async def human_pause(min_s: float = 0.5, max_s: float = 1.5) -> None:
    """Sleep for a random duration to mimic 'thinking time' between actions."""
    await asyncio.sleep(random.uniform(min_s, max_s))


async def human_type(
    locator: Locator,
    text: str,
    *,
    min_delay_ms: int = 50,
    max_delay_ms: int = 150,
    clear_first: bool = True,
) -> None:
    """
    Type `text` into `locator` one character at a time with jittered delays.

    DO NOT replace this with `locator.fill(text)` – fill() sets `value`
    in a single synchronous JS call and is trivially detectable.
    """
    await locator.wait_for(state="visible", timeout=15_000)
    await locator.scroll_into_view_if_needed()
    await locator.click(delay=random.randint(30, 120))

    if clear_first:
        await locator.press("Control+A")
        await locator.press("Delete")

    for char in text:
        await locator.type(char, delay=random.randint(min_delay_ms, max_delay_ms))
        # occasional micro-pause as if the user hesitates between words
        if char == " " and random.random() < 0.2:
            await asyncio.sleep(random.uniform(0.15, 0.4))


async def human_click(
    page: Page,
    locator: Locator,
    *,
    pre_pause: bool = True,
    post_pause: bool = True,
) -> None:
    """Hover-then-click with a small mouse-move jitter."""
    if pre_pause:
        await human_pause(0.4, 1.2)

    await locator.wait_for(state="visible", timeout=15_000)
    await locator.scroll_into_view_if_needed()

    box = await locator.bounding_box()
    if box:
        target_x = box["x"] + box["width"] / 2 + random.uniform(-6, 6)
        target_y = box["y"] + box["height"] / 2 + random.uniform(-3, 3)
        await page.mouse.move(target_x, target_y, steps=random.randint(8, 20))

    await locator.click(delay=random.randint(40, 130))

    if post_pause:
        await human_pause(0.5, 1.4)


async def human_select(locator: Locator, value: str) -> None:
    """Select an <option> with a tiny realistic delay."""
    await locator.wait_for(state="visible", timeout=15_000)
    await asyncio.sleep(random.uniform(0.2, 0.6))
    await locator.select_option(value)
    await asyncio.sleep(random.uniform(0.3, 0.8))


def random_scan_interval(low: int, high: int) -> float:
    """Jittered scan cadence – avoids perfectly periodic polling patterns."""
    base = random.uniform(low, high)
    # 10 % chance to add a longer 'coffee break' pause
    if random.random() < 0.10:
        base += random.uniform(5, 12)
    return base


# --------------------------------------------------------------------------- #
# Macro helper
# --------------------------------------------------------------------------- #
async def fill_form_field(
    page: Page,
    selector: str,
    value: Optional[str],
    *,
    label: str = "",
) -> None:
    """
    High-level wrapper used by the Sniper.  Skips silently if value is empty,
    so optional fields don't crash the flow.
    """
    if not value:
        return
    locator = page.locator(selector).first
    await human_type(locator, value)
    if label:
        from loguru import logger

        logger.debug(f"  ✓ {label}: {value!r}")
