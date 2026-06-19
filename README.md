# Goethe Appointment Scanner + Sniper (Async Python)

This project provides a resilient two-stage automation framework:

1. **Scanner** (`httpx`, no browser): polls a booking endpoint every 15-30 seconds.
2. **Sniper** (`playwright`): opens Chromium only after a positive scanner signal.

## Important

- Use this only in ways that comply with Goethe-Institut terms and local law.
- This implementation does **not** include anti-bot bypass logic.
- You must inspect the live form and replace placeholder selectors/URLs before use.

## Project Files

- `main.py` - orchestrates scanner, alert, and sniper.
- `goethe_bot/config.py` - typed config and `client.json` loading.
- `goethe_bot/scanner.py` - lightweight monitor with proxy-rotation placeholder.
- `goethe_bot/sniper.py` - browser booking flow with human-like typing simulation.
- `goethe_bot/alerts.py` - Telegram alert placeholder.
- `bot_config.example.json` - config template with placeholders.
- `client.example.json` - sample personal data format.

## macOS Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Configure

1. Copy and edit config files:

```bash
cp bot_config.example.json bot_config.json
cp client.example.json client.json
```

2. In `bot_config.json`, replace:
   - `scan.endpoint_url` with the lightweight monitoring URL.
   - `sniper.booking_url` with the actual booking flow page.
   - `sniper.selectors.*` with real CSS/XPath selectors from your inspected page.
3. Optionally add residential proxies to `scan.residential_proxies`.
4. Optionally set Telegram credentials in `alert`.

## Run

```bash
python main.py --config bot_config.json --verbose
```

## Behavior Summary

- Scanner sends lightweight HTTP requests and checks for content changes.
- If unavailable text disappears and availability markers appear, a slot is flagged.
- Sniper launches Chromium with:
  - `headless=False`
  - viewport `1280x800`
  - macOS Chrome user-agent
- Form typing is humanized with random 50-150ms per keystroke.
- Navigation/clicking pauses are randomized to 0.5-1.5s.

