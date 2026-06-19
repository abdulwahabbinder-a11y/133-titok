# Goethe-Institut Appointment Bot

A resilient, stealthy, two-stage automation bot that monitors the Goethe-Institut booking portal for available visa/language-test appointment slots and books one the instant it appears.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                       main.py                           │
│  Orchestrator — starts Scanner, awaits slot signal,     │
│  then launches Sniper                                   │
└────────────────┬────────────────────────────────────────┘
                 │
       ┌─────────┴──────────┐
       │                    │
 ┌─────▼──────┐      ┌──────▼──────┐
 │ scanner.py │      │  sniper.py  │
 │            │      │             │
 │ httpx/h2   │ ───► │ Playwright  │
 │ no browser │      │ Chromium    │
 │ proxy rot. │      │ + stealth   │
 └────────────┘      └─────────────┘
       │                    │
       └────────┬───────────┘
                │
         ┌──────▼──────┐
         │ notifier.py │
         │ Telegram /  │
         │ extensible  │
         └─────────────┘
```

| File | Role |
|---|---|
| `main.py` | Entry point & orchestrator |
| `config.py` | All tunable constants & selectors |
| `scanner.py` | Lightweight HTTP poller with proxy rotation |
| `sniper.py` | Playwright booking engine with human simulation |
| `notifier.py` | Telegram alerts (extensible to email / WhatsApp) |
| `client.json` | Applicant personal data |
| `.env` | Secrets (Telegram token, chat ID) |

---

## Quick Start

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
pip install -r requirements.txt
playwright install chromium        # downloads ~130 MB browser binary
```

### 2. Configure secrets

```bash
cp .env.example .env
# Edit .env and add your Telegram bot token and chat ID
```

### 3. Fill in your personal details

Edit `client.json`:

```json
{
  "first_name": "Max",
  "last_name":  "Mustermann",
  "passport":   "C01X00T47",
  "email":      "max@example.com",
  "phone":      "+49 170 1234567"
}
```

### 4. Configure the target portal

Open `config.py` and update **every line marked `REPLACE`**:

| Constant | What to set |
|---|---|
| `TARGET_URL` | The URL of the Goethe booking / calendar page |
| `NO_SLOT_MARKER` | Exact text shown when no slots exist |
| `AVAILABLE_SLOT_SELECTOR` | CSS selector of the slot button / link (optional but recommended) |
| `SELECTORS[...]` | CSS selectors for every form field |

> **Tip:** Open DevTools (⌘ + ⌥ + I) on the booking page, switch to the *Inspector* tab, right-click each field → *Copy selector* to get the CSS path.

### 5. (Optional) Add proxies

Append residential proxy URLs (one per line) to `proxies.txt`:

```
http://user:pass@gate.smartproxy.com:7000
http://user:pass@residential.oxylabs.io:8001
```

Then set `PROXY_FILE = "proxies.txt"` in `config.py`.

### 6. Run the bot

```bash
python main.py
```

The bot logs to the console and to `bot.log`. A Chromium window opens the moment a slot is detected.

---

## Key Design Decisions

### Scanner (no browser)
Uses `httpx` with HTTP/2 to make raw GET requests — orders of magnitude lighter than a full browser. IPs are rotated on every request to avoid rate-limit bans.

### Sniper (stealthy browser)
`playwright-stealth` patches every JavaScript property that fingerprinters probe (`navigator.webdriver`, `plugins`, `languages`, hardware concurrency, WebGL vendor, etc.).  
`--disable-blink-features=AutomationControlled` removes the CDP automation flag at the Chromium level.

### Human simulation
- Per-character typing with 50–150 ms random delay → defeats keystroke-velocity detectors.
- Random 0.5–1.5 s pauses between steps → mimics natural reading/interaction pace.
- Randomised `Accept-Language` headers → blends into organic traffic.

### Headless = False
The browser window is visible. This lets you:
- Solve CAPTCHAs manually if one appears.
- Observe the flow and intervene if the bot misidentifies a field.
- The bot waits 60 s after submitting before closing the window.

---

## Extending Notifications

Open `notifier.py` and implement `_send_email()` or `_send_whatsapp()`, then uncomment the corresponding line in `notify()`. Both placeholders already exist in the file.

---

## Disclaimer

This tool is provided for educational and personal productivity purposes. Ensure your use complies with the Goethe-Institut's terms of service and any applicable laws.
