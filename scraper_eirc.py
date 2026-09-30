import os
import re
import time
import json
import html
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
    "ASANSOL": "🚂 Asansol",
    "DURGAPUR": "🏭 Durgapur"
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

# Exact branch codes extracted from ICAI portal
BRANCHES_TO_CHECK = {
    "KOLKATA": "53",
    "BHUBANESWAR": "44",
    "CUTTACK": "45",
    "GUWAHATI": "47",
    "ROURKELA": "48",
    "SILIGURI": "50",
    "ASANSOL": "43",
    "DURGAPUR": "46",
    "SAMBALPUR": "49",
    "BRAHMAPUR": "271",
    "TINSUKIA": "244",
    "EIRC": "248"
}

# Pre-signed Eastern Region cryptographic tokens
FALLBACK_VIEWSTATE = (
    "/wEPDwUKMTY4OTkwNTY0MA9kFgICBA9kFgoCAw8WAh4HVmlzaWJsZWdkAgcPEA8WBh4NRGF0YVRleHRGaWVsZAULcmVnaW9uX25hbWUe"
    "DkRhdGFWYWx1ZUZpZWxkBQlyZWdpb25faWQeC18hRGF0YUJvdW5kZ2QQFQcGU2VsZWN0B0NlbnRyYWwHRWFzdGVybgdGb3JlaWduCE5v"
    "cnRoZXJuCFNvdXRoZXJuB1dlc3Rlcm4VBwZTZWxlY3QBNQExATYBMwE0ATIUKwMHZ2dnZ2dnZxYBAgJkAgsPEA8WBh8BBQticmFuY2hf"
    "bmFtZR8CBQlicmFuY2hfaWQfA2dkEBUMB0FTQU5TT0wLQkhVQkFORVNXQVIJQlJBSE1BUFVSB0NVVFRBQ0sIRFVSR0FQVVIERUlSQwhH"
    "VVdBSEFUSQdLT0xLQVRBCFJPVVJLRUxBCVNBTUJBTFBVUghTSUxJR1VSSQhUSU5TVUtJQRUMAjQzAjQ0AzI3MQI0NQI0NgMyNDgCNDcCNTMC"
    "NDgCNDkCNTADMjQ0FCsDDGdnZ2dnZ2dnZ2dnZ2RkAg8PEA8WBh8BBQtjb3Vyc2VfbmFtZR8CBQljb3Vyc2VfaWQfA2dkEBUFHEFkdmFu"
    "Y2VkIChJQ0lUU1MpIE1DUyBDb3Vyc2UmQWR2YW5jZWQgKElDSVRTUykgTUNTIENvdXJzZSAtIFdlZWtlbmQpQUlDSVRTUyAtIEFkdmFu"
    "Y2VkIEluZm9ybWF0aW9uIFRlY2hub2xvZ3kfSUNJVFNTIC0gSW5mb3JtYXRpb24gVGVjaG5vbG9neRtJQ0lUU1MgLSBPcmllbnRhdGlv"
    "biBDb3Vyc2UVBQI0NQI0OQI0OAI0NwI0NhQrAwVnZ2dnZ2RkAhMPZBYCZg9kFgICAQ88KwARAwAPFgQfA2ceC18hSXRlbUNvdW50AgZk"
    "ARAWAQIJFgE8KwAFAQAWAh8AaBYBAgYMFCsAABYCZg9kFhACAQ9kFhZmD2QWAgIBDw8WAh4EVGV4dAUVSUNJVFNTT0NfX0tPTEtBVEFf"
    "MTc5ZGQCAQ9kFgICAQ8PFgIfBQUBMWRkAgIPZBYCAgEPDxYCHwUFCjA2LzEwLzIwMjZkZAIDD2QWAgIBDw8WAh8FBQoyOC8xMC8yMDI2"
    "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"
)
FALLBACK_EVENTVALIDATION = (
    "/wEdABsBw6VmqCrf9crEi2nTHQ7NBlQi3z98kEUtu3eeY4Trat6exFmXkPdVcrOOeGjItwuyPnxUY8XnCNICH5i1DkmDXFPgpuH3lERe"
    "Dvg4F/RmT2b5xc52gpE9Izq5nWPtrGRQp2m7IlhPwdDibvoytWRumG9yZyRhUfRE4W6sWNNHnbU7cbYesaWJWhXAU382C3ntgNL+4p/A"
    "duL2BW78IuwvwsRhpxX4JzaE7aSKXrc5/xLy5w4Xu5MAv5cCZdhbEdoYPAl4zPqnBZJyzSRZ2mDC/03gWaYTkGKl5QQTjVa4lXcxSL/Z"
    "jxR0SmDNH5AGJA4kKEofgcJC0/kAeT1noS06Y/4arEL1H7h5ouScqVveajDSDAe2rz/Z5cTcMTXq6dXnKqiHkMOM8aHZFm+oRL2+S6yq"
    "sraNL6VFS/mZAsb02KloJbUOEFTcESxgIFrHhYyN/xiIHVeMzqkMy4GwJOSx0cUbK0TfCxtEsoeSAg7XeWHc7ncqrRg+FiLpBkcbDO8wr"
    "eDitKG6Ux59wHXBCphYfPdTtiwfZG04Ub7pO+qXUp2dVZ+AxxaNIFTi790Uou0jyUs18EfcRpJzvL750D0sHCYAa9J0sxTK1vFD4heU+g=="
)

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

def get_or_create_topic(group_id, tier, topic_name, topics_map, force_refresh=False):
    tier_key = tier.upper()
    if tier_key not in topics_map:
        topics_map[tier_key] = {}

    if not force_refresh and topic_name in topics_map[tier_key]:
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
            print(f"[{tier}] Created/restored topic: '{topic_name}' in group {group_id} (ID: {thread_id})")
            time.sleep(1.0)
            return thread_id
        else:
            print(f"Failed to create topic '{topic_name}' in group {group_id}: {data}")
            return None
    except Exception as e:
        print(f"Error creating topic '{topic_name}': {e}")
        return None

def send_telegram_alert(batch, course, group_id, tier, topic_title, topics_map, max_retries=3):
    if not BOT_TOKEN or not group_id:
        return False

    thread_id = get_or_create_topic(group_id, tier, topic_title, topics_map)

    text = (
        f"{course['icon']} <b>[EIRC] New ICAI {html.escape(course['name'])} Batch!</b>\n\n"
        f"📍 <b>Centre:</b> {html.escape(batch['pou'])}\n"
        f"🆔 <b>Batch Code:</b> <code>{html.escape(batch['batch_no'])}</code>\n"
        f"📅 <b>Dates:</b> {html.escape(batch['from_date'])} to {html.escape(batch['to_date'])}\n"
        f"⏰ <b>Timings:</b> {html.escape(batch['timings'])}\n"
        f"💺 <b>Available Seats:</b> {html.escape(str(batch['seats']))}\n"
        f"📌 <b>Status:</b> {html.escape(batch['status'])}\n\n"
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
                print(f"[Rate Limit] Pausing {wait_time + 1}s before retry...")
                time.sleep(wait_time + 1)
                continue

            if not res.ok:
                err_data = res.json()
                desc = err_data.get("description", "")
                print(f"Telegram API Error ({res.status_code}): {desc}")

                # Self-healing: if topic was deleted from Telegram, recreate on the fly
                if "message thread not found" in desc:
                    print(f"Rebuilding deleted topic '{topic_title}' and retrying delivery...")
                    thread_id = get_or_create_topic(group_id, tier, topic_title, topics_map, force_refresh=True)
                    if thread_id:
                        payload["message_thread_id"] = thread_id
                        res = requests.post(api_url, json=payload, timeout=10)
                        if res.ok:
                            print(f"[{course['name']}] Recovered alert for {batch['batch_no']} -> Topic: {thread_id}")
                            time.sleep(1.5)
                            return True

                res.raise_for_status()

            print(f"[{course['name']}] Sent alert for {batch['batch_no']} -> Group {group_id} (Topic: {thread_id})")
            time.sleep(1.5)
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

def query_portal(session, course_id, branch_code, viewstate, eventval, viewstategen="10EF2921"):
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
    post_headers = dict(HEADERS)
    post_headers["Content-Type"] = "application/x-www-form-urlencoded"
    return session.post(URL, data=payload, headers=post_headers, timeout=20)

def main():
    seen_batches = set(load_json(SEEN_DATA_FILE, []))
    topics_map = load_json(TOPICS_FILE, {"INTER": {}, "FINAL": {}})
    newly_seen = set()
    session = requests.Session()

    print("Fetching live session tokens from portal...")
    try:
        res = session.get(URL, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")
        vs_tag = soup.find("input", {"id": "__VIEWSTATE"})
        ev_tag = soup.find("input", {"id": "__EVENTVALIDATION"})
        gen_tag = soup.find("input", {"id": "__VIEWSTATEGENERATOR"})

        live_vs = vs_tag.get("value", "") if vs_tag else ""
        live_ev = ev_tag.get("value", "") if ev_tag else ""
        live_gen = gen_tag.get("value", "10EF2921") if gen_tag else "10EF2921"
    except Exception as e:
        print(f"Initial GET failed: {e}. Falling back to pre-signed tokens.")
        live_vs, live_ev, live_gen = "", "", "10EF2921"

    for course in COURSES_TO_CHECK:
        print(f"\n================ Scanning EIRC [{course['tier']}]: {course['name']} ================")
        for branch_name, branch_code in BRANCHES_TO_CHECK.items():
            try:
                table = None
                if live_vs and live_ev:
                    res = query_portal(session, course["id"], branch_code, live_vs, live_ev, live_gen)
                    if res.status_code == 200:
                        table = find_batch_table(BeautifulSoup(res.text, "html.parser"))

                if not table:
                    res = query_portal(session, course["id"], branch_code, FALLBACK_VIEWSTATE, FALLBACK_EVENTVALIDATION, "10EF2921")
                    if res.status_code == 200:
                        table = find_batch_table(BeautifulSoup(res.text, "html.parser"))

                if not table:
                    continue

                batches = parse_batches(table)
                unseen_batches = [b for b in batches if b["batch_no"] not in seen_batches]

                if not unseen_batches:
                    continue

                print(f"[{course['name']}] {branch_name.ljust(15)} -> {len(unseen_batches)} NEW BATCHES TO ALERT")

                clean_name = branch_name.strip().upper()
                topic_title = HIGH_DENSITY_BRANCHES.get(clean_name, CATCH_ALL_TOPIC_NAME)

                for b in unseen_batches:
                    if send_telegram_alert(b, course, course["group_id"], course["tier"], topic_title, topics_map):
                        seen_batches.add(b["batch_no"])
                        newly_seen.add(b["batch_no"])

            except Exception as e:
                print(f"Error querying {course['name']} @ {branch_name}: {e}")

    if newly_seen:
        save_json(SEEN_DATA_FILE, sorted(list(seen_batches)))
        print(f"\n[EIRC] Run complete: recorded and alerted {len(newly_seen)} new batches.")
    else:
        print("\n[EIRC] Run complete: scan finished cleanly (no new batches).")

if __name__ == "__main__":
    main()
