import os
import re
import time
import json
import html
import urllib.parse
import requests
from bs4 import BeautifulSoup

URL = "https://www.icaionlineregistration.org/launchbatchdetail.aspx"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SEEN_DATA_FILE = "seen_batches_wirc.json"
TOPICS_FILE = "topics_wirc.json"

# Telegram Supergroup Chat IDs
GROUP_INTER_ID = -1003700354486
GROUP_FINAL_ID = -1003906764845

# Dedicated high-density topics (all others go to 'Other WIRC Branches')
HIGH_DENSITY_BRANCHES = {
    "GOA": "🌴 Goa",
    "MUMBAI": "🏢 Mumbai",
    "PUNE": "🏛️ Pune",
    "AHMEDABAD": "🏙️ Ahmedabad",
    "SURAT": "💎 Surat",
    "NAGPUR": "🍊 Nagpur",
    "VADODARA": "🏭 Vadodara",
    "NASHIK": "🍇 Nashik",
    "THANE": "🌆 Thane",
    "NAVI MUMBAI": "🌉 Navi Mumbai",
    "PIMPRI CHINCHWAD": "🏗️ Pimpri Chinchwad",
    "JALGAON": "🍌 Jalgaon"
}
CATCH_ALL_TOPIC_NAME = "📍 Other WIRC Branches"

COURSES_TO_CHECK = [
    # ICITSS -> Inter Group
    {"id": "46", "name": "Orientation Course (OC)", "tier": "INTER", "group_id": GROUP_INTER_ID, "icon": "🎓"},
    {"id": "47", "name": "Information Technology (ITT)", "tier": "INTER", "group_id": GROUP_INTER_ID, "icon": "💻"},
    
    # AICITSS -> Final Group
    {"id": "48", "name": "Advanced ITT", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "⚡"},
    {"id": "45", "name": "MCS Course (GMCS)", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "👔"},
    {"id": "49", "name": "MCS Course (Weekend)", "tier": "FINAL", "group_id": GROUP_FINAL_ID, "icon": "👔"}
]

REGION_ID = "2"

BRANCHES_TO_CHECK = {
    "MUMBAI": "255",
    "PUNE": "77",
    "AHMEDABAD": "56",
    "THANE": "84",
    "NAVI MUMBAI": "76",
    "PIMPRI CHINCHWAD": "78",
    "NASHIK": "74",
    "NAGPUR": "72",
    "SURAT": "83",
    "VADODARA": "62",
    "AURANGABAD": "61",
    "KOLHAPUR": "70",
    "JALGAON": "68",
    "SOLAPUR": "82",
    "SANGLI": "80",
    "SATARA": "81",
    "DHULE": "65",
    "AHMEDNAGAR": "57",
    "AKOLA": "58",
    "AMRAVATI": "60",
    "ANAND": "59",
    "BHARUCH": "63",
    "BHAVNAGAR": "64",
    "BHUJ": "266",
    "GANDHIDHAM": "66",
    "GANDHINAGAR": "282",
    "GOA": "67",
    "ICHALKARANJI": "274",
    "JAMNAGAR": "69",
    "KALYAN DOMBIVLI": "265",
    "LATUR": "71",
    "NANDED": "73",
    "NAVSARI": "75",
    "RAJKOT": "79",
    "RATNAGIRI": "269",
    "VAPI": "86",
    "VASAI": "85"
}

FALLBACK_VIEWSTATE = urllib.parse.unquote(
    "%2FwEPDwUKMTY4OTkwNTY0MA9kFgICBA9kFgoCAw8WAh4HVmlzaWJsZWdkAgcPEA8WBh4NRGF0YVRleHRGaWVsZAULcmVnaW9uX25hbWUeDkRhdGFWYWx1ZUZpZWxkBQlyZWdpb25faWQeC18hRGF0YUJvdW5kZ2QQFQcGU2VsZWN0B0NlbnRyYWwHRWFzdGVybgdGb3JlaWduCE5vcnRoZXJuCFNvdXRoZXJuB1dlc3Rlcm4VBwZTZWxlY3QBNQExATYBMwE0ATIUKwMHZ2dnZ2dnZxYBAgZkAgsPEA8WBh8BBQticmFuY2hfbmFtZR8CBQlicmFuY2hfaWQfA2dkEBUmCUFITUVEQUJBRApBSE1FRE5BR0FSBUFLT0xBCEFNUkFWQVRJBUFOQU5ECkFVUkFOR0FCQUQHQkhBUlVDSAlCSEFWTkFHQVIEQkhVSgVESFVMRQpHQU5ESElESEFNDEdBTkRISU5BR0FSIANHT0EMSWNoYWxrYXJhbmppB0pBTEdBT04ISkFNTkFHQVIOS2FseWFuRG9tYml2bGkIS09MSEFQVVIFTEFUVVIGTVVNQkFJBk5BR1BVUgZOQU5ERUQGTkFTSElLC05BVkkgTVVNQkFJB05BVlNBUkkQUElNUFJJIENISU5DSFdBRARQVU5FBlJBSktPVApSYXRhbmFnaXJpBlNBTkdMSQZTQVRBUkEHU09MQVBVUgVTVVJBVAVUSEFORQh0cnlzdXBlcghWYWRvZGFyYQRWQVBJBVZBU0FJFSYCNTYCNTcCNTgCNjACNTkCNjECNjMCNjQDMjY2AjY1AjY2AzI4MgI2NwMyNzQCNjgCNjkDMjY1AjcwAjcxAzI1NQI3MgI3MwI3NAI3NgI3NQI3OAI3NwI3OQMyNjkCODACODECODICODMCODQDMjYxAjYyAjg2Ajg1FCsDJmdnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZGQCDw8QDxYGHwEFC2NvdXJzZV9uYW1lHwIFCWNvdXJzZV9pZB8DZ2QQFQUcQWR2YW5jZWQgKElDSVRTUykgTUNTIENvdXJzZSZBZHZhbmNlZCAoSUNJVFNTKSBNQ1MgQ291cnNlIC0gV2Vla2VuZClBSUNJVFNTIC0gQWR2YW5jZWQgSW5mb3JtYXRpb24gVGVjaG5vbG9neR9JQ0lUU1MgLSBJbmZvcm1hdGlvbiBUZWNobm9sb2d5G0lDSVRTUyAtIE9yaWVudGF0aW9uIENvdXJzZRUFAjQ1AjQ5AjQ4AjQ3AjQ2FCsDBWdnZ2dnZGQCEw9kFgJmD2QWAgIBDzwrABEDAA8WBB8DZx4LXyFJdGVtQ291bnQCAWQBEBYAFgAWAAwUKwAAFgJmD2QWBgIBD2QWFmYPZBYCAgEPDxYCHgRUZXh0BRRJQ0lUU1NPQ19fSkFMR0FPTl8xMWRkAgEPZBYCAgEPDxYCHwUFAjQ4ZGQCAg9kFgICAQ8PFgIfBQUKMTgvMTAvMjAyNmRkAgMPZBYCAgEPDxYCHwUFCjAxLzExLzIwMjZkZAIED2QWAgIBDw8WAh8FBRE4LTAtQU0gdG8gMi0zMC1QTWRkAgUPZBYCAgEPDxYCHwUFB0pBTEdBT05kZAIGD2QWAgIBDw8WAh8FBRtJQ0lUU1MgLSBPcmllbnRhdGlvbiBDb3Vyc2VkZAIHD2QWAgIBDw8WAh8FBQdHZW5lcmFsZGQCCA9kFgQCAQ8PFgIfBQUCNDZkZAIDDw8WAh8FBQEyZGQCCQ9kFgICAQ8PFgIfBQUKMTcvMDgvMjAyNmRkAgoPZBYCAgEPDxYCHwUFElJlZ2lzdHJhdGlvbiBTdGFydGRkAgIPDxYCHwBoZGQCAw8PFgIfAGhkZBgBBQlHcmlkVmlldzEPPCsADAEIAgFkQrpm6LsM2NU1AMgmZ%2FVjPpvuhjK%2BXW8KFr8vqx5L6Ho%3D"
)
FALLBACK_EVENTVALIDATION = urllib.parse.unquote(
    "%2FwEdADWt6592kFtp90VL2l8q6a0CBlQi3z98kEUtu3eeY4Trat6exFmXkPdVcrOOeGjItwuyPnxUY8XnCNICH5i1DkmDXFPgpuH3lEReDvg4F%2FRmT2b5xc52gpE9Izq5nWPtrGRQp2m7IlhPwdDibvoytWRumG9yZyRhUfRE4W6sWNNHnbU7cbYesaWJWhXAU382C3kj2dHwvW82cujaYSiCkZ3sA9ZB91Hi9Hb4eSQCzCsWTr0zL%2F%2FrRmHUvq882TgElaDiAF1C15DShQJg3gLf3lIBSHkjRrhTv1gK%2FpfTt%2Bj0UqvFGMDYBctWFaudAlGyyom2tpbxbuqFVQa0ii1p%2F06xhhpNFv%2FptNOUicIA960rmZMS1R2hQsQTENvLg2JoqpJwo%2Bu1QKo3GadUL4kU7BPMW4r41v%2Fas%2Fjqz%2Bc3gK5Dg6Gix9t5pEuSWM8VlLuDA%2BhQ8ouPJD4lh19ggQRT9m%2ByKyrqt68fILF55VOdOBNniNPS2AFNQYQbtWz49tYHuHkirPaKyBDZHHpb6hilqKfE71zVWg6UO85R3Cu5VKOjdHxCdMzKi5w%2FNHcC0UDhMm2AfezN8hGv%2FdwZzolfDNabPd7NHiDshxfHCCF7RYhdBp5qDKfl7Q8B3xsnZA%2BpTX7BLmYS52zorp7Mo5%2BfYtnZMUNFTMQYWQvKImsPBvs2BsiVWYgA1%2FcGwVXOUX83EzIEhjUUHkyf8Ko4hSy1M6oBD4Dq%2Fxl5DN3fqI27no%2BEPb22d%2Bz3sdQbEZAx7Cd6pagjLwEz%2FjL2jk%2BPB2NU9qvd0a7Bu4U6sDaZwEe8HbKgtReP0w3R41UEL7KPhZFFYL4U%2FTCSCSOOEFh7xgwlhyvdWKLNhBIVeGRqWdDTr3wOGDxGIlb1UPRXn%2Fcp%2FX%2Fx1er9UblSXGkW8TsL7rmcYxIHVa6HOiXsJdx4k5V59u54LAjhLOcFrOCbR%2B0TLZ1yPzxhNBp58LV3C%2BSDQPNS5yIY6NCIsbOSWoJPjFmpjk9u%2B43%2FGIgdV4zOqQzLgbAk5LHRxRsrRN8LG0Syh5ICDtd5YdzudyqtGD4WIukGRxsM7zCt4OK0obpTHn3AdcEKmFh891O2LB9kbThRvuk76pdSnZ1Vn4DHFo0gVOLv3RSi7Y7vExhtpSYs0p0QACwwJIP2EmMQNHVKMKQvTgrCvl65"
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
        f"{course['icon']} <b>[WIRC] New ICAI {html.escape(course['name'])} Batch!</b>\n\n"
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

                # Self-healing: recreate deleted topics on the fly
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
        print(f"\n================ Scanning WIRC [{course['tier']}]: {course['name']} ================")
        for branch_name, branch_code in BRANCHES_TO_CHECK.items():
            try:
                table = None
                if live_vs and live_ev:
                    post_res = query_portal(session, course["id"], branch_code, live_vs, live_ev, live_gen)
                    if post_res.status_code == 200:
                        table = find_batch_table(BeautifulSoup(post_res.text, "html.parser"))

                if not table:
                    post_res = query_portal(
                        session, course["id"], branch_code, FALLBACK_VIEWSTATE, FALLBACK_EVENTVALIDATION, "10EF2921"
                    )
                    if post_res.status_code == 200:
                        table = find_batch_table(BeautifulSoup(post_res.text, "html.parser"))

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
        print(f"\n[WIRC] Run complete: recorded and alerted {len(newly_seen)} new batches.")
    else:
        print("\n[WIRC] Run complete: no new batches detected.")

if __name__ == "__main__":
    main()
