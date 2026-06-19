# Goethe Appointment Availability Monitor

Async Python scaffold for monitoring a Goethe-Institut appointment page with a
lightweight HTTP scanner and opening a visible Playwright browser when an
availability signal appears.

This project intentionally supports a compliant assisted workflow: it avoids
proxy rotation, CAPTCHA bypass, anti-bot fingerprint evasion, and automated form
submission against third-party booking systems.

## Files

- `appointment_monitor.py` - scanner, Telegram alert placeholder, and assisted
  Playwright browser launch.
- `client.example.json` - template for local applicant data.
- `requirements.txt` - Python dependencies.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp client.example.json client.json
```

Edit `client.json` locally with:

```json
{
  "first_name": "Erika",
  "last_name": "Mustermann",
  "passport": "C01X00T47",
  "email": "erika.mustermann@example.com",
  "phone": "+491701234567"
}
```

## Configuration

Set the target URLs and optional parsing hints before running:

```bash
export GOETHE_SCAN_URL="https://www.goethe.de/INS/YOUR_TARGET_BOOKING_PAGE"
export GOETHE_BOOKING_URL="https://www.goethe.de/INS/YOUR_TARGET_BOOKING_PAGE"

# Optional: pipe-separated text markers that mean no slots are available.
export UNAVAILABLE_MARKERS="No appointments available|Keine Termine verfügbar"

# Optional: pipe-separated CSS selectors that only exist when slots are visible.
export AVAILABILITY_SELECTORS=".appointment-slot|button[data-testid='book-appointment']"

# Optional Telegram notification placeholders.
export TELEGRAM_BOT_TOKEN="123456:replace-me"
export TELEGRAM_CHAT_ID="123456789"
```

Run:

```bash
python appointment_monitor.py
```

When the scanner detects availability, the script sends the alert placeholder
and opens Chromium with a 1280x800 viewport and a macOS Chrome user agent for
manual booking completion.
