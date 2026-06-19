# Appointment Availability Monitor

This repository contains a compliant Python availability monitor for a
Goethe-Institut appointment page. It performs lightweight HTTP checks and opens
Chromium for manual booking when it detects a potential slot.

The tool intentionally does **not** bypass anti-bot systems, rotate residential
proxies, solve CAPTCHAs, hide automation fingerprints, or submit booking forms.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
cp client.example.json client.json
```

Edit `client.json` locally. It is ignored by git.

## Configuration

Set the booking page URL after confirming automated monitoring is permitted for
that page:

```bash
export BOOKING_URL="https://www.goethe.de/YOUR-BOOKING-PAGE"
```

Optional Telegram notification placeholder:

```bash
export TELEGRAM_BOT_TOKEN="123456:token"
export TELEGRAM_CHAT_ID="123456789"
```

Optional single outbound proxy for permitted network routing:

```bash
export HTTP_PROXY_URL="http://user:pass@host:port"
```

## Run

Continuous monitor:

```bash
python goethe_appointment_monitor.py
```

Single scan:

```bash
python goethe_appointment_monitor.py --once
```

Override the URL without environment variables:

```bash
python goethe_appointment_monitor.py --url "https://www.goethe.de/YOUR-BOOKING-PAGE"
```

## Detection placeholders

Availability is detected in `goethe_appointment_monitor.py` using:

- `unavailable_markers`, such as `"No appointments available"`
- `positive_slot_patterns`, such as `"book now"` or `"select appointment"`

Adjust those strings after inspecting the actual page response.
