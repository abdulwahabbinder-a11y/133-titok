# Goethe-Institut Appointment Bot

Resilient async Python automation for monitoring Goethe-Institut booking pages and triggering a Playwright sniper when slots open.

## Architecture

```
┌─────────────┐     slot detected      ┌──────────────┐
│   SCANNER   │ ─────────────────────► │    SNIPER    │
│ httpx poll  │     Telegram alert     │  Playwright  │
│  15–30 sec  │                        │ headless=False│
└─────────────┘                        └──────────────┘
```

| Module | Role |
|--------|------|
| `goethe_bot/scanner.py` | Lightweight HTTP polling (no browser) |
| `goethe_bot/sniper.py` | Visible Chromium booking engine with stealth |
| `goethe_bot/config.py` | URLs, selectors, proxy & Telegram placeholders |
| `goethe_bot/human_sim.py` | Human-like typing and step delays |
| `goethe_bot/notifications.py` | Telegram alert hook |
| `goethe_bot/main.py` | Orchestrator entry point |

## Setup (macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp client.json.example client.json   # fill in your details
```

## Configuration

1. **`goethe_bot/config.py`** — set `SCANNER_TARGET_URL`, `SNIPER_BOOKING_URL`, and all `FormSelectors` after inspecting the live portal in DevTools.
2. **`client.json`** — applicant `first_name`, `last_name`, `passport`, `email`, `phone`.
3. **Proxies** — set `PROXY.enabled = True` and `PROXY.rotating_endpoint` with your residential provider credentials.
4. **Telegram** — set `TELEGRAM.enabled = True` plus `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` (or env vars).

## Run

```bash
python -m goethe_bot.main
```

Press `Ctrl+C` to stop the scanner gracefully.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `GOETHE_SCANNER_URL` | Override scanner target URL |
| `GOETHE_BOOKING_URL` | Override sniper booking URL |
| `GOETHE_CLIENT_JSON` | Path to client data file |
| `GOETHE_PROXY_URL` | Rotating residential proxy endpoint |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat ID |
| `GOETHE_LOG_LEVEL` | Logging level (default `INFO`) |
