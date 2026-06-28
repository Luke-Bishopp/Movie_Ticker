import os
import time
import requests
import logging
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# --- Config from environment variables ---
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL_SECONDS", "120"))  # default: 2 mins
HEARTBEAT_EVERY = int(os.environ.get("HEARTBEAT_EVERY_CHECKS", "5"))   # ping every 5 checks = ~10 mins

# --- Target Config ---
TARGET_DATE = os.environ.get("TARGET_DATE", "20250730")   # July 30, 2026 — Spider-Man release date
VENUE_KEYWORD = os.environ.get("VENUE_KEYWORD", "prasads").lower()
SCREEN_KEYWORD = os.environ.get("SCREEN_KEYWORD", "pcx").lower()
CITY_CODE = "HYD"

BMS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://in.bookmyshow.com/",
    "x-bms-id": "in.bms.web",
    "x-region-code": CITY_CODE,
    "x-region-slug": "hyderabad",
    "x-subregion-code": "",
}


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        logging.info("Telegram notification sent!")
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")


def check_july30_at_prasads():
    """
    Core strategy: watch for ANY movie appearing at Prasads on July 30.
    We don't care about the movie name — if Prasads opens bookings for
    July 30, it's Spider-Man. Check for PCX screen specifically.
    """

    # Try multiple BMS API endpoints since they change
    endpoints = [
        f"https://in.bookmyshow.com/api/movies-data/showtimes-by-event?appCode=MOBAND2&appVersion=14.3.1&language=en&eventCode=&regionCode={CITY_CODE}&subRegion=&format=json&date={TARGET_DATE}",
        f"https://in.bookmyshow.com/api/explore/v1/discover/regions/{CITY_CODE}/collection/nowShowing?",
    ]

    for url in endpoints:
        try:
            r = requests.get(url, headers=BMS_HEADERS, timeout=15)
            if r.status_code != 200:
                logging.warning(f"Got {r.status_code} from {url}")
                continue

            data = r.json()
            result = scan_response_for_prasads_pcx(data, url)
            if result:
                return result

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error: {e}")
        except Exception as e:
            logging.error(f"Parse error: {e}")

    # Fallback: raw text scan of BMS Hyderabad page for the target date
    return check_bms_raw_page()


def scan_response_for_prasads_pcx(data, source_url):
    """
    Recursively scan any JSON structure for Prasads + PCX + target date combo.
    Returns alert dict if found, None otherwise.
    """
    text_dump = str(data).lower()

    # Quick pre-filter: does this response even mention prasads?
    if VENUE_KEYWORD not in text_dump:
        logging.info(f"Prasads not mentioned in response from {source_url}")
        return None

    # Walk events
    events = (
        data.get("BookMyShow", {}).get("arrEvents", []) or
        data.get("arrEvents", []) or
        data.get("events", []) or
        []
    )

    for event in events:
        venues = (
            event.get("Venues") or
            event.get("arrVenues") or
            event.get("venues") or
            []
        )
        event_name = event.get("EventName") or event.get("EventTitle") or event.get("name") or "Unknown Movie"

        for venue in venues:
            venue_name = (venue.get("VenueName") or venue.get("venueName") or venue.get("name") or "").lower()
            if VENUE_KEYWORD not in venue_name:
                continue

            logging.info(f"✅ Prasads found for event: {event_name}")

            # Check sessions/screens for PCX
            sessions = (
                venue.get("ShowDetails") or
                venue.get("arrShowDetails") or
                venue.get("sessions") or
                venue.get("shows") or
                []
            )

            for session in sessions:
                screen = (
                    session.get("ScreenName") or
                    session.get("ScreenDesc") or
                    session.get("VenueHallName") or
                    session.get("screenName") or
                    ""
                ).lower()

                show_time = (
                    session.get("ShowTime") or
                    session.get("ShowStartTime") or
                    session.get("showTime") or
                    "Check BMS app"
                )

                if SCREEN_KEYWORD in screen:
                    return {
                        "movie": event_name,
                        "screen": screen.upper(),
                        "show_time": show_time,
                        "venue": venue.get("VenueName") or "Prasads"
                    }

                # Even if screen name isn't explicitly PCX yet,
                # flag that Prasads opened for this date
                logging.info(f"Prasads has {event_name} but screen is '{screen}' — not PCX yet")

    return None


def check_bms_raw_page():
    """
    Fallback: scrape the BMS Hyderabad movies page and do a text search.
    Less precise but catches edge cases.
    """
    try:
        url = f"https://in.bookmyshow.com/hyderabad/movies"
        r = requests.get(url, headers=BMS_HEADERS, timeout=15)
        text = r.text.lower()

        if VENUE_KEYWORD in text and SCREEN_KEYWORD in text:
            logging.info("PCX + Prasads found in raw page scan!")
            return {
                "movie": "Spider-Man (detected via page scan)",
                "screen": "PCX",
                "show_time": "Check BMS app",
                "venue": "Prasads"
            }
    except Exception as e:
        logging.error(f"Raw page scan error: {e}")

    return None


def main():
    logging.info(f"🕷️ BMS Watcher started — targeting July 30 at Prasads PCX")
    logging.info(f"Checking every {CHECK_INTERVAL}s | Heartbeat every {HEARTBEAT_EVERY} checks")

    send_telegram(
        f"🤖 <b>BMS Watcher is LIVE!</b>\n\n"
        f"🎯 Strategy: Watching for <b>ANY movie on July 30, 2026</b> at Prasads PCX\n"
        f"⏱️ Checking every <b>{CHECK_INTERVAL} seconds</b>\n"
        f"💓 Heartbeat every <b>{HEARTBEAT_EVERY * CHECK_INTERVAL // 60} minutes</b>\n\n"
        f"The moment PCX opens for July 30 = you get pinged. 🕷️"
    )

    check_count = 0
    alerted = False

    while True:
        check_count += 1
        logging.info(f"Check #{check_count}...")

        result = check_july30_at_prasads()

        if result and not alerted:
            send_telegram(
                f"🚨🕷️ <b>GO GO GO — BOOK NOW!</b> 🕷️🚨\n\n"
                f"<b>Prasads PCX is OPEN for July 30!</b>\n\n"
                f"🎬 Movie: {result['movie']}\n"
                f"🏟️ Venue: {result['venue']}\n"
                f"📺 Screen: {result['screen']}\n"
                f"🕐 Show time: {result['show_time']}\n\n"
                f"🎟️ <b>BOOK NOW:</b>\n"
                f"https://in.bookmyshow.com/hyderabad/movies\n\n"
                f"<i>Open BMS → Prasads → PCX → grab your seat!</i>"
            )
            alerted = True
            # Keep running to catch more showtimes but don't spam
            logging.info("Alert sent! Continuing to monitor for additional shows...")

        # Heartbeat
        if check_count % HEARTBEAT_EVERY == 0:
            status = "✅ BOOKED — still watching for more shows" if alerted else "👀 Nothing yet — still watching"
            send_telegram(
                f"💓 <b>Heartbeat #{check_count // HEARTBEAT_EVERY}</b>\n"
                f"Status: {status}\n"
                f"Checks done: {check_count}\n"
                f"Next check in {CHECK_INTERVAL}s"
            )

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
