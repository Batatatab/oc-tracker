import os
import re
import time
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup

URL = "https://www.icaionlineregistration.org/launchbatchdetail.aspx"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SEEN_DATA_FILE = "seen_batches_eirc.json"
TOPICS_FILE = "topics_eirc.json"

# Telegram Supergroup Chat IDs for EIRC
GROUP_INTER_ID = -1004354982130
GROUP_FINAL_ID = -1004224921246

# High-density focus branches in Eastern Region
HIGH_DENSITY_BRANCHES = {
    "KOLKATA": "🏢 Kolkata",
    "BHUBANESWAR": "🏛️ Bhubaneswar",
    "GUWAHATI": "🌿 Guwahati",
    "SILIGURI": "🏔️ Siliguri",
    "CUTTACK": "🏰 Cuttack",
    "ROURKELA": "🏭 Rourkela",
    "ASANSOL": "🚂 Asansol"
}
CATCH_ALL_TOPIC_NAME = "📍 Other EIRC Branches"

COURSES_TO_CHECK = [
    # ICITSS -> Inter Group
    {"id": "46", "name": "Orientation Course (OC)", "tier": "INTER", "group_id": GROUP_INTER_ID, "icon": "🎓"},
    {"id": "47", "name": "Information Technology (ITT)", "tier": "INTER", "group_id": GROUP_INTER_ID, "icon": "💻"},
    
    # AICITSS -> Final Group
    {"id": "48", "name": "Advanced ITT", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "⚡"},
    {"id": "45", "name": "MCS Course (GMCS)", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "👔"},
    {"id": "49", "name": "MCS Course (Weekend)", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "👔"}
]

REGION_ID = "1"  # Eastern Region

FALLBACK_BRANCHES = {
    "KOLKATA": "1",
    "BHUBANESWAR": "2",
    "CUTTACK": "3",
    "GUWAHATI": "4",
    "ROURKELA": "5",
    "SILIGURI": "6",
    "ASANSOL": "7",
    "SAMBALPUR": "8",
    "RANIGANJ": "9",
    "BRAHMAPUR": "10",
    "DIBRUGARH": "11",
    "TINSUKIA": "12"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Origin": "https://www.icaionlineregistration.org",
    "Referer": "https://www.icaionlineregistration.org/launchbatchdetail.aspx",
}

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def get_or_create_topic(group_id, tier, topic_name, topics_map):
    tier_key = tier.upper()
    if tier_key not in topics_map:
        topics_map[tier_key] = {}

    if topic_name in topics_map[tier_key]:
        return topics_map[tier_key][topic_name]

    if not BOT_TOKEN or not group_id:
        return None

    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/createForumTopic"
    payload = {
        "chat_id": group_id,
        "name": topic_name
    }

    try:
        res = requests.post(api_url, json=payload, timeout=10)
        data = res.json()
        if data.get("ok"):
            thread_id = data["result"]["message_thread_id"]
            topics_map[tier_key][topic_name] = thread_id
            save_json(TOPICS_FILE, topics_map)
            print(f"[{tier}] Created topic: '{topic_name}' in group {group_id} (ID: {thread_id})")
            time.sleep(1.0)
            return thread_id
        else:
            print(f"Failed to create topic '{topic_name}' in group {group_id}: {data}")
            return None
    except Exception as e:
        print(f"Error creating topic '{topic_name}': {e}")
        return None

def send_telegram_alert(batch, course, group_id, thread_id, max_retries=3):
    if not BOT_TOKEN or not group_id:
        return False

    text = (
        f"{course['icon']} <b>[EIRC] New ICAI {course['name']} Batch!</b>\n\n"
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
        "chat_id": group_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if thread_id:
        payload["message_thread_id"] = thread_id

    for attempt in range(max_retries):
        try:
            res = requests.post(api_url, json=payload, timeout=10)
            if res.status_code == 429:
                wait_time = 5
                try:
                    wait_time = res.json().get("parameters", {}).get("retry_after", 5)
                except Exception:
                    pass
                time.sleep(wait_time + 1)
                continue

            res.raise_for_status()
            print(f"[{course['name']}] Sent alert for {batch['batch_no']} -> Group {group_id} (Topic: {thread_id})")
            time.sleep(2.0)
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {batch['batch_no']}: {e}")
            time.sleep(2.0)

    return False

def find_batch_table(soup):
    for table in soup.find_all("table"):
        text = table.text
        if "Batch No" in text and "Available Seats" in text:
            return table
    return None

def parse_batches(table):
    results = []
    rows = table.find_all("tr")
    for row in rows:
        cols = [c.text.strip() for c in row.find_all("td")]
        if len(cols) >= 6 and "Batch No" not in cols[0]:
            batch_data = {
                "batch_no": cols[0],
                "seats": cols[1],
                "from_date": cols[2],
                "to_date": cols[3],
                "timings": cols[4],
                "pou": cols[5],
                "status": cols[10] if len(cols) > 10 else "Open"
            }
            if batch_data["batch_no"]:
                results.append(batch_data)
    return results

def get_live_eirc_branches(session, vs, ev, gen):
    payload = {
        "__EVENTTARGET": "ddl_reg",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": vs,
        "__VIEWSTATEGENERATOR": gen,
        "__SCROLLPOSITIONX": "0",
        "__SCROLLPOSITIONY": "0",
        "__EVENTVALIDATION": ev,
        "ddl_reg": REGION_ID,
        "ddlPou": "Select",
        "ddl_course": "Select"
    }
    try:
        r = session.post(URL, data=payload, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        pou_select = soup.find("select", {"id": "ddlPou"})
        branches = {}
        if pou_select:
            for opt in pou_select.find_all("option"):
                val = opt.get("value", "").strip()
                name = opt.text.strip()
                if val and val.lower() != "select":
                    clean_name = re.sub(r'[^a-zA-Z\s]', '', name).strip().upper()
                    branches[clean_name] = val
        if branches:
            print(f"Discovered {len(branches)} live branches for EIRC from portal.")
            return branches, soup
    except Exception as e:
        print(f"Error fetching live EIRC branches: {e}")
    return FALLBACK_BRANCHES, None

def query_portal(session, course_id, branch_code, viewstate, eventval, viewstategen):
    payload = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": viewstategen,
        "__SCROLLPOSITIONX": "0",
        "__SCROLLPOSITIONY": "0",
        "__EVENTVALIDATION": eventval,
        "ddl_reg": REGION_ID,
        "ddlPou": branch_code,
        "ddl_course": course_id,
        "btn_getlist": "Get List"
    }
    return session.post(URL, data=payload, headers=HEADERS, timeout=20)

def main():
    seen_batches = set(load_json(SEEN_DATA_FILE, []))
    topics_map = load_json(TOPICS_FILE, {"INTER": {}, "FINAL": {}})
    newly_seen = set()
    session = requests.Session()

    print("Fetching initial session tokens from portal...")
    try:
        res = session.get(URL, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        live_vs = soup.find("input", {"id": "__VIEWSTATE"}).get("value", "")
        live_ev = soup.find("input", {"id": "__EVENTVALIDATION"}).get("value", "")
        live_gen = soup.find("input", {"id": "__VIEWSTATEGENERATOR"}).get("value", "10EF2921")
    except Exception as e:
        print(f"Initial get request failed: {e}")
        return

    branches_to_check, postback_soup = get_live_eirc_branches(session, live_vs, live_ev, live_gen)
    if postback_soup:
        try:
            live_vs = postback_soup.find("input", {"id": "__VIEWSTATE"}).get("value", live_vs)
            live_ev = postback_soup.find("input", {"id": "__EVENTVALIDATION"}).get("value", live_ev)
            live_gen = postback_soup.find("input", {"id": "__VIEWSTATEGENERATOR"}).get("value", live_gen)
        except Exception:
            pass

    for course in COURSES_TO_CHECK:
        print(f"\n================ Scanning EIRC [{course['tier']}]: {course['name']} ================")
        for branch_name, branch_code in branches_to_check.items():
            try:
                res = query_portal(session, course["id"], branch_code, live_vs, live_ev, live_gen)
                table = find_batch_table(BeautifulSoup(res.text, "html.parser"))
                if not table:
                    continue

                batches = parse_batches(table)

                topic_title = HIGH_DENSITY_BRANCHES.get(branch_name, CATCH_ALL_TOPIC_NAME)
                thread_id = get_or_create_topic(course["group_id"], course["tier"], topic_title, topics_map)

                for b in batches:
                    if b["batch_no"] not in seen_batches:
                        if send_telegram_alert(b, course, course["group_id"], thread_id):
                            seen_batches.add(b["batch_no"])
                            newly_seen.add(b["batch_no"])
            except Exception as e:
                print(f"Error querying {course['name']} @ {branch_name}: {e}")

    if newly_seen:
        save_json(SEEN_DATA_FILE, sorted(list(seen_batches)))
        print(f"\n[EIRC] Run complete: recorded {len(newly_seen)} new batches.")
    else:
        print("\n[EIRC] Run complete: no new batches detected.")

if __name__ == "__main__":
    main()
