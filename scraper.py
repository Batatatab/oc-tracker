import os
import json
import requests
from bs4 import BeautifulSoup

URL = "https://www.icaionlineregistration.org/launchbatchdetail.aspx"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = "@OCreminder"
DATA_FILE = "seen_batches.json"

# Western Region = 2, Orientation Course = 46
REGION_ID = "2"
COURSE_ID = "46"

# Add or remove branches to monitor here:
BRANCHES_TO_CHECK = {
    "JALGAON": "68",
    "PUNE": "77",
    "MUMBAI": "255",
    "NASHIK": "74",
    "AHMEDABAD": "56"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Origin": "https://www.icaionlineregistration.org",
    "Referer": "https://www.icaionlineregistration.org/launchbatchdetail.aspx",
}

def load_seen_batches():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_seen_batches(seen_batches):
    with open(DATA_FILE, "w") as f:
        json.dump(sorted(list(seen_batches)), f, indent=2)

def send_telegram_alert(batch):
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is not set.")
        return

    text = (
        f"🎓 *New ICAI OC Batch Announced!*\n\n"
        f"📍 *Centre:* {batch['pou']}\n"
        f"🆔 *Batch Code:* `{batch['batch_no']}`\n"
        f"📅 *Dates:* {batch['from_date']} to {batch['to_date']}\n"
        f"⏰ *Timings:* {batch['timings']}\n"
        f"💺 *Available Seats:* {batch['seats']}\n"
        f"📌 *Status:* {batch['status']}\n\n"
        f"🔗 [Register on ICAI Portal]({URL})"
    )

    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        res = requests.post(api_url, json=payload, timeout=10)
        res.raise_for_status()
        print(f"Sent alert for batch: {batch['batch_no']}")
    except Exception as e:
        print(f"Failed to send Telegram message for {batch['batch_no']}: {e}")

def scrape_branch(session, branch_name, branch_code, seen_batches, newly_seen):
    # Step 1: Harvest active ASP.NET state tokens
    res = session.get(URL, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(res.text, "html.parser")

    viewstate = soup.find("input", {"id": "__VIEWSTATE"})
    event_val = soup.find("input", {"id": "__EVENTVALIDATION"})
    gen = soup.find("input", {"id": "__VIEWSTATEGENERATOR"})

    if not viewstate or not event_val:
        print(f"[{branch_name}] Failed to extract ASP.NET viewstate tokens.")
        return

    payload = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": viewstate.get("value", ""),
        "__VIEWSTATEGENERATOR": gen.get("value", "10EF2921") if gen else "10EF2921",
        "__EVENTVALIDATION": event_val.get("value", ""),
        "ddl_reg": REGION_ID,
        "ddlPou": branch_code,
        "ddl_course": COURSE_ID,
        "btn_getlist": "Get List"
    }

    # Step 2: Query batch list
    post_res = session.post(URL, data=payload, headers=HEADERS, timeout=20)
    result_soup = BeautifulSoup(post_res.text, "html.parser")
    table = result_soup.find("table", {"id": "GridView1"})

    if not table:
        print(f"[{branch_name}] No batches listed.")
        return

    rows = table.find_all("tr")[1:]  # Skip table header
    print(f"[{branch_name}] Found {len(rows)} batches.")

    for row in rows:
        cols = [c.text.strip() for c in row.find_all("td")]
        if len(cols) < 7:
            continue

        batch_no = cols[0]
        batch_data = {
            "batch_no": batch_no,
            "seats": cols[1],
            "from_date": cols[2],
            "to_date": cols[3],
            "timings": cols[4],
            "pou": cols[5],
            "status": cols[10] if len(cols) > 10 else "Open"
        }

        # Check if already notified
        if batch_no not in seen_batches:
            send_telegram_alert(batch_data)
            seen_batches.add(batch_no)
            newly_seen.add(batch_no)

def main():
    seen_batches = load_seen_batches()
    newly_seen = set()
    session = requests.Session()

    for name, code in BRANCHES_TO_CHECK.items():
        try:
            scrape_branch(session, name, code, seen_batches, newly_seen)
        except Exception as e:
            print(f"Error scraping {name}: {e}")

    if newly_seen:
        save_seen_batches(seen_batches)
        print(f"Added {len(newly_seen)} new batches to tracking.")
    else:
        print("No new batches found across monitored branches.")

if __name__ == "__main__":
    main()
