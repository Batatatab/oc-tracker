import os
import re
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

# Branches to monitor
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

def extract_asp_tokens(soup):
    vs = soup.find("input", {"id": "__VIEWSTATE"})
    ev = soup.find("input", {"id": "__EVENTVALIDATION"})
    gen = soup.find("input", {"id": "__VIEWSTATEGENERATOR"})
    
    return {
        "__VIEWSTATE": vs.get("value", "") if vs else "",
        "__EVENTVALIDATION": ev.get("value", "") if ev else "",
        "__VIEWSTATEGENERATOR": gen.get("value", "10EF2921") if gen else "10EF2921"
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

    # Use HTML formatting to prevent underscore parse errors
    text = (
        f"🎓 <b>New ICAI OC Batch Announced!</b>\n\n"
        f"📍 <b>Centre:</b> {batch['pou']}\n"
        f"🆔 <b>Batch Code:</b> <code>{batch['batch_no']}</code>\n"
        f"📅 <b>Dates:</b> {batch['from_date']} to {batch['to_date']}\n"
        f"⏰ <b>Timings:</b> {batch['timings']}\n"
        f"💺 <b>Available Seats:</b> {batch['seats']}\n"
        f"📌 <b>Status:</b> {batch['status']}\n\n"
        f"🔗 <a href='{URL}'>Register on ICAI Portal</a>"
    )

    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        res = requests.post(api_url, json=payload, timeout=10)
        res.raise_for_status()
        print(f"Sent alert for batch: {batch['batch_no']}")
    except Exception as e:
        print(f"Failed to send Telegram message for {batch['batch_no']}: {e}")

def main():
    seen_batches = load_seen_batches()
    newly_seen = set()
    session = requests.Session()

    print("Fetching initial page...")
    res = session.get(URL, headers=HEADERS, timeout=20)
    tokens = extract_asp_tokens(BeautifulSoup(res.text, "html.parser"))

    # Step 1: Simulate selecting Western Region to populate branches and authorize branch IDs
    print(f"Selecting Region {REGION_ID} (Western)...")
    region_payload = {
        "__EVENTTARGET": "ddl_reg",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": tokens["__VIEWSTATE"],
        "__VIEWSTATEGENERATOR": tokens["__VIEWSTATEGENERATOR"],
        "__EVENTVALIDATION": tokens["__EVENTVALIDATION"],
        "ddl_reg": REGION_ID,
        "ddlPou": "Select",
        "ddl_course": COURSE_ID,
    }
    res_reg = session.post(URL, data=region_payload, headers=HEADERS, timeout=20)
    reg_tokens = extract_asp_tokens(BeautifulSoup(res_reg.text, "html.parser"))

    if not reg_tokens["__VIEWSTATE"]:
        print("Failed to initialize Western Region state.")
        return

    # Step 2: Query each branch using the populated state
    for branch_name, branch_code in BRANCHES_TO_CHECK.items():
        payload = {
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": reg_tokens["__VIEWSTATE"],
            "__VIEWSTATEGENERATOR": reg_tokens["__VIEWSTATEGENERATOR"],
            "__EVENTVALIDATION": reg_tokens["__EVENTVALIDATION"],
            "ddl_reg": REGION_ID,
            "ddlPou": branch_code,
            "ddl_course": COURSE_ID,
            "btn_getlist": "Get List"
        }

        try:
            post_res = session.post(URL, data=payload, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(post_res.text, "html.parser")
            
            # Find the GridView table (case-insensitive)
            table = soup.find("table", id=re.compile(r"gridview", re.I))

            if not table:
                print(f"[{branch_name}] No batches listed.")
                continue

            rows = table.find_all("tr")[1:]  # skip header row
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

                if batch_no not in seen_batches:
                    send_telegram_alert(batch_data)
                    seen_batches.add(batch_no)
                    newly_seen.add(batch_no)

        except Exception as e:
            print(f"Error querying {branch_name}: {e}")

    if newly_seen:
        save_seen_batches(seen_batches)
        print(f"Added {len(newly_seen)} new batches to tracking.")
    else:
        print("No new batches found across monitored branches.")

if __name__ == "__main__":
    main()
