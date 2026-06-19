"""
Sniper -- Playwright (async) booking engine.

Stealth checklist (matches Goethe / Cloudflare / Turnstile defences):
* `headless=False`             -- real GUI, so you can intervene on captchas.
* `--disable-blink-features=AutomationControlled` launch flag.
* `playwright-stealth` patches navigator.webdriver, chrome.runtime, plugins,
  WebGL vendor, permission queries, ...
* macOS Chrome user-agent + 1280x800 viewport + Europe/Berlin timezone.
* Human typing (50-150 ms per keystroke) and randomised step pauses.

Once a slot is detected, the orchestrator calls `book_appointment()` exactly
once. The function returns True on success and False on any failure so the
orchestrator can decide whether to keep scanning.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

import config

log = logging.getLogger("sniper")


# ---------------------------------------------------------------------------
# Human-simulation helpers
# ---------------------------------------------------------------------------

async def human_pause(min_s: Optional[float] = None,
                      max_s: Optional[float] = None) -> None:
    """Random delay between high-level UI actions to mimic a human."""
    lo = config.STEP_PAUSE_MIN_S if min_s is None else min_s
    hi = config.STEP_PAUSE_MAX_S if max_s is None else max_s
    await asyncio.sleep(random.uniform(lo, hi))


async def human_type(locator: Locator, text: str) -> None:
    """Type into a field one character at a time with a randomised delay.

    Why not `locator.fill()`? -- `fill()` sets `.value` in one shot which
    leaves a strong "automation" signature (no individual keydown events,
    no inter-keystroke timing). We dispatch a real `press()` per character
    with a small random sleep instead.
    """
    await locator.click()
    await human_pause(0.1, 0.3)

    # Ensure the field is empty before typing.
    try:
        await locator.fill("")
    except Exception:                                            # noqa: BLE001
        pass

    for char in text:
        delay_ms = random.randint(
            config.TYPING_DELAY_MIN_MS, config.TYPING_DELAY_MAX_MS
        )
        # `Locator.type` honours `delay=` per keystroke, but we still loop
        # so that *each* keystroke gets its own random delay (instead of a
        # single delay applied between every char).
        await locator.type(char, delay=delay_ms)


# ---------------------------------------------------------------------------
# Stealth glue (works with both `playwright-stealth` and `tf-playwright-stealth`)
# ---------------------------------------------------------------------------

async def _apply_stealth(page: Page) -> None:
    """Best-effort stealth patching.

    The package name and entry-point changed over time. We try the newest
    API first and gracefully fall back. The `init_script` below also makes
    sure `navigator.webdriver` is wiped even if the stealth lib is missing.
    """
    patched = False
    try:
        # tf-playwright-stealth >= 1.1
        from playwright_stealth import Stealth          # type: ignore

        await Stealth().apply_stealth_async(page)
        patched = True
    except Exception:                                            # noqa: BLE001
        pass

    if not patched:
        try:
            # legacy `playwright-stealth`
            from playwright_stealth import stealth_async  # type: ignore

            await stealth_async(page)
            patched = True
        except Exception:                                        # noqa: BLE001
            pass

    if not patched:
        log.warning(
            "playwright-stealth not available -- falling back to manual patch."
        )

    # Always layer a manual scrub on top. Belt + braces.
    await page.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages',
                              { get: () => ['de-DE', 'de', 'en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins',
                              { get: () => [1, 2, 3, 4, 5] });
        window.chrome = window.chrome || { runtime: {} };
        const origQuery = window.navigator.permissions
            && window.navigator.permissions.query;
        if (origQuery) {
            window.navigator.permissions.query = (p) =>
                p && p.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : origQuery(p);
        }
        """
    )


# ---------------------------------------------------------------------------
# Browser bootstrap
# ---------------------------------------------------------------------------

async def _launch_browser(pw) -> tuple[Browser, BrowserContext, Page]:
    browser = await pw.chromium.launch(
        headless=False,
        args=config.CHROMIUM_ARGS,
    )

    context = await browser.new_context(
        viewport=config.VIEWPORT,
        user_agent=config.USER_AGENT,
        locale=config.LOCALE,
        timezone_id=config.TIMEZONE,
        java_script_enabled=True,
        is_mobile=False,
        device_scale_factor=2,                # retina-like, matches macOS
        color_scheme="light",
    )

    # remove the automation banner that Chrome shows at the top
    await context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )

    page = await context.new_page()
    await _apply_stealth(page)
    return browser, context, page


# ---------------------------------------------------------------------------
# The actual booking flow
# ---------------------------------------------------------------------------

async def book_appointment(client_data: dict) -> bool:
    """Run the entire booking flow end-to-end.

    The function is intentionally linear and *very* commented so you can
    drop in the real selectors / extra steps once you've inspected the
    portal in DevTools.
    """
    log.info("Sniper firing -- launching Chromium.")

    async with async_playwright() as pw:
        browser, context, page = await _launch_browser(pw)

        try:
            # ------------------------------------------------------------ 1
            # Navigate to the appointment listing page.
            #
            # TODO: if the booking flow starts at a different URL than the
            #       page the Scanner monitors, change this.
            # ------------------------------------------------------------
            log.info("Navigating to %s", config.TARGET_URL)
            await page.goto(config.TARGET_URL, wait_until="domcontentloaded")
            await human_pause()

            # ------------------------------------------------------------ 2
            # Click the "book this slot" button.
            #
            # TODO: if there are several offered slots and you want the
            #       *first* / *cheapest* / *specific date*, change this
            #       locator to pick the right row.
            # ------------------------------------------------------------
            book_btn = page.locator(config.SELECTORS["appointment_book_button"])
            await book_btn.first.wait_for(state="visible", timeout=15_000)
            await human_pause()
            await book_btn.first.click()
            log.info("Clicked the 'book appointment' button.")

            # ------------------------------------------------------------ 3
            # Fill out personal data.
            #
            # TODO: if the form is split across multiple pages, add an
            #       extra `await page.wait_for_url(...)` / click "Next"
            #       between blocks.
            # ------------------------------------------------------------
            await human_pause()
            await human_type(
                page.locator(config.SELECTORS["first_name"]),
                client_data["first_name"],
            )
            await human_pause(0.2, 0.6)
            await human_type(
                page.locator(config.SELECTORS["last_name"]),
                client_data["last_name"],
            )
            await human_pause(0.2, 0.6)
            await human_type(
                page.locator(config.SELECTORS["passport"]),
                client_data["passport"],
            )
            await human_pause(0.2, 0.6)
            await human_type(
                page.locator(config.SELECTORS["email"]),
                client_data["email"],
            )
            await human_pause(0.2, 0.6)
            await human_type(
                page.locator(config.SELECTORS["phone"]),
                client_data["phone"],
            )

            # ------------------------------------------------------------ 4
            # Terms-of-service checkbox.
            # ------------------------------------------------------------
            await human_pause()
            tos = page.locator(config.SELECTORS["tos_checkbox"])
            if await tos.count():
                await tos.first.check()
                log.info("Accepted ToS.")

            # ------------------------------------------------------------ 5
            # Captcha checkpoint.
            #
            # We launched non-headless precisely so YOU can solve a
            # Cloudflare Turnstile / hCaptcha if it shows up. We just give
            # you a generous window before pressing submit.
            #
            # TODO: tune this depending on whether the site shows a captcha
            #       on the final step or earlier.
            # ------------------------------------------------------------
            log.warning(
                "If a captcha appears, solve it now. Auto-continuing in 25s."
            )
            await asyncio.sleep(25)

            # ------------------------------------------------------------ 6
            # Submit.
            # ------------------------------------------------------------
            await human_pause()
            await page.locator(config.SELECTORS["submit_button"]).first.click()
            log.info("Submit button clicked -- waiting for confirmation page.")

            # ------------------------------------------------------------ 7
            # Confirmation detection.
            #
            # TODO: replace with the exact success indicator (URL pattern,
            #       confirmation text, "Buchung bestätigt", ...).
            # ------------------------------------------------------------
            try:
                await page.wait_for_load_state("networkidle", timeout=30_000)
            except PlaywrightTimeoutError:
                log.warning("networkidle wait timed out -- continuing anyway.")

            html = (await page.content()).lower()
            success_markers = [
                "buchung bestätigt", "booking confirmed",
                "vielen dank", "thank you",
                "confirmation", "bestätigung",
            ]
            booked = any(m in html for m in success_markers)

            if booked:
                log.info("BOOKING CONFIRMED.")
            else:
                log.warning(
                    "Could not auto-detect a confirmation page. "
                    "Inspect the open browser window manually."
                )

            # Leave the browser open so the user can take a screenshot /
            # complete any last manual step. Close it by pressing Ctrl-C.
            log.info(
                "Browser left open for manual verification. Press Ctrl-C "
                "in the terminal to close."
            )
            await asyncio.sleep(900)   # 15 min grace window

            return booked

        except Exception as exc:                                  # noqa: BLE001
            log.exception("Sniper crashed: %s", exc)
            # Pause so the user can see what happened on screen.
            await asyncio.sleep(120)
            return False
        finally:
            try:
                await context.close()
                await browser.close()
            except Exception:                                     # noqa: BLE001
                pass


# ---------------------------------------------------------------------------
# CLI smoke-test:   python -m sniper
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    config.configure_logging()
    asyncio.run(book_appointment(config.load_client_data()))
