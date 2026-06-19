"""
THE SNIPER – Playwright booking engine.

Launches a non-headless Chromium with stealth patches applied so that
`navigator.webdriver`, plugin enumeration, WebGL vendor strings, etc.
look like a real macOS Chrome session.  Falls through the booking form
using human-cadence typing and clicks.

The selector strings inside `book()` are intentionally placeholders
(marked `>>> CUSTOMISE ME <<<`).  Inspect the live Goethe-Institut
form in DevTools and drop in the actual IDs / data-test attributes.
"""

from __future__ import annotations

import asyncio
import random
from typing import Optional

from loguru import logger
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

try:
    # playwright-stealth ≥ 1.0.6
    from playwright_stealth import stealth_async
except ImportError:  # pragma: no cover
    stealth_async = None  # type: ignore[assignment]
    logger.warning(
        "playwright-stealth is not installed. "
        "Run `pip install playwright-stealth` for full fingerprint masking."
    )

from config import settings
from human import fill_form_field, human_click, human_pause, human_type
from notifier import send_alert


# --------------------------------------------------------------------------- #
# macOS-specific browser profile
# --------------------------------------------------------------------------- #
MAC_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

VIEWPORT = {"width": 1280, "height": 800}

CHROMIUM_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-site-isolation-trials",
    "--no-default-browser-check",
    "--no-first-run",
    "--start-maximized",
]


# --------------------------------------------------------------------------- #
class Sniper:
    def __init__(self, client_data: dict) -> None:
        self.client = client_data

    # ------------------------------------------------------------------ #
    async def _launch(self, pw: Playwright) -> tuple[Browser, BrowserContext, Page]:
        proxy_cfg = settings.proxy.as_playwright()

        browser = await pw.chromium.launch(
            headless=False,                    # keep visible for manual rescue
            args=CHROMIUM_ARGS,
            proxy=proxy_cfg,
            slow_mo=0,
        )

        context = await browser.new_context(
            user_agent=MAC_USER_AGENT,
            viewport=VIEWPORT,
            locale="de-DE",
            timezone_id="Europe/Berlin",
            color_scheme="light",
            device_scale_factor=2,             # Retina
            is_mobile=False,
            has_touch=False,
            java_script_enabled=True,
            extra_http_headers={
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            },
        )

        # Belt-and-braces: blank out navigator.webdriver even if
        # playwright-stealth is missing.
        await context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = window.chrome || { runtime: {} };
            Object.defineProperty(navigator, 'languages',
                {get: () => ['de-DE', 'de', 'en-US', 'en']});
            Object.defineProperty(navigator, 'plugins',
                {get: () => [1, 2, 3, 4, 5]});
            """
        )

        page = await context.new_page()

        if stealth_async is not None:
            await stealth_async(page)

        return browser, context, page

    # ------------------------------------------------------------------ #
    async def book(self) -> bool:
        """
        Execute the booking flow.  Returns True on success.

        NOTE:  All selectors below are PLACEHOLDERS.  Open the Goethe form
        in your browser, inspect each control, and replace the strings
        marked  >>> CUSTOMISE ME <<<.
        """
        logger.info("Sniper launching Chromium…")
        async with async_playwright() as pw:
            browser, context, page = await self._launch(pw)
            try:
                # ---------------------------------------------------------- #
                # 1. Navigate to the booking page
                # ---------------------------------------------------------- #
                await page.goto(settings.target_url, wait_until="domcontentloaded")
                await human_pause(1.0, 2.0)
                await send_alert("Sniper opened booking page. Standing by.")

                # ---------------------------------------------------------- #
                # 2. Pick the first available slot
                #    >>> CUSTOMISE ME <<<
                #    Example placeholder: each slot rendered as
                #        <a class="slot" data-status="free" href="…">10:30</a>
                # ---------------------------------------------------------- #
                slot_selector = "a.slot[data-status='free']"
                try:
                    slot = page.locator(slot_selector).first
                    await slot.wait_for(state="visible", timeout=10_000)
                    await human_click(page, slot)
                except Exception:
                    logger.warning(
                        "No slot element matched – the markup may have "
                        "changed. Switch to manual mode in the open window."
                    )
                    # Keep the browser open so the user can finish manually.
                    await human_pause(5, 8)

                # ---------------------------------------------------------- #
                # 3. Fill personal data
                #    >>> CUSTOMISE ME <<<  – replace each selector.
                # ---------------------------------------------------------- #
                logger.info("Filling personal data…")
                await fill_form_field(
                    page, "input#firstName", self.client["first_name"],
                    label="first_name",
                )
                await human_pause(0.4, 1.0)

                await fill_form_field(
                    page, "input#lastName", self.client["last_name"],
                    label="last_name",
                )
                await human_pause(0.4, 1.0)

                await fill_form_field(
                    page, "input#passport", self.client["passport"],
                    label="passport",
                )
                await human_pause(0.4, 1.0)

                await fill_form_field(
                    page, "input#email", self.client["email"],
                    label="email",
                )
                await human_pause(0.4, 1.0)

                await fill_form_field(
                    page, "input#phone", self.client["phone"],
                    label="phone",
                )
                await human_pause(0.6, 1.5)

                # ---------------------------------------------------------- #
                # 4. Accept Terms & Conditions
                #    >>> CUSTOMISE ME <<<
                # ---------------------------------------------------------- #
                try:
                    tos = page.locator("input[type='checkbox']#agb").first
                    await human_click(page, tos)
                except Exception:
                    logger.debug("No T&C checkbox found – skipping.")

                # ---------------------------------------------------------- #
                # 5. Submit
                #    >>> CUSTOMISE ME <<<
                # ---------------------------------------------------------- #
                submit = page.locator("button[type='submit']").first
                await human_click(page, submit)

                # ---------------------------------------------------------- #
                # 6. Confirmation
                # ---------------------------------------------------------- #
                try:
                    await page.wait_for_selector(
                        "text=/Buchungsbestätigung|Bestätigung|Vielen Dank/i",
                        timeout=30_000,
                    )
                    logger.success("✅ Booking confirmed.")
                    await send_alert(
                        f"✅ <b>Goethe slot booked</b> for "
                        f"{self.client['first_name']} {self.client['last_name']}!"
                    )
                    success = True
                except Exception:
                    logger.warning(
                        "No confirmation text detected within 30 s. "
                        "Inspect the open window and complete manually."
                    )
                    await send_alert(
                        "⚠️ Sniper finished the form but confirmation was "
                        "not detected – manual review required."
                    )
                    success = False

                # Keep the window open for inspection / manual takeover.
                logger.info("Browser will remain open for 5 minutes…")
                await asyncio.sleep(300)
                return success

            finally:
                await context.close()
                await browser.close()
