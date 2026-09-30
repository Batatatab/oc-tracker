import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup

URL = "https://www.icaionlineregistration.org/launchbatchdetail.aspx"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SEEN_DATA_FILE = "seen_batches_sirc.json"
TOPICS_FILE = "topics_sirc.json"

# Telegram Supergroup Chat IDs for SIRC
GROUP_INTER_ID = -1004454612113
GROUP_FINAL_ID = -1004446662940

# High-density focus branches in Southern Region
HIGH_DENSITY_BRANCHES = {
    "CHENNAI": "🏢 Chennai",
    "BENGALURU": "💻 Bengaluru",
    "HYDERABAD": "💎 Hyderabad",
    "ERNAKULAM": "🚢 Ernakulam",
    "COIMBATORE": "🏭 Coimbatore",
    "VISAKHAPATNAM": "⚓ Visakhapatnam",
    "VIJAYAWADA": "🏛️ Vijayawada",
    "MADURAI": "🛕 Madurai",
    "KOZHIKODE": "🌴 Kozhikode",
    "THIRUVANANTHAPURAM": "🏛️ Thiruvananthapuram",
    "MYSURU": "🏰 Mysuru",
    "MANGALURU": "🏖️ Mangaluru"
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

# Authentic branch codes from SIRC portal
BRANCHES_TO_CHECK = {
    "Alappuzha": "101",
    "Anantapur": "260",
    "Ballari": "104",
    "Belagavi": "103",
    "BENGALURU": "102",
    "Chengalpattu": "268",
    "CHENNAI": "138",
    "COIMBATORE": "106",
    "ERNAKULAM": "107",
    "ERODE": "252",
    "GUNTUR": "109",
    "HUBBALLI": "110",
    "HYDERABAD": "111",
    "KADAPA": "279",
    "KAKINADA": "112",
    "Kalaburgi": "273",
    "KANNUR": "113",
    "KARIMNAGAR": "258",
    "Kollam": "122",
    "KOTTAYAM": "114",
    "Kozhikode": "105",
    "KUMBAKONAM": "115",
    "KURNOOL": "245",
    "MADURAI": "116",
    "Mangaluru": "117",
    "Mysuru": "118",
    "NELLORE": "119",
    "ONGOLE": "259",
    "Palakkad": "120",
    "PUDUCHERRY": "121",
    "RAJAMAHENDRAVARAM": "123",
    "SALEM": "124",
    "SIRC": "251",
    "SIVAKASI": "125",
    "Thiruvananthapuram": "131",
    "Thoothukudi": "132",
    "Thrissur": "130",
    "Tiruchirapalli": "126",
    "TIRUNELVELI": "127",
    "TIRUPATI": "128",
    "TIRUPUR": "129",
    "UDUPI": "133",
    "VELLORE": "134",
    "VIJAYAWADA": "135",
    "VISAKHAPATNAM": "136",
    "WARANGAL": "246",
    "West Godavari": "281"
}

# Complete, intact cryptographic tokens for Southern Region
FALLBACK_VIEWSTATE = (
    "/wEPDwUKMTY4OTkwNTY0MA9kFgICBA9kFgoCAw8WAh4HVmlzaWJsZWdkAgcPEA8WBh4NRGF0YVRleHRGaWVsZAULcmVnaW9uX25hbWUe"
    "DkRhdGFWYWx1ZUZpZWxkBQlyZWdpb25faWQeC18hRGF0YUJvdW5kZ2QQFQcGU2VsZWN0B0NlbnRyYWwHRWFzdGVybgdGb3JlaWduCE5v"
    "cnRoZXJuCFNvdXRoZXJuB1dlc3Rlcm4VBwZTZWxlY3QBNQExATYBMwE0ATIUKwMHZ2dnZ2dnZxYBAgVkAgsPEA8WBh8BBQticmFuY2hf"
    "bmFtZR8CBQlicmFuY2hfaWQfA2dkEBUvCUFsYXBwdXpoYQlBbmFudGFwdXIHQmFsbGFyaQhCZWxhZ2F2aQlCRU5HQUxVUlUMQ2hlbmdh"
    "bHBhdHR1B0NIRU5OQUkKQ09JTUJBVE9SRQlFUk5BS1VMQU0FRVJPREUGR1VOVFVSCEhVQkJBTExJCUhZREVSQUJBRAZLQURBUEEIS0FL"
    "SU5BREEJS2FsYWJ1cmdpBktBTk5VUgpLQVJJTU5BR0FSBktvbGxhbQhLT1RUQVlBTQlLb3poaWtvZGUKS1VNQkFLT05BTQdLVVJOT09M"
    "B01BRFVSQUkJTWFuZ2FsdXJ1Bk15c3VydQdORUxMT1JFBk9OR09MRQhQYWxha2thZApQVURVQ0hFUlJZEVJBSkFNQUhFTkRSQVZBUkFN"
    "BVNBTEVNBFNJUkMIU0lWQUtBU0kSVGhpcnV2YW5hbnRoYXB1cmFtC1Rob290aHVrdWRpCFRocmlzc3VyDlRpcnVjaGlyYXBhbGxpC1RJ"
    "UlVORUxWRUxJCFRJUlVQQVRJB1RJUlVQVVIFVURVUEkHVkVMTE9SRQpWSUpBWUFXQURBDVZJU0FLSEFQQVROQU0IV0FSQU5HQUwNV2Vz"
    "dCBHb2RhdmFyaRUvAzEwMQMyNjADMTA0AzEwMwMxMDIDMjY4AzEzOAMxMDYDMTA3AzI1MgMxMDkDMTEwAzExMQMyNzkDMTEyAzI3MwMx"
    "MTMDMjU4AzEyMgMxMTQDMTA1AzExNQMyNDUDMTE2AzExNwMxMTgDMTE5AzI1OQMxMjADMTIxAzEyMwMxMjQDMjUxAzEyNQMxMzEDMTMy"
    "AzEzMAMxMjYDMTI3AzEyOAMxMjkDMTMzAzEzNAMxMzUDMTM2AzI0NgMyODEUKwMvZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dn"
    "Z2dnZ2dnZ2dnZ2dnZ2dnZ2RkAg8PEA8WBh8BBQtjb3Vyc2VfbmFtZR8CBQljb3Vyc2VfaWQfA2dkEBUFHEFkdmFuY2VkIChJQ0lUU1Mp"
    "IE1DUyBDb3Vyc2UmQWR2YW5jZWQgKElDSVRTUykgTUNTIENvdXJzZSAtIFdlZWtlbmQpQUlDSVRTUyAtIEFkdmFuY2VkIEluZm9ybWF0"
    "aW9uIFRlY2hub2xvZ3kfSUNJVFNTIC0gSW5mb3JtYXRpb24gVGVjaG5vbG9neRtJQ0lUU1MgLSBPcmllbnRhdGlvbiBDb3Vyc2UVBQI0"
    "NQI0OQI0OAI0NwI0NhQrAwVnZ2dnZ2RkAhMPZBYCZg9kFgICAQ88KwARAwAPFgQfA2ceC18hSXRlbUNvdW50AgZkARAWAQIJFgE8KwAF"
    "AQAWAh8AaBYBAgYMFCsAABYCZg9kFhACAQ9kFhZmD2QWAgIBDw8WAh4EVGV4dAUWSUNJVFNTT0NfX0FsYXBwdXpoYV85MGRkAgEPZBYC"
    "AgEPDxYCHwUFAjE1ZGQCAg9kFgICAQ8PFgIfBQUKMDUvMTAvMjAyNmRkAgMPZBYCAgEPDxYCHwUFCjI0LzEwLzIwMjZkZAIED2QWAgIB"
    "Dw8WAh8FBRI5LTMwLUFNIHRvIDQtMzAtUE1kZAIFD2QWAgIBDw8WAh8FBQlBbGFwcHV6aGFkZAIGD2QWAgIBDw8WAh8FBRtJQ0lUU1Mg"
    "LSBPcmllbnRhdGlvbiBDb3Vyc2VkZAIHD2QWAgIBDw8WAh8FBQdHZW5lcmFsZGQCCA9kFgQCAQ8PFgIfBQUCNDZkZAIDDw8WAh8FBQI0"
    "OWRkAgkPZBYCAgEPDxYCHwUFCjE2LzA3LzIwMjZkZAIKD2QWAgIBDw8WAh8FBRJSZWdpc3RyYXRpb24gU3RhcnRkZAICD2QWFmYPZBYC"
    "AgEPDxYCHwUFFklDSVRTU09DX19BbGFwcHV6aGFfOTFkZAIBD2QWAgIBDw8WAh8FBQEzZGQCAg9kFgICAQ8PFgIfBQUKMDUvMTAvMjAy"
    "NmRkAgMPZBYCAgEPDxYCHwUFCjI0LzEwLzIwMjZkZAIED2QWAgIBDw8WAh8FBRI5LTMwLUFNIHRvIDQtMzAtUE1kZAIFD2QWAgIBDw8W"
    "Ah8FBQlBbGFwcHV6aGFkZAIGD2QWAgIBDw8WAh8FBRtJQ0lUU1MgLSBPcmllbnRhdGlvbiBDb3Vyc2VkZAIHD2QWAgIBDw8WAh8FBQdH"
    "ZW5lcmFsZGQCCA9kFgQCAQ8PFgIfBQUCNDZkZAIDDw8WAh8FBQI0N2RkAgkPZBYCAgEPDxYCHwUFCjI3LzA3LzIwMjZkZAIKD2QWAgIB"
    "Dw8WAh8FBRJSZWdpc3RyYXRpb24gU3RhcnRkZAIDD2QWFmYPZBYCAgEPDxYCHwUFFklDSVRTU09DX19BbGFwcHV6aGFfOTRkZAIBD2QW"
    "AgIBDw8WAh8FBQEzZGQCAg9kFgICAQ8PFgIfBQUKMDUvMTAvMjAyNmRkAgMPZBYCAgEPDxYCHwUFCjI0LzEwLzIwMjZkZAIED2QWAgIB"
    "Dw8WAh8FBRI5LTMwLUFNIHRvIDQtMzAtUE1kZAIFD2QWAgIBDw8WAh8FBQlBbGFwcHV6aGFkZAIGD2QWAgIBDw8WAh8FBRtJQ0lUU1Mg"
    "LSBPcmllbnRhdGlvbiBDb3Vyc2VkZAIHD2QWAgIBDw8WAh8FBQdHZW5lcmFsZGQCCA9kFgQCAQ8PFgIfBQUCNDZkZAIDDw8WAh8FBQI0"
    "NWRkAgkPZBYCAgEPDxYCHwUFCjE3LzA4LzIwMjZkZAIKD2QWAgIBDw8WAh8FBRJSZWdpc3RyYXRpb24gU3RhcnRkZAIED2QWFmYPZBYC"
    "AgEPDxYCHwUFFklDSVRTU09DX19BbGFwcHV6aGFfOTJkZAIBD2QWAgIBDw8WAh8FBQIzNmRkAgIPZBYCAgEPDxYCHwUFCjI2LzEwLzIw"
    "MjZkZAIDD2QWAgIBDw8WAh8FBQoxMS8xMS8yMDI2ZGQCBA9kFgICAQ8PFgIfBQUSOS0zMC1BTSB0byA0LTMwLVBNZGQCBQ9kFgICAQ8P"
    "FgIfBQUJQWxhcHB1emhhZGQCBg9kFgICAQ8PFgIfBQUbSUNJVFNTIC0gT3JpZW50YXRpb24gQ291cnNlZGQCBw9kFgICAQ8PFgIfBQUH"
    "R2VuZXJhbGRkAggPZBYEAgEPDxYCHwUFAjQ2ZGQCAw8PFgIfBQUCMTRkZAIJD2QWAgIBDw8WAh8FBQoxMy8wOC8yMDI2ZGQCCg9kFgIC"
    "AQ8PFgIfBQUSUmVnaXN0cmF0aW9uIFN0YXJ0ZGQCBQ9kFhZmD2QWAgIBDw8WAh8FBRZJQ0lUU1NPQ19fQWxhcHB1emhhXzkzZGQCAQ9k"
    "FgICAQ8PFgIfBQUCNDVkZAICD2QWAgIBDw8WAh8FBQoxMi8xMS8yMDI2ZGQCAw9kFgICAQ8PFgIfBQUKMjgvMTEvMjAyNmRkAgQPZBYC"
    "AgEPDxYCHwUFEjktMzAtQU0gdG8gNC0zMC1QTWRkAgUPZBYCAgEPDxYCHwUFCUFsYXBwdXpoYWRkAgYPZBYCAgEPDxYCHwUFG0lDSVRT"
    "UyAtIE9yaWVudGF0aW9uIENvdXJzZWRkAgcPZBYCAgEPDxYCHwUFB0dlbmVyYWxkZAIID2QWBAIBDw8WAh8FBQI0NmRkAgMPDxYCHwUF"
    "ATBkZAIJD2QWAgIBDw8WAh8FBQoxMy8wOC8yMDI2ZGQCCg9kFgICAQ8PFgIfBQULTm90IFN0YXJ0ZWRkZAIGD2QWFmYPZBYCAgEPDxYC"
    "HwUFFklDSVRTU09DX19BbGFwcHV6aGFfOTVkZAIBD2QWAgIBDw8WAh8FBQIzNWRkAgIPZBYCAgEPDxYCHwUFCjMwLzExLzIwMjZkZAID"
    "D2QWAgIBDw8WAh8FBQoxNi8xMi8yMDI2ZGQCBA9kFgICAQ8PFgIfBQUSOS0zMC1BTSB0byA0LTMwLVBNZGQCBQ9kFgICAQ8PFgIfBQUJ"
    "QWxhcHB1emhhZGQCBg9kFgICAQ8PFgIfBQUbSUNJVFNTIC0gT3JpZW50YXRpb24gQ291cnNlZGQCBw9kFgICAQ8PFgIfBQUHR2VuZXJh"
    "bGRkAggPZBYEAgEPDxYCHwUFAjQ2ZGQCAw8PFgIfBQUBMGRkAgkPZBYCAgEPDxYCHwUFCjAyLzA5LzIwMjZkZAIKD2QWAgIBDw8WAh8F"
    "BQtOb3QgU3RhcnRlZGRkAgcPDxYCHwBoZGQCCA8PFgIfAGhkZBgBBQlHcmlkVmlldzEPPCsADAEIAgFknUipbOocbVYHmWI16GM7pKX2"
    "ATo4WzfzGi6tFAkV8p4="
)

FALLBACK_EVENTVALIDATION = (
    "/wEdAD483aUHnQenEfGVOzPQARODBlQi3z98kEUtu3eeY4Trat6exFmXkPdVcrOOeGjItwuyPnxUY8XnCNICH5i1DkmDXFPgpuH3lERe"
    "Dvg4F/RmT2b5xc52gpE9Izq5nWPtrGRQp2m7IlhPwdDibvoytWRumG9yZyRhUfRE4W6sWNNHnbU7cbYesaWJWhXAU382C3nK1uKYS3Gi"
    "68/4c2xMtrvuObZcupe3bd4w1MvO+ZC7Yp126uGiE2JuyBo5cwQP0Gu7cSOL3+udQ2TBIOQOSLAdGbB9cfaCVQZ86pVUr60JPjq7z0Qv"
    "p5hPrVt2vxmMHla53DJZQqagnF0mlbmz4Ka9Luo5RIwcyTTFd6THEIdMlUF9NBk+DuecPl6fd0wZpCR/mYsq5yYAazieHNbKobJAzynf"
    "IPAYQXqgZ7gHmahmhg5RsmyVw54jbEUdxNoyDeqI0in9bFSYGcH89WBqb8/wbas6eXwU3tBBycFDHdquZe7suztI+tny0668pnqNMv01"
    "hlQubnErvO0pe2kq9oPuJUmSVlCThqGli3RMjglnvPXcztUYLKThCC15lHRaa7L8mMesddC9tYybJs3JOkIo4dcX/cUooiVp6MOjyi+/"
    "susmlZ81h0Trw25UBaxWuB4C5dE5hPWRbJgnN8wyr6P2iJFECo00p/9qP+mnBDa2oYeP8AQgsCz+/VAhClZ1ZExnKHQKlIEMuFR/8Zpr"
    "OzsqaieS9qq0W3ucL/Kk6zhIkBzce2lWFtIfkXnjl61s1Qhj34CeJky0YAcMFYl70ApQZp4py2mFabGohSQ5mZu4azk+k1Fb2waK8Sif"
    "78/4FpdqajnrnWt28Z54bncjAFwJGU7UUEIhvTiLhpeB6CyEvOKBGMvxBHc8Q6EKvWj5Oh8Yp3f1/ecSc9+ASFYYYh6XBViwl/E37a6j"
    "w3mAUZcM1ZAKtTrJHMVCi2elio1TXDycnolUflm6rnDyuQD5fNaPzr1kn5pjIyrG5TPIjcqvAvY3Gw66Uk79WV0zCK2tysM2c7zi2zLu"
    "qXEuNLHxpUYobghHth7CZhkwJ/cCqopp/zBI57I60ZH4tmKnLGHog/xDYz6VkmtiHo52Y7icSgI7Bag8q5TNZyHxSvi+gnbqrVBKg4kM"
    "oun+wl9MPMqJaAdO5Rq3JszBCXUiJtuqk1xUKLeArIVMQI3+3K8EA6D73Y3/GIgdV4zOqQzLgbAk5LHRxRsrRN8LG0Syh5ICDtd5Ydzu"
    "dyncqrRg+FiLpBkcbDO8wreDitKG6Ux59wHXBCphYfPdTtiwfZG04Ub7pO+qXUp2dVZ+AxxaNIFTi790Uou0jyUs18EfcRpJzvL750D0"
    "sHCYAa9J0sxTK1vFD4heU+g=="
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
        f"{course['icon']} <b>[SIRC] New ICAI {course['name']} Batch!</b>\n\n"
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

def query_portal(session, course_id, branch_code):
    payload = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": FALLBACK_VIEWSTATE,
        "__VIEWSTATEGENERATOR": "10EF2921",
        "__SCROLLPOSITIONX": "0",
        "__SCROLLPOSITIONY": "0",
        "__EVENTVALIDATION": FALLBACK_EVENTVALIDATION,
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
                table = find_batch_table(BeautifulSoup(res.text, "html.parser"))

                if not table:
                    print(f"[{course['name']}] {branch_name.ljust(20)} -> 0 active batches")
                    continue

                batches = parse_batches(table)
                print(f"[{course['name']}] {branch_name.ljust(20)} -> FOUND {len(batches)} BATCHES")

                topic_title = HIGH_DENSITY_BRANCHES.get(branch_name.upper(), CATCH_ALL_TOPIC_NAME)
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
        print(f"\n[SIRC] Run complete: recorded {len(newly_seen)} new batches.")
    else:
        print("\n[SIRC] Run complete: scan finished cleanly (no new batches).")

if __name__ == "__main__":
    main()
