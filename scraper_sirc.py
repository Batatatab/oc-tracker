import os
import re
import time
import json
import html
import requests
from bs4 import BeautifulSoup

URL = "https://www.icaionlineregistration.org/launchbatchdetail.aspx"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SEEN_DATA_FILE = "seen_batches_sirc.json"
TOPICS_FILE = "topics_sirc.json"

# SIRC Telegram Supergroup Chat IDs
GROUP_INTER_ID = -1004454612113
GROUP_FINAL_ID = -1004446662940

# Dedicated high-density topics
HIGH_DENSITY_BRANCHES = {
    "CHENNAI": "🏛️ Chennai",
    "BENGALURU": "💻 Bengaluru",
    "HYDERABAD": "🏙️ Hyderabad",
    "COIMBATORE": "🏭 Coimbatore",
    "ERNAKULAM": "🚢 Ernakulam (Kochi)",
    "VISAKHAPATNAM": "🌊 Visakhapatnam",
    "VIJAYAWADA": "🌾 Vijayawada",
    "MADURAI": "🛕 Madurai",
    "THIRUVANANTHAPURAM": "🌴 Thiruvananthapuram",
    "KOZHIKODE": "☕ Kozhikode",
    "MYSURU": "🏰 Mysuru",
    "TIRUPATI": "🙏 Tirupati"
}
CATCH_ALL_TOPIC_NAME = "📍 Other SIRC Branches"

COURSES_TO_CHECK = [
    # ICITSS -> Inter Group
    {"id": "46", "name": "Orientation Course (OC)", "tier": "INTER", "group_id": GROUP_INTER_ID, "icon": "🎓"},
    {"id": "47", "name": "Information Technology (ITT)", "tier": "INTER", "group_id": GROUP_INTER_ID, "icon": "💻"},
    
    # AICITSS -> Final Group
    {"id": "48", "name": "Advanced ITT", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "⚡"},
    {"id": "45", "name": "MCS Course (GMCS)", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "👔"},
    {"id": "49", "name": "MCS Course (Weekend)", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "👔"}
]

REGION_ID = "4"  # Southern Region

BRANCHES_TO_CHECK = {
    "CHENNAI": "138",
    "BENGALURU": "102",
    "HYDERABAD": "111",
    "COIMBATORE": "106",
    "ERNAKULAM": "107",
    "VISAKHAPATNAM": "136",
    "VIJAYAWADA": "135",
    "MADURAI": "116",
    "THIRUVANANTHAPURAM": "131",
    "KOZHIKODE": "105",
    "MYSURU": "118",
    "TIRUPATI": "128",
    "ALAPPUZHA": "101",
    "ANANTAPUR": "260",
    "BALLARI": "104",
    "BELAGAVI": "103",
    "CHENGALPATTU": "268",
    "ERODE": "252",
    "GUNTUR": "109",
    "HUBBALLI": "110",
    "KADAPA": "279",
    "KAKINADA": "112",
    "KALABURGI": "273",
    "KANNUR": "113",
    "KARIMNAGAR": "258",
    "KOLLAM": "122",
    "KOTTAYAM": "114",
    "KUMBAKONAM": "115",
    "KURNOOL": "245",
    "MANGALURU": "117",
    "NELLORE": "119",
    "ONGOLE": "259",
    "PALAKKAD": "120",
    "PUDUCHERRY": "121",
    "RAJAMAHENDRAVARAM": "123",
    "SALEM": "124",
    "SIRC": "251",
    "SIVAKASI": "125",
    "THOOTHUKUDI": "132",
    "THRISSUR": "130",
    "TIRUCHIRAPALLI": "126",
    "TIRUNELVELI": "127",
    "TIRUPUR": "129",
    "UDUPI": "133",
    "VELLORE": "134",
    "WARANGAL": "246",
    "WEST GODAVARI": "281"
}

# Bit-for-bit uncorrupted Southern Region ViewState
SIRC_VIEWSTATE = """/wEPDwUKMTY4OTkwNTY0MA9kFgICBA9kFgoCAw8WAh4HVmlzaWJsZWdkAgcPEA8WBh4NRGF0YVRleHRGaWVsZAULcmVnaW9uX25hbWUeDkRhdGFWYWx1ZUZpZWxkBQlyZWdpb25faWQeC18hRGF0YUJvdW5kZ2QQFQcGU2VsZWN0B0NlbnRyYWwHRWFzdGVybgdGb3JlaWduCE5vcnRoZXJuCFNvdXRoZXJuB1dlc3Rlcm4VBwZTZWxlY3QBNQExATYBMwE0ATIUKwMHZ2dnZ2dnZxYBAgVkAgsPEA8WBh8BBQticmFuY2hfbmFtZR8CBQlicmFuY2hfaWQfA2dkEBUvCUFsYXBwdXpoYQlBbmFudGFwdXIHQmFsbGFyaQhCZWxhZ2F2aQlCRU5HQUxVUlUMQ2hlbmdhbHBhdHR1B0NIRU5OQUkKQ09JTUJBVE9SRQlFUk5BS1VMQU0FRVJPREUGR1VOVFVSCEhVQkJBTExJCUhZREVSQUJBRAZLQURBUEEIS0FLSU5BREEJS2FsYWJ1cmdpBktBTk5VUgpLQVJJTU5BR0FSBktvbGxhbQhLT1RUQVlBTQlLb3poaWtvZGUKS1VNQkFLT05BTQdLVVJOT09MB01BRFVSQUkJTWFuZ2FsdXJ1Bk15c3VydQdORUxMT1JFBk9OR09MRQhQYWxha2thZApQVURVQ0hFUlJZEVJBSkFNQUhFTkRSQVZBUkFNBVNBTEVNBFNJUkMIU0lWQUtBU0kSVGhpcnV2YW5hbnRoYXB1cmFtC1Rob290aHVrdWRpCFRocmlzc3VyDlRpcnVjaGlyYXBhbGxpC1RJUlVORUxWRUxJCFRJUlVQQVRJB1RJUlVQVVIFVURVUEkHVkVMTE9SRQpWSUpBWUFXQURBDVZJU0FLSEFQQVROQU0IV0FSQU5HQUwNV2VzdCBHb2RhdmFyaRUvAzEwMQMyNjADMTA0AzEwMwMxMDIDMjY4AzEzOAMxMDYDMTA3AzI1MgMxMDkDMTEwAzExMQMyNzkDMTEyAzI3MwMxMTMDMjU4AzEyMgMxMTQDMTA1AzExNQMyNDUDMTE2AzExNwMxMTgDMTE5AzI1OQMxMjADMTIxAzEyMwMxMjQDMjUxAzEyNQMxMzEDMTMyAzEzMAMxMjYDMTI3AzEyOAMxMjkDMTMzAzEzNAMxMzUDMTM2AzI0NgMyODEUKwMvZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dkZAIPDxAPFgYfAQULY291cnNlX25hbWUfAgUJY291cnNlX2lkHwNnZBAVBRxBZHZhbmNlZCAoSUNJVFNTKSBNQ1MgQ291cnNlJkFkdmFuY2VkIChJQ0lUU1MpIE1DUyBDb3Vyc2UgLSBXZWVrZW5kKUFJQ0lUU1MgLSBBZHZhbmNlZCBJbmZvcm1hdGlvbiBUZWNobm9sb2d5H0lDSVRTUyAtIEluZm9ybWF0aW9uIFRlY2hub2xvZ3kbSUNJVFNTIC0gT3JpZW50YXRpb24gQ291cnNlFQUCNDUCNDkCNDgCNDcCNDYUKwMFZ2dnZ2dkZAITD2QWAmYPZBYCAgEPPCsAEQMADxYEHwNnHgtfIUl0ZW1Db3VudGZkARAWAQIJFgE8KwAFAQAWAh8AaBYBAgYMFCsAAGQYAQUJR3JpZFZpZXcxDzwrAAwBCGZknb6lTo0j2DhVQ30COuTYIYvhuQPFt2h5ri6WsjILD4o=""".strip()

# Bit-for-bit uncorrupted Southern Region EventValidation
SIRC_EVENTVALIDATION = """/wEdAD5/e2jEPM/ZRHYzXC/qnjolBlQi3z98kEUtu3eeY4Trat6exFmXkPdVcrOOeGjItwuyPnxUY8XnCNICH5i1DkmDXFPgpuH3lEReDvg4F/RmT2b5xc52gpE9Izq5nWPtrGRQp2m7IlhPwdDibvoytWRumG9yZyRhUfRE4W6sWNNHnbU7cbYesaWJWhXAU382C3nK1uKYS3Gi68/4c2xMtrvuObZcupe3bd4w1MvO+ZC7Yp126uGiE2JuyBo5cwQP0Gu7cSOL3+udQ2TBIOQOSLAdGbB9cfaCVQZ86pVUr60JPjq7z0Qvp5hPrVt2vxmMHla53DJZQqagnF0mlbmz4Ka9Luo5RIwcyTTFd6THEIdMlUF9NBk+DuecPl6fd0wZpCR/mYsq5yYAazieHNbKobJAzynfIPAYQXqgZ7gHmahmhg5RsmyVw54jbEUdxNoyDeqI0in9bFSYGcH89WBqb8/wbas6eXwU3tBBycFDHdquZe7suztI+tny0668pnqNMv01hlQubnErvO0pe2kq9oPuJUmSVlCThqGli3RMjglnvPXcztUYLKThCC15lHRaa7L8mMesddC9tYybJs3JOkIo4dcX/cUooiVp6MOjyi+/susmlZ81h0Trw25UBaxWuB4C5dE5hPWRbJgnN8wyr6P2iJFECo00p/9qP+mnBDa2oYeP8AQgsCz+/VAhClZ1ZExnKHQKlIEMuFR/8ZprOzsqaieS9qq0W3ucL/Kk6zhIkBzce2lWFtIfkXnjl61s1Qhj34CeJky0YAcMFYl70ApQZp4py2mFabGohSQ5mZu4azk+k1Fb2waK8Sif78/4FpdqajnrnWt28Z54bncjAFwJGU7UUEIhvTiLhpeB6CyEvOKBGMvxBHc8Q6EKvWj5Oh8Yp3f1/ecSc9+ASFYYYh6XBViwl/E37a6jw3mAUZcM1ZAKtTrJHMVCi2elio1TXDycnolUflm6rnDyuQD5fNaPzr1kn5pjIyrG5TPIjcqvAvY3Gw66Uk79WV0zCK2tysM2c7zi2zLuqXEuNLHxpUYobghHth7CZhkwJ/cCqopp/zBI57I60ZH4tmKnLGHog/xDYz6VkmtiHo52Y7icSgI7Bag8q5TNZyHxSvi+gnbqrVBKg4kMoun+wl9MPMqJaAdO5Rq3JszBCXUiJtuqk1xUKLeArIVMQI3+3K8EA6D73Y3/GIgdV4zOqQzLgbAk5LHRxRsrRN8LG0Syh5ICDtd5YdzudyqtGD4WIukGRxsM7zCt4OK0obphfn3AdcEKmFh891O2LB9kbThRvuk76pdSnZ1Vn4DHFo0gVOLv3RSi7TbSIs4gM1Ewq4gdOwiIcvJHBlwKOPzTmNSCDCzQXGMF""".strip()

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
        f"{course['icon']} <b>[SIRC] New ICAI {html.escape(course['name'])} Batch!</b>\n\n"
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

def query_portal(session, course_id, branch_code):
    payload = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": SIRC_VIEWSTATE,
        "__VIEWSTATEGENERATOR": "10EF2921",
        "__SCROLLPOSITIONX": "0",
        "__SCROLLPOSITIONY": "0",
        "__EVENTVALIDATION": SIRC_EVENTVALIDATION,
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

    for course in COURSES_TO_CHECK:
        print(f"\n================ Scanning SIRC [{course['tier']}]: {course['name']} ================")
        for branch_name, branch_code in BRANCHES_TO_CHECK.items():
            try:
                res = query_portal(session, course["id"], branch_code)

                if res.status_code != 200:
                    print(f"[{course['name']}] {branch_name.ljust(20)} -> SERVER HTTP {res.status_code}")
                    continue

                table = find_batch_table(BeautifulSoup(res.text, "html.parser"))
                if not table:
                    continue

                batches = parse_batches(table)
                unseen_batches = [b for b in batches if b["batch_no"] not in seen_batches]

                if not unseen_batches:
                    continue

                print(f"[{course['name']}] {branch_name.ljust(20)} -> {len(unseen_batches)} NEW BATCHES TO ALERT")

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
        print(f"\n[SIRC] Run complete: recorded and alerted {len(newly_seen)} new batches.")
    else:
        print("\n[SIRC] Run complete: no new batches detected.")

if __name__ == "__main__":
    main()
