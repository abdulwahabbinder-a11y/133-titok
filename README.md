# Goethe-Institut Appointment Sniper

A resilient, high-speed and stealthy automation pipeline that books
visa / language-test appointments on the Goethe-Institut portal the
moment a slot opens up.

The system is split into two cooperating components:

| Component   | Purpose                                                          | Cost      |
|-------------|------------------------------------------------------------------|-----------|
| **Scanner** | Lightweight `httpx` poller, rotating residential proxies.        | Cheap     |
| **Sniper**  | Async Playwright (Chromium, `headless=False`) booking engine with `playwright-stealth`, human typing and randomised pauses. | Heavy |

```
┌──────────┐        slot_open Event        ┌─────────┐
│ Scanner  │ ─────────────────────────────▶│ Sniper  │ ───▶ booking
└──────────┘                               └─────────┘
   │  every 15-30 s, new proxy IP             │  Chromium, stealth, human typing
   ▼                                          ▼
 HTTP GET (no browser)                Playwright + client.json
```

## Requirements

* macOS (tested on Sonoma & Sequoia; the code is portable, only the
  native notification banner is macOS-only)
* Python 3.10+
* A Goethe-Institut account already pre-filled in the browser is not
  required -- the Sniper fills the form from `client.json`

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

## Configure

1. **Client data** -- copy the template and fill it in:

   ```bash
   cp client.example.json client.json
   $EDITOR client.json
   ```

2. **Environment / secrets** -- copy and fill in:

   ```bash
   cp .env.example .env
   $EDITOR .env
   ```

   You can configure:

   * `GOETHE_TARGET_URL` -- the exact booking page / JSON endpoint.
   * `PROXY_GATEWAY` *or* `PROXY_LIST` -- rotating residential proxies.
   * `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` -- Telegram alerts.

3. **Selectors** -- open the Goethe portal in DevTools and, inside
   `config.py`, update every entry of `SELECTORS` and the
   `SOLD_OUT_MARKERS` / `AVAILABLE_MARKERS` lists. Every value that
   needs your attention is tagged with a `# TODO:` comment.

## Run

```bash
# Full pipeline (scan -> sniper -> notify, retrying forever)
python main.py

# Stop after the first sniper attempt
python main.py --once

# Debug logging
python main.py --debug
```

You can also run the components individually for testing:

```bash
python -m scanner            # poll the page until availability is detected
python -m sniper             # open Chromium and run the booking flow once
python -m notifier "hi"      # smoke-test Telegram / macOS notifications
```

## Stealth notes

* `headless=False` so you can solve a Cloudflare Turnstile or hCaptcha
  manually if it appears -- the Sniper waits 25 s on the captcha step
  by default; tune `await asyncio.sleep(25)` in `sniper.py` if needed.
* Chromium is launched with `--disable-blink-features=AutomationControlled`
  and `playwright-stealth` is applied to every page. We also push a
  belt-and-braces JS patch that wipes `navigator.webdriver`,
  randomises `languages`/`plugins` and injects a fake `window.chrome`.
* Form fields are filled with **per-character delays of 50-150 ms**
  via `human_type()` -- never `Locator.fill()`.
* Between high-level steps we sleep a random 0.5-1.5 s
  (`human_pause()`), and the Scanner polls every 15-30 s with a fresh
  proxy IP.

## File layout

```
.
├── config.py              # all tunables / selectors / secrets
├── scanner.py             # async httpx poller + proxy rotation
├── sniper.py              # async Playwright booking engine
├── notifier.py            # Telegram / macOS push helpers
├── main.py                # orchestrator (Scanner -> Sniper)
├── client.example.json    # template for client data
├── .env.example           # template for secrets
└── requirements.txt
```

## Disclaimer

This project is provided for educational purposes. Make sure you
respect the terms of service of any website you automate and that you
have a legitimate booking need.
