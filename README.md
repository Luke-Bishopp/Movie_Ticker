# 🕷️ BMS Spider-Man PCX Watcher

Watches BookMyShow for Spider-Man Brand New Day at Prasads PCX, Hyderabad.
Sends a Telegram alert the moment bookings open.

---

## Deploy on Railway (Free, No Credit Card)

### Step 1 — GitHub Setup
1. Go to github.com → sign up / log in (free)
2. Create a new repository called `bms-watcher`
3. Upload these 3 files: `main.py`, `requirements.txt`, `Dockerfile`

### Step 2 — Railway Setup
1. Go to railway.app → sign up with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your `bms-watcher` repo
4. Railway will auto-detect the Dockerfile and start building

### Step 3 — Set Environment Variables
In Railway dashboard → your project → **Variables** tab, add:

| Variable | Value |
|---|---|
| `TELEGRAM_TOKEN` | your new bot token from BotFather |
| `TELEGRAM_CHAT_ID` | 811851413 |
| `CHECK_INTERVAL_SECONDS` | 120 |

### Step 4 — Deploy
Hit **Deploy** — Railway will build and run it 24/7 for free.

You'll get a Telegram message saying "BMS Watcher is live!" to confirm it's running.

---

## What it does
- Checks BMS every 2 minutes for Spider-Man at Prasads
- Scans all dates (today + 7 days ahead)
- Specifically looks for PCX screen
- Sends instant Telegram alert with showtime + booking link
- Sends heartbeat every 50 checks so you know it's alive

---

## Free tier limits
Railway free tier gives 500 hours/month — enough to run 24/7 for ~20 days.
For longer, create a free account at render.com as backup (same setup).
