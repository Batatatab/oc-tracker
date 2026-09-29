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

BRANCHES_TO_CHECK = {
    "JALGAON": "68",
    "PUNE": "77",
    "MUMBAI": "255",
    "NASHIK": "74",
    "AHMEDABAD": "56"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Origin": "https://www.icaionlineregistration.org",
    "Referer": "https://www.icaionlineregistration.org/launchbatchdetail.aspx",
}

def extract_form_fields(soup):
    """Extracts all current hidden inputs and default select values from the page."""
    data = {}
    for inp in soup.find_all("input"):
        name = inp.get("name")
        if name:
            data[name] = inp.get("value", "")
            
    for sel in soup.find_all("select"):
        name = sel.get("name")
        if name:
            selected_opt = sel.find("option", selected=True) or sel.find("option")
            data[name] = selected_opt.get("value", "") if selected_opt else ""
            
    return data

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

    print("Step 1: Loading initial page...")
    res = session.get(URL, headers=HEADERS, timeout=20)
    if res.status_code != 200:
        print(f"Failed to load page. HTTP Status: {res.status_code}")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    form_data = extract_form_fields(soup)

    if "__VIEWSTATE" not in form_data:
        print("Failed to find __VIEWSTATE on initial load.")
        return

    print("Step 2: Selecting Western Region...")
    form_data["__EVENTTARGET"] = "ddl_reg"
    form_data["__EVENTARGUMENT"] = ""
    form_data["ddl_reg"] = REGION_ID
    # Remove submit button when triggering a dropdown change postback
    form_data.pop("btn_getlist", None)

    res_reg = session.post(URL, data=form_data, headers=HEADERS, timeout=20)
    if res_reg.status_code != 200:
        print(f"Region postback failed. HTTP Status: {res_reg.status_code}")
        return

    soup_reg = BeautifulSoup(res_reg.text, "html.parser")
    reg_form = extract_form_fields(soup_reg)

    if "__VIEWSTATE" not in reg_form:
        print("Failed to capture updated VIEWSTATE after selecting region.")
        return

    print("Step 3: Western Region state ready. Querying branches...")
    reg_form["__EVENTTARGET"] = ""
    reg_form["__EVENTARGUMENT"] = ""
    reg_form["ddl_reg"] = REGION_ID
    reg_form["ddl_course"] = COURSE_ID
    reg_form["btn_getlist"] = "Get List"

    for branch_name, branch_code in BRANCHES_TO_CHECK.items():
        payload = reg_form.copy()
        payload["ddlPou"] = branch_code

        try:
            post_res = session.post(URL, data=payload, headers=HEADERS, timeout=20)
            branch_soup = BeautifulSoup(post_res.text, "html.parser")
            
            # Match GridView table or any table containing "Batch No"
            table = branch_soup.find("table", id=re.compile(r"gridview", re.I))
            if not table:
                for t in branch_soup.find_all("table"):
                    if "Batch No" in t.text:
                        table = t
                        break

            if not table:
                print(f"[{branch_name}] No batches listed.")
                continue

            rows = table.find_all("tr")[1:]  # skip table headers
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
        print(f"Successfully processed and recorded {len(newly_seen)} new batches.")
    else:
        print("Scan finished. No new batches detected.")

if __name__ == "__main__":
    main()
