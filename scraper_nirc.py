import os
import re
import time
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup

URL = "https://www.icaionlineregistration.org/launchbatchdetail.aspx"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SEEN_DATA_FILE = "seen_batches_nirc.json"
TOPICS_FILE = "topics_nirc.json"

# --- INSERT YOUR NIRC TELEGRAM GROUP IDs HERE ---
# (Can be the same group ID for testing, or separate groups for Inter & Final)
GROUP_INTER_ID = -1004425118828  
GROUP_FINAL_ID = -1003702612974  

# Dedicated high-density topics (all others route to 'Other NIRC Branches')
HIGH_DENSITY_BRANCHES = {
    "HIMACHAL PRADESH": "🏔️ Himachal Pradesh",
    "DELHI": "🏢 Delhi",
    "CHANDIGARH": "🏛️ Chandigarh",
    "GURUGRAM": "🏙️ Gurugram",
    "FARIDABAD": "🏭 Faridabad",
    "LUDHIANA": "🧵 Ludhiana",
    "AMRITSAR": "🛕 Amritsar",
    "JALANDHAR": "⚽ Jalandhar",
    "JAMMU & KASHMIR": "❄️ Jammu & Kashmir",
    "KARNAL": "🌾 Karnal",
    "ROHTAK": "🏫 Rohtak",
    "PANIPAT": "🧶 Panipat"
}
CATCH_ALL_TOPIC_NAME = "📍 Other NIRC Branches"

COURSES_TO_CHECK = [
    # ICITSS -> Inter
    {"id": "46", "name": "Orientation Course (OC)", "tier": "INTER", "group_id": GROUP_INTER_ID, "icon": "🎓"},
    {"id": "47", "name": "Information Technology (ITT)", "tier": "INTER", "group_id": GROUP_INTER_ID, "icon": "💻"},
    
    # AICITSS -> Final
    {"id": "48", "name": "Advanced ITT", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "⚡"},
    {"id": "45", "name": "MCS Course (GMCS)", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "👔"},
    {"id": "49", "name": "MCS Course (Weekend)", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "👔"}
]

REGION_ID = "3"  # Northern Region

BRANCHES_TO_CHECK = {
    "DELHI": "254",
    "CHANDIGARH": "19",
    "GURUGRAM": "21",
    "FARIDABAD": "20",
    "LUDHIANA": "26",
    "AMRITSAR": "17",
    "JALANDHAR": "14",
    "AMBALA": "16",
    "BHATINDA": "18",
    "BHIWANI": "278",
    "BAHADURGARH": "272",
    "HIMACHAL PRADESH": "22",
    "HISAR": "23",
    "JAMMU & KASHMIR": "24",
    "KARNAL": "25",
    "KURUKSHETRA": "277",
    "PANIPAT": "28",
    "PATIALA": "27",
    "REWARI": "33",
    "ROHTAK": "29",
    "SANGRUR": "30",
    "SIRSA": "34",
    "SONEPAT": "31",
    "YAMUNANAGAR": "32"
}

FALLBACK_VIEWSTATE = urllib.parse.unquote(
    "%2FwEPDwUKMTY4OTkwNTY0MA9kFgICBA9kFgoCAw8WAh4HVmlzaWJsZWdkAgcPEA8WBh4NRGF0YVRleHRGaWVsZAULcmVnaW9uX25hbWUeDkRhdGFWYWx1ZUZpZWxkBQlyZWdpb25faWQeC18hRGF0YUJvdW5kZ2QQFQcGU2VsZWN0B0NlbnRyYWwHRWFzdGVybgdGb3JlaWduCE5vcnRoZXJuCFNvdXRoZXJuB1dlc3Rlcm4VBwZTZWxlY3QBNQExATYBMwE0ATIUKwMHZ2dnZ2dnZxYBAgRkAgsPEA8WBh8BBQticmFuY2hfbmFtZR8CBQlicmFuY2hfaWQfA2dkEBUYBkFNQkFMQQhBTVJJVFNBUgtCYWhhZHVyZ2FyaAhCaGF0aW5kYQdCSElXQU5JCkNIQU5ESUdBUkgFREVMSEkJRkFSSURBQkFECEd1cnVncmFtEEhJTUFDSEFMIFBSQURFU0gFSElTQVIJSkFMQU5ESEFSDUphbW11Jkthc2htaXIGS0FSTkFMC0t1cnVrc2hldHJhCExVREhJQU5BB1BBTklQQVQHUEFUSUFMQQZSRVdBUkkGUk9IVEFLB1NBTkdSVVIFU0lSU0EHU09ORVBBVAtZQU1VTkFOQUdBUhUYAjE2AjE3AzI3MgIxOAMyNzgCMTkDMjU0AjIwAjIxAjIyAjIzAjE0AjI0AjI1AzI3NwIyNgIyOAIyNwIzMwIyOQIzMAIzNAIzMQIzMhQrAxhnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dkZAIPDxAPFgYfAQULY291cnNlX25hbWUfAgUJY291cnNlX2lkHwNnZBAVBRxBZHZhbmNlZCAoSUNJVFNTKSBNQ1MgQ291cnNlJkFkdmFuY2VkIChJQ0lUU1MpIE1DUyBDb3Vyc2UgLSBXZWVrZW5kKUFJQ0lUU1MgLSBBZHZhbmNlZCBJbmZvcm1hdGlvbiBUZWNobm9sb2d5H0lDSVRTUyAtIEluZm9ybWF0aW9uIFRlY2hub2xvZ3kbSUNJVFNTIC0gT3JpZW50YXRpb24gQ291cnNlFQUCNDUCNDkCNDgCNDcCNDYUKwMFZ2dnZ2dkZAITD2QWAmYPZBYCAgEPPCsAEQIBEBYAFgAWAAwUKwAAZBgBBQlHcmlkVmlldzEPZ2S9EC9W9lwOJFL%2FPOY%2BW1%2BC0tTyogCGrFqqtbTQhPZDOA%3D%3D"
)
FALLBACK_EVENTVALIDATION = urllib.parse.unquote(
    "%2FwEdACdtJlGxILTIqjAlm%2FubZNQYBlQi3z98kEUtu3eeY4Trat6exFmXkPdVcrOOeGjItwuyPnxUY8XnCNICH5i1DkmDXFPgpuH3lEReDvg4F%2FRmT2b5xc52gpE9Izq5nWPtrGRQp2m7IlhPwdDibvoytWRumG9yZyRhUfRE4W6sWNNHnbU7cbYesaWJWhXAU382C3mffdNPt7G97XzuvLC3pgO%2Bf5r4zuzY1%2BI4IOsX7n%2Fgm62MgvOqjvmBFLE3Fu7D0kTgValH0KNnMZNDfY%2Bgc11uT1B8beu9Xuih4VQ%2FRcDMeW91W6bk0m9LgmzdroYVw98zArUB0FZfGCzcx2R9vdismAW2KkmmvRvWLyuFFNfDaH4aDGJNeGZpjY7%2BSt5quKtH8fJRNtif4VJvLCHr0fvrO9L2lXyBrH8va6VXydAo4Qj%2FaGg2KKw%2FTwAn3hy6JUQImsmxJWW%2FROt5NUvup4%2FXlW4TBWDBhGcBf1TTA5oF%2BUwntHQTzzYaFv5PW1bR5RJPnBoCK26PmctL%2B3KVAcsIWPey1bwufGvvMAdUffLE3cU78dXNwx5fL5heEd7XXtj%2FGMWmEjC11DdBpm%2FotuGDXQWZVkFozyqCoyvtiueutWbT68pekcf6y9t8iu0bfdrzXbDPwJfD%2Fi7ffrd6fTlHBDNr8J5BXrTRmVliLuOx7wbrpmr8zfE5YXFmQlMRvfON%2FxiIHVeMzqkMy4GwJOSx0cUbK0TfCxtEsoeSAg7XeWHc7ncqrRg%2BFiLpBkcbDO8wreDitKG6Ux59wHXBCphYfPdTtiwfZG04Ub7pO%2BqXUp2dVZ%2BAxxaNIFTi790Uou343WyvsxpPvq%2FtihCzO1o53xGaklGO6qhLUAZhZDs5FA%3D%3D"
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

def get_or_create_topic(group_id, topic_name, topics_map):
    group_key = str(group_id)
    if group_key not in topics_map:
        topics_map[group_key] = {}

    # Check cache by group ID
    if topic_name in topics_map[group_key]:
        return topics_map[group_key][topic_name]

    if not BOT_TOKEN:
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
            topics_map[group_key][topic_name] = thread_id
            save_json(TOPICS_FILE, topics_map)
            print(f"Created topic: '{topic_name}' in group {group_id} (Thread: {thread_id})")
            time.sleep(1.0)
            return thread_id
        else:
            print(f"Failed to create topic '{topic_name}' in group {group_id}: {data}")
            return None
    except Exception as e:
        print(f"Error creating topic '{topic_name}': {e}")
        return None

def send_telegram_alert(batch, course, group_id, thread_id, max_retries=3):
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is not set.")
        return False

    text = (
        f"{course['icon']} <b>[NIRC] New ICAI {course['name']} Batch!</b>\n\n"
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
                print(f"[Rate Limit] Pausing {wait_time + 1}s before retry...")
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
    topics_map = load_json(TOPICS_FILE, {})
    newly_seen = set()
    session = requests.Session()

    print("Fetching fresh session tokens from portal...")
    try:
        res = session.get(URL, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")

        vs = soup.find("input", {"id": "__VIEWSTATE"})
        ev = soup.find("input", {"id": "__EVENTVALIDATION"})
        gen = soup.find("input", {"id": "__VIEWSTATEGENERATOR"})

        live_vs = vs.get("value", "") if vs else ""
        live_ev = ev.get("value", "") if ev else ""
        live_gen = gen.get("value", "10EF2921") if gen else "10EF2921"
    except Exception as e:
        print(f"Initial get request failed: {e}. Falling back to saved tokens.")
        live_vs, live_ev, live_gen = "", "", "10EF2921"

    for course in COURSES_TO_CHECK:
        print(f"\n================ Scanning NIRC [{course['tier']}]: {course['name']} ================")
        for branch_name, branch_code in BRANCHES_TO_CHECK.items():
            try:
                table = None
                if live_vs and live_ev:
                    post_res = query_portal(session, course["id"], branch_code, live_vs, live_ev, live_gen)
                    table = find_batch_table(BeautifulSoup(post_res.text, "html.parser"))

                if not table:
                    post_res = query_portal(
                        session, course["id"], branch_code, FALLBACK_VIEWSTATE, FALLBACK_EVENTVALIDATION, "10EF2921"
                    )
                    table = find_batch_table(BeautifulSoup(post_res.text, "html.parser"))

                if not table:
                    continue

                batches = parse_batches(table)

                # Fetch or create topic (keyed by group ID)
                topic_title = HIGH_DENSITY_BRANCHES.get(branch_name, CATCH_ALL_TOPIC_NAME)
                thread_id = get_or_create_topic(course["group_id"], topic_title, topics_map)

                for b in batches:
                    if b["batch_no"] not in seen_batches:
                        if send_telegram_alert(b, course, course["group_id"], thread_id):
                            seen_batches.add(b["batch_no"])
                            newly_seen.add(b["batch_no"])

            except Exception as e:
                print(f"Error querying {course['name']} @ {branch_name}: {e}")

    if newly_seen:
        save_json(SEEN_DATA_FILE, sorted(list(seen_batches)))
        print(f"\n[NIRC] Run complete: recorded {len(newly_seen)} new batches.")
    else:
        print("\n[NIRC] Run complete: no new batches detected.")

if __name__ == "__main__":
    main()
   
