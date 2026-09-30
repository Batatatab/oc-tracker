import os
import re
import time
import json
import html
import requests
from bs4 import BeautifulSoup

URL = "https://www.icaionlineregistration.org/launchbatchdetail.aspx"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SEEN_DATA_FILE = "seen_batches_circ.json"
TOPICS_FILE = "topics_circ.json"

# Telegram Supergroup Chat IDs for CIRC
GROUP_INTER_ID = -1004499260705  # Replace with CIRC Inter Group ID
GROUP_FINAL_ID = -1003935561138  # Replace with CIRC Final Group ID

# Strictly these 8 cities get dedicated topics
HIGH_DENSITY_BRANCHES = {
    "JAIPUR": "🏰 Jaipur",
    "INDORE": "🌟 Indore",
    "GHAZIABAD": "🏢 Ghaziabad",
    "BHOPAL": "🌊 Bhopal",
    "AGRA": "🕌 Agra",
    "AJMER": "🕌 Ajmer",
    "PATNA": "📜 Patna",
    "MEERUT": "🏙️ Meerut"
}
CATCH_ALL_TOPIC_NAME = "📍 Other CIRC Branches"

COURSES_TO_CHECK = [
    # ICITSS -> Inter Group
    {"id": "46", "name": "Orientation Course (OC)", "tier": "INTER", "group_id": GROUP_INTER_ID, "icon": "🎓"},
    {"id": "47", "name": "Information Technology (ITT)", "tier": "INTER", "group_id": GROUP_INTER_ID, "icon": "💻"},
    
    # AICITSS -> Final Group
    {"id": "48", "name": "Advanced ITT", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "⚡"},
    {"id": "45", "name": "MCS Course (GMCS)", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "👔"},
    {"id": "49", "name": "MCS Course (Weekend)", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "👔"}
]

REGION_ID = "5"  # Central Region

BRANCHES_TO_CHECK = {
    "AGRA": "150",
    "AJMER": "151",
    "ALIGARH": "152",
    "ALWAR": "154",
    "BAREILLY": "155",
    "BEAWAR": "156",
    "Bhagalpur": "280",
    "Bharatpur": "264",
    "BHILAI": "157",
    "BHILWARA": "158",
    "BHOPAL": "159",
    "BIKANER": "160",
    "BILASPUR": "161",
    "Bulandshahr": "270",
    "CHITTORGARH": "162",
    "CIRC": "247",
    "DEHRADUN": "163",
    "DHANBAD": "164",
    "GautamBudhaNagar": "181",
    "GHAZIABAD": "165",
    "GORAKHPUR": "166",
    "GWALIOR": "167",
    "Haldwani": "262",
    "Hanumangarh": "284",
    "HARIDWAR": "243",
    "INDORE": "168",
    "JABALPUR": "169",
    "JAIPUR": "170",
    "JAMSHEDPUR": "171",
    "JHANSI": "172",
    "JODHPUR": "173",
    "KANPUR": "240",
    "KISHANGARH": "174",
    "KOTA": "175",
    "LUCKNOW": "176",
    "MATHURA": "177",
    "MEERUT": "178",
    "MORADABAD": "179",
    "MUZAFFARNAGAR": "180",
    "Neemuch": "283",
    "PALI": "182",
    "PATNA": "183",
    "PRAYAGRAJ": "153",
    "Raigarh": "288",
    "RAIPUR": "184",
    "Rajsamand": "286",
    "RANCHI": "185",
    "RATLAM": "186",
    "SAHARANPUR": "187",
    "SATNA": "241",
    "SIKAR": "188",
    "SRIGANGANAGAR": "189",
    "UDAIPUR": "190",
    "UJJAIN": "191",
    "VARANASI": "192"
}

CIRC_VIEWSTATE = """/wEPDwUKMTY4OTkwNTY0MA9kFgICBA9kFgoCAw8WAh4HVmlzaWJsZWdkAgcPEA8WBh4NRGF0YVRleHRGaWVsZAULcmVnaW9uX25hbWUeDkRhdGFWYWx1ZUZpZWxkBQlyZWdpb25faWQeC18hRGF0YUJvdW5kZ2QQFQcGU2VsZWN0B0NlbnRyYWwHRWFzdGVybgdGb3JlaWduCE5vcnRoZXJuCFNvdXRoZXJuB1dlc3Rlcm4VBwZTZWxlY3QBNQExATYBMwE0ATIUKwMHZ2dnZ2dnZxYBAgFkAgsPEA8WBh8BBQticmFuY2hfbmFtZR8CBQlicmFuY2hfaWQfA2dkEBU3BEFHUkEFQUpNRVIHQUxJR0FSSAVBTFdBUghCQVJFSUxMWQZCRUFXQVIJQmhhZ2FscHVyCUJoYXJhdHB1cgZCSElMQUkIQkhJTFdBUkEGQkhPUEFMB0JJS0FORVIIQklMQVNQVVILQnVsYW5kc2hhaHILQ0hJVFRPUkdBUkgEQ0lSQwhERUhSQURVTgdESEFOQkFEEEdhdXRhbUJ1ZGhhTmFnYXIJR0hBWklBQkFECUdPUkFLSFBVUgdHV0FMSU9SCEhhbGR3YW5pC0hhbnVtYW5nYXJoCEhBUklEV0FSBklORE9SRQhKQUJBTFBVUgZKQUlQVVIKSkFNU0hFRFBVUgZKSEFOU0kHSk9ESFBVUgZLQU5QVVIKS0lTSEFOR0FSSARLT1RBB0xVQ0tOT1cHTUFUSFVSQQZNRUVSVVQJTU9SQURBQkFEDU1VWkFGRkFSTkFHQVIHTmVlbXVjaARQQUxJBVBBVE5BCVBSQVlBR1JBSgdSYWlnYXJoBlJBSVBVUglSYWpzYW1hbmQGUkFOQ0hJBlJBVExBTQpTQUhBUkFOUFVSBVNBVE5BBVNJS0FSDVNSSUdBTkdBTkFHQVIHVURBSVBVUgZVSkpBSU4IVkFSQU5BU0kVNwMxNTADMTUxAzE1MgMxNTQDMTU1AzE1NgMyODADMjY0AzE1NwMxNTgDMTU5AzE2MAMxNjEDMjcwAzE2MgMyNDcDMTYzAzE2NAMxODEDMTY1AzE2NgMxNjcDMjYyAzI4NAMyNDMDMTY4AzE2OQMxNzADMTcxAzE3MgMxNzMDMjQwAzE3NAMxNzUDMTc2AzE3NwMxNzgDMTc5AzE4MAMyODMDMTgyAzE4MwMxNTMDMjg4AzE4NAMyODYDMTg1AzE4NgMxODcDMjQxAzE4OAMxODkDMTkwAzE5MQMxOTIUKwM3Z2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2RkAg8PEA8WBh8BBQtjb3Vyc2VfbmFtZR8CBQljb3Vyc2VfaWQfA2dkEBUFHEFkdmFuY2VkIChJQ0lUU1MpIE1DUyBDb3Vyc2UmQWR2YW5jZWQgKElDSVRTUykgTUNTIENvdXJzZSAtIFdlZWtlbmQpQUlDSVRTUyAtIEFkdmFuY2VkIEluZm9ybWF0aW9uIFRlY2hub2xvZ3kfSUNJVFNTIC0gSW5mb3JtYXRpb24gVGVjaG5vbG9neRtJQ0lUU1MgLSBPcmllbnRhdGlvbiBDb3Vyc2UVBQI0NQI0OQI0OAI0NwI0NhQrAwVnZ2dnZ2RkAhMPZBYCZg9kFgICAQ88KwARAgEQFgAWABYADBQrAABkGAEFCUdyaWRWaWV3MQ9nZFpQAkqnXnWZ13wdbG/nIZ+EPukTVzCt1m7+/Y84baW/""".strip()

CIRC_EVENTVALIDATION = """/wEdAEahT2x411WE+qKyQqm6MZXqBlQi3z98kEUtu3eeY4Trat6exFmXkPdVcrOOeGjItwuyPnxUY8XnCNICH5i1DkmDXFPgpuH3lEReDvg4F/RmT2b5xc52gpE9Izq5nWPtrGRQp2m7IlhPwdDibvoytWRumG9yZyRhUfRE4W6sWNNHnbU7cbYesaWJWhXAU382C3n6egKoRaBQkLESZcuYTH8FBTy4HgdqeVGYUsH7q/5GqPmMCVaP0ZyOC1X/SlWllkNrYUCHyEH2clVc8JunqT+Fa3oQG+TzRLk34zRKdw8Mg/r6bU6N8W4e15HSzCdISFpMKhlwDD+Ha7TZS2moIQ5Ph11/wPqciHwwwb3i4Tu1rHPkeixJWNBn6j4YuamNpdeWMbu1BooDoHuJJBLS1ENJzcdTwrZUejztp28fTGkI3Am6E1jNXL0/jhg5t/6z2+KUybmITfpVa0yglltNN2OO2E29HP5fCpqGcvbPWrjbI/hWnAA1oQNXU11pXjbZ1E9sKxuvX45Y95cQ0Mxi7KnHwHz/HcXdqh7e4gR3x/runbrEb2SapeFpYgz79WZCGKg2zhRX0ECbpG51anMPltUJxNzN9Ctda21xC0rw0sk7ju3LdMEG+jBy10KIaOqdj96DfcovoqHuD6XhI0HyQ2wfX308p1R58pkQR7tgyHTNGGCq7ZtC/MrctPU2TnYOKpTjzIZRpSbhJOkUsUE39iyz4QVy7s5DTxRR1xAzIda16X/67/F6GAd/gQ2aA/zkUYSrVscY+DQPmfQXrdxmS7wDZW5F2MOBEnw/amQtsj4clV9qxMR6fIHP7aCFEcHVrNEFZV7xWtM2WgSAs2POepyWhDAsYkq9wy277Bv58KL+LuraXJ2Uhsk0C9NkW7N76pJmbSXZAxMUauKwcFDJruQ24wegyTh3RZ1+dl3fU2QNEM18crEz4bgYwbO4ivUlKFE6zrU5ah7ysbAs2iDVmL5P6gyr66e2cQbrHfy6nSrZ8FPezTL6I1lTEOUfbmFGMLEx5Fhyg4Q2InBKjnWWtwzP4rDfD/m1vJixE660VHsdjYSvE9epg49etY5L+UdMEawjZyCc0n+rfFNrGgxYNOniwfSaEDwdJQNCJIfO62TjbzwCCqaXRqclAOq1Q0DeDhaLBrFYu0vI7+LM+9iEE4qfG/GFlDZqisUL4VJjQ3Rr0Q0z6V6ohkaA4+jrUoXdGWGqMNSyKaQO5kK8F9N1rzl0CB5qaRvExS0NfQuWBLNo6ezTkfLD1s4EcY5VwI5S8gA+ja+ZQCVUd2D40xjTt2yAKb2FrmP0zyD2/zOrWcMGqxqfZsN4UKhh8Hqlv9wcMm8DHR8KpOmb0fJKm5AzVN5vjf8YiB1XjM6pDMuBsCTksdHFGytE3wsbRLKHkgIO13lh3O53Kq0YPhYi6QZHGwzvMK3g4rShulMefcB1wQqYWHz3U7YsH2RtOFG+6Tvql1KdnVWfgMcWjSBU4u/dFKLtJn8mteDFBdQiiT3TCXVMUd/1gSFnmS5WupvdimtcCT0=""".strip()

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

    if not BOT_TOKEN or not group_id or group_id == -1000000000000:
        return None

    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/createForumTopic"
    payload = {"chat_id": group_id, "name": topic_name}

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
    if not BOT_TOKEN or not group_id or group_id == -1000000000000:
        return False

    text = (
        f"{course['icon']} <b>[CIRC] New ICAI {html.escape(course['name'])} Batch!</b>\n\n"
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
                time.sleep(wait_time + 1)
                continue

            if not res.ok:
                print(f"Telegram API Error ({res.status_code}): {res.text}")
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
        "__VIEWSTATE": CIRC_VIEWSTATE,
        "__VIEWSTATEGENERATOR": "10EF2921",
        "__SCROLLPOSITIONX": "0",
        "__SCROLLPOSITIONY": "0",
        "__EVENTVALIDATION": CIRC_EVENTVALIDATION,
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
        print(f"\n================ Scanning CIRC [{course['tier']}]: {course['name']} ================")
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
                # Filter for batches not yet alerted
                unseen_batches = [b for b in batches if b["batch_no"] not in seen_batches]

                if not unseen_batches:
                    continue

                print(f"[{course['name']}] {branch_name.ljust(20)} -> {len(unseen_batches)} NEW BATCHES TO ALERT")

                # Resolve topic only when new batches exist
                clean_name = branch_name.strip().upper()
                topic_title = HIGH_DENSITY_BRANCHES.get(clean_name, CATCH_ALL_TOPIC_NAME)
                thread_id = get_or_create_topic(course["group_id"], course["tier"], topic_title, topics_map)

                for b in unseen_batches:
                    if send_telegram_alert(b, course, course["group_id"], thread_id):
                        seen_batches.add(b["batch_no"])
                        newly_seen.add(b["batch_no"])

            except Exception as e:
                print(f"Error querying {course['name']} @ {branch_name}: {e}")

    if newly_seen:
        save_json(SEEN_DATA_FILE, sorted(list(seen_batches)))
        print(f"\n[CIRC] Run complete: recorded and alerted {len(newly_seen)} new batches.")
    else:
        print("\n[CIRC] Run complete: scan finished cleanly (all batches already alerted).")

if __name__ == "__main__":
    main()
