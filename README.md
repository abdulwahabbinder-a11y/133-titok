# Goethe-Institut Appointment Sniper

A two-stage async Python bot for monitoring and auto-booking
Goethe-Institut exam / visa appointments on **macOS**.

```
┌────────────────────┐    asyncio.Event    ┌──────────────────────┐
│  SCANNER (httpx)   │ ──────────────────▶ │  SNIPER (Playwright) │
│  • 15-30 s polling │                     │  • Chromium visible  │
│  • Rotating proxy  │                     │  • Stealth patches   │
│  • Marker diff     │                     │  • Human-typed form  │
└────────────────────┘                     └──────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Telegram Alert  │
                  └─────────────────┘
```

> **Read this first.** This project is intended for *personal* use to book
> your own appointment.  Respect the Goethe-Institut Terms of Service
> and applicable laws — automated booking may be restricted in your
> jurisdiction.  You are solely responsible for how you use this code.

---

## 1. Features

| Stage      | Tech                                | Why                                                   |
|------------|-------------------------------------|-------------------------------------------------------|
| Scanner    | `httpx` (HTTP/2) + `BeautifulSoup`  | Tiny RAM footprint, no JS engine, harder to fingerprint |
| Proxies    | Rotating residential gateway        | Fresh exit IP per scan – avoids per-IP rate limits     |
| Sniper     | `playwright` + `playwright-stealth` | Full DOM/JS execution, bypasses Cloudflare/Turnstile   |
| Humanising | `human.py`                          | 50–150 ms key delay, mouse jitter, micro-pauses        |
| Alerts     | Telegram Bot API (placeholder)      | Push the moment a slot appears / is booked             |

---

## 2. Quick start (macOS)

```bash
# 1. clone and enter the project
git clone <repo> goethe-sniper && cd goethe-sniper

# 2. virtual-env
python3 -m venv .venv
source .venv/bin/activate

# 3. dependencies
pip install -r requirements.txt
python -m playwright install chromium

# 4. configuration
cp .env.example .env          # edit TARGET_URL, proxy, telegram, etc.
cp client.example.json client.json   # fill in your real personal data

# 5. run
python main.py
```

> First Playwright launch on macOS may prompt for keychain access –
> approve it once; subsequent runs are silent.

---

## 3. Configuration

### 3.1 `.env`

| Variable              | Purpose                                                                 |
|-----------------------|-------------------------------------------------------------------------|
| `TARGET_URL`          | Exact booking / availability page on goethe.de                          |
| `SCAN_INTERVAL_MIN/MAX` | Randomised poll cadence (seconds)                                     |
| `NEGATIVE_MARKER`     | Text present **only when no slots** (e.g. `Keine Buchung möglich`)      |
| `POSITIVE_MARKER`     | Text/CTA present **only when slots open** (e.g. `Anmelden`)             |
| `PROXY_URL` / host+port | Rotating residential gateway (BrightData, Oxylabs, IPRoyal, …)        |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Optional push notifications                       |

### 3.2 `client.json`

```json
{
    "first_name": "Max",
    "last_name":  "Mustermann",
    "passport":   "C01X00T47",
    "email":      "max@example.com",
    "phone":      "+491701234567"
}
```

Never commit this file – it is already in `.gitignore`.

---

## 4. Where to customise the selectors

Open the target booking page in Chrome DevTools and inspect each form
control.  Then edit the placeholders inside `sniper.py` – every spot
that needs your attention is tagged with:

```python
# >>> CUSTOMISE ME <<<
```

The same marker is used inside `scanner.py` for the availability
heuristic, in case the simple "negative-string disappeared" check is
not reliable for your portal.

---

## 5. Project layout

```
.
├── main.py            # orchestrator
├── scanner.py         # lightweight polling layer
├── sniper.py          # Playwright booking engine
├── human.py           # typing / clicking simulation helpers
├── notifier.py        # Telegram (or any) alert hook
├── config.py          # env-driven settings
├── client.example.json
├── .env.example
├── requirements.txt
└── README.md
```

---

## 6. Operational tips

* **Run on a wired connection** – Wi-Fi jitter can push Scanner latency
  past the slot's lifetime (popular Goethe slots vanish in < 3 s).
* **Keep the Mac awake**: `caffeinate -dimsu python main.py`.
* **Rotate proxies, not VPNs** – consumer VPN ranges are pre-banned
  by Cloudflare on goethe.de.
* If you hit Turnstile / hCaptcha in the Sniper window, solve it
  manually – the script keeps the browser open for 5 minutes after
  the form submission specifically for this case.
* Logs are written to `goethe_sniper.log` (rotated at 10 MB).

---

## 7. Legal & ethical notice

This script is provided **for educational purposes**.  Automating any
public-service booking system may violate its Terms of Service or local
regulations.  Use only for appointments you are personally entitled to
book, and never to resell / scalp slots.
