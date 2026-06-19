"""
sniper.py — Playwright-based booking engine (the "Sniper").

Triggered immediately after the Scanner detects an available slot.
Launches a real Chromium browser with full stealth configuration,
reads client credentials from client.json, and navigates the Goethe-Institut
booking form using human-like typing and pacing.
"""

import asyncio
import json
import random
from pathlib import Path

from loguru import logger
from playwright.async_api import (
    async_playwright,
    Page,
    BrowserContext,
    TimeoutError as PlaywrightTimeoutError,
)
from playwright_stealth import Stealth

import config
import notifier

# macOS-specific stealth profile — overrides default Win32 platform string
# and ensures navigator.platform / languages match a real macOS Chrome session.
_STEALTH = Stealth(
    navigator_platform_override="MacIntel",
    navigator_languages_override=("en-US", "en"),
    navigator_vendor_override="Google Inc.",
    navigator_user_agent_override=config.USER_AGENT,
)


# ---------------------------------------------------------------------------
# Client data loader
# ---------------------------------------------------------------------------

def load_client_data() -> dict[str, str]:
    """
    Load applicant details from client.json.

    Expected keys: first_name, last_name, passport, email, phone
    """
    path = Path(config.CLIENT_JSON_PATH)
    if not path.exists():
        raise FileNotFoundError(
            f"client.json not found at '{config.CLIENT_JSON_PATH}'. "
            "Please create it with your personal details."
        )

    data = json.loads(path.read_text(encoding="utf-8"))
    required = {"first_name", "last_name", "passport", "email", "phone"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"client.json is missing required keys: {missing}")

    return data


# ---------------------------------------------------------------------------
# Human simulation helpers
# ---------------------------------------------------------------------------

async def human_type(page: Page, selector: str, text: str) -> None:
    """
    Type `text` into the element matched by `selector` one character at a time,
    with a random per-keystroke delay (TYPE_DELAY_MIN_MS … TYPE_DELAY_MAX_MS).

    This defeats keystroke-velocity bot-detection heuristics that flag
    Playwright's instant `.fill()` method.

    Args:
        page:     Active Playwright Page object.
        selector: CSS selector of the input field.
        text:     The string to type.
    """
    element = page.locator(selector)
    await element.click()           # Focus the field first
    await element.clear()           # Remove any pre-filled placeholder text

    for char in text:
        await element.type(char, delay=0)   # type() fires real key events
        delay_ms = random.randint(
            config.TYPE_DELAY_MIN_MS,
            config.TYPE_DELAY_MAX_MS,
        )
        await asyncio.sleep(delay_ms / 1000)

    logger.debug(f"Typed into '{selector}' ({len(text)} chars).")


async def human_click(page: Page, selector: str) -> None:
    """
    Click an element and then sleep for a short random duration to
    mimic the natural pause a human takes between interactions.
    """
    await page.locator(selector).click()
    pause = random.uniform(config.STEP_SLEEP_MIN, config.STEP_SLEEP_MAX)
    await asyncio.sleep(pause)
    logger.debug(f"Clicked '{selector}', paused {pause:.2f}s.")


async def human_sleep() -> None:
    """Short random sleep between navigation steps."""
    pause = random.uniform(config.STEP_SLEEP_MIN, config.STEP_SLEEP_MAX)
    await asyncio.sleep(pause)


# ---------------------------------------------------------------------------
# Browser / context factory
# ---------------------------------------------------------------------------

async def _build_context(playwright) -> tuple:
    """
    Launch Chromium with stealth settings and return (browser, context).

    Stealth measures applied:
      • playwright-stealth patches navigator.webdriver = false,
        plugins array, languages, hardware concurrency, etc.
      • Custom macOS User-Agent replaces Playwright's default headless UA.
      • --disable-blink-features=AutomationControlled removes the CDP flag.
      • Realistic viewport matching a 13" MacBook screen.
    """
    browser = await playwright.chromium.launch(
        headless=config.HEADLESS,
        args=config.CHROMIUM_ARGS,
    )

    context = await browser.new_context(
        viewport=config.VIEWPORT,
        user_agent=config.USER_AGENT,
        locale="en-US",
        timezone_id="Europe/Berlin",        # Match typical Goethe portal timezone
        java_script_enabled=True,
        accept_downloads=False,
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
        },
    )

    # Apply playwright-stealth to every new page opened in this context
    context.on(
        "page",
        lambda page: asyncio.ensure_future(_STEALTH.apply_stealth_async(page)),
    )

    return browser, context


# ---------------------------------------------------------------------------
# Booking flow
# ---------------------------------------------------------------------------

async def _step_navigate_to_booking(page: Page) -> None:
    """
    Step 1 — Navigate to the booking page and trigger the slot search.

    ── HOW TO CONFIGURE ────────────────────────────────────────────────────
    Replace TARGET_URL in config.py with the exact URL of the appointment
    calendar or search page.

    If there is a "Search" or "Check availability" button before the calendar
    loads, set its selector in config.SELECTORS["search_button"].
    ────────────────────────────────────────────────────────────────────────
    """
    logger.info(f"Navigating to booking URL: {config.TARGET_URL}")
    await page.goto(config.TARGET_URL, wait_until="domcontentloaded", timeout=config.BROWSER_TIMEOUT)
    await human_sleep()

    # If the portal requires clicking a "Search" button first
    search_sel = config.SELECTORS.get("search_button", "")
    if search_sel and not search_sel.startswith("#REPLACE"):
        logger.info("Clicking search/availability button …")
        await human_click(page, search_sel)
        await page.wait_for_load_state("networkidle", timeout=config.BROWSER_TIMEOUT)


async def _step_select_slot(page: Page) -> None:
    """
    Step 2 — Select the first available appointment slot.

    ── HOW TO CONFIGURE ────────────────────────────────────────────────────
    Inspect the calendar/list view and find the selector for the first
    clickable slot (a <button> or <a> element).
    Set it as config.SELECTORS["first_slot"].
    ────────────────────────────────────────────────────────────────────────
    """
    slot_sel = config.SELECTORS["first_slot"]
    logger.info(f"Waiting for a slot to appear: '{slot_sel}' …")

    await page.wait_for_selector(slot_sel, timeout=config.BROWSER_TIMEOUT)
    logger.info("Slot element found — clicking.")
    await human_click(page, slot_sel)
    await page.wait_for_load_state("networkidle", timeout=config.BROWSER_TIMEOUT)
    await human_sleep()


async def _step_fill_form(page: Page, client: dict[str, str]) -> None:
    """
    Step 3 — Fill in the applicant's personal details using human-paced typing.

    ── HOW TO CONFIGURE ────────────────────────────────────────────────────
    After clicking a slot the portal will show a registration / contact form.
    Use DevTools → Inspector to find each field's id or class, then update
    config.SELECTORS with the correct CSS selectors for:
      first_name, last_name, passport, email, phone
    ────────────────────────────────────────────────────────────────────────
    """
    logger.info("Filling in applicant details …")

    field_map = {
        "first_name": client["first_name"],
        "last_name":  client["last_name"],
        "passport":   client["passport"],
        "email":      client["email"],
        "phone":      client["phone"],
    }

    for field_key, value in field_map.items():
        selector = config.SELECTORS.get(field_key, "")
        if not selector or selector.startswith("#REPLACE"):
            logger.warning(
                f"Selector for '{field_key}' is not configured — skipping field. "
                "Update config.SELECTORS with the real selector."
            )
            continue

        logger.debug(f"Typing '{field_key}' …")
        await human_type(page, selector, value)
        await human_sleep()


async def _step_confirm_and_submit(page: Page) -> None:
    """
    Step 4 — Click the confirmation checkbox / agree button and submit the form.

    ── HOW TO CONFIGURE ────────────────────────────────────────────────────
    Some portals have a multi-step confirmation:
      • A "confirm details" page with a Confirm button → config.SELECTORS["confirm_button"]
      • A final "submit booking" button               → config.SELECTORS["submit_button"]
    If your portal has only one step, leave confirm_button as the REPLACE
    placeholder and only set submit_button.
    ────────────────────────────────────────────────────────────────────────
    """
    confirm_sel = config.SELECTORS.get("confirm_button", "")
    submit_sel  = config.SELECTORS.get("submit_button", "")

    if confirm_sel and not confirm_sel.startswith("#REPLACE"):
        logger.info("Clicking confirm button …")
        await human_click(page, confirm_sel)
        await page.wait_for_load_state("networkidle", timeout=config.BROWSER_TIMEOUT)
        await human_sleep()

    if submit_sel and not submit_sel.startswith("#REPLACE"):
        logger.info("Clicking final submit button …")
        await human_click(page, submit_sel)
        await page.wait_for_load_state("networkidle", timeout=config.BROWSER_TIMEOUT)
        await human_sleep()
    else:
        logger.warning(
            "Submit button selector not configured. "
            "Pausing for 120s so you can submit manually."
        )
        await asyncio.sleep(120)


async def _step_verify_booking(page: Page) -> bool:
    """
    Step 5 — Check the post-submit page for a success confirmation.

    ── HOW TO CONFIGURE ────────────────────────────────────────────────────
    After a successful booking the portal typically shows a confirmation page
    containing text like "Booking confirmed" or a reference number.
    Update the text/selector below to match the actual confirmation message.
    ────────────────────────────────────────────────────────────────────────
    """
    # PLACEHOLDER: adapt this text to what the portal actually shows on success
    success_markers = [
        "booking confirmed",
        "appointment confirmed",
        "bestätigung",       # German: "confirmation"
        "ihre buchung",      # German: "your booking"
    ]

    page_text = (await page.content()).lower()
    for marker in success_markers:
        if marker in page_text:
            logger.success(f"Booking confirmed! Confirmation marker found: '{marker}'")
            return True

    logger.warning(
        "Could not automatically verify booking success. "
        "Please check the browser window manually."
    )
    return False


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run_sniper() -> None:
    """
    Launch the Playwright booking engine and attempt to secure the appointment.

    Called by main.py as soon as the Scanner fires the slot_found_event.
    """
    client = load_client_data()
    logger.info(f"Sniper launched for client: {client['first_name']} {client['last_name']}")

    async with async_playwright() as pw:
        browser, context = await _build_context(pw)
        page = await context.new_page()

        # Apply stealth patches to suppress all automation signals
        await _STEALTH.apply_stealth_async(page)

        try:
            await _step_navigate_to_booking(page)
            await _step_select_slot(page)
            await _step_fill_form(page, client)
            await _step_confirm_and_submit(page)

            success = await _step_verify_booking(page)

            if success:
                await notifier.notify(
                    f"✅ <b>Booking SUCCESSFUL!</b>\n"
                    f"Client: {client['first_name']} {client['last_name']}\n"
                    f"Please check your email ({client['email']}) for the confirmation."
                )
            else:
                await notifier.notify(
                    f"⚠️ <b>Booking submitted but outcome unclear.</b>\n"
                    f"Client: {client['first_name']} {client['last_name']}\n"
                    "Check the browser window or your email to confirm."
                )

        except PlaywrightTimeoutError as exc:
            logger.error(f"Playwright timeout: {exc}")
            await notifier.notify(
                f"❌ <b>Sniper timed out</b> — element not found in time.\n{exc}"
            )
        except Exception as exc:
            logger.exception(f"Unexpected sniper error: {exc}")
            await notifier.notify(
                f"❌ <b>Sniper crashed</b>: {exc}\n"
                "Check the terminal for the full traceback."
            )
        finally:
            # Keep the browser open so you can intervene manually (e.g. solve CAPTCHA)
            # then close it gracefully after a brief pause.
            logger.info(
                "Sniper flow complete. Browser will stay open for 60s "
                "in case manual intervention is needed."
            )
            await asyncio.sleep(60)
            await context.close()
            await browser.close()
