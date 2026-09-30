import os
import re
import time
import json
import html
import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIG
# ============================================================

URL = "https://www.icaionlineregistration.org/launchbatchdetail.aspx"

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

SEEN_DATA_FILE = "seen_batches_sirc.json"
TOPICS_FILE = "topics_sirc.json"


# ------------------------------------------------------------
# TELEGRAM GROUPS
# ------------------------------------------------------------

GROUP_INTER_ID = -1004454612113       # <-- CHANGE
GROUP_FINAL_ID = -1004446662940       # <-- CHANGE


# ------------------------------------------------------------
# SOUTHERN REGION
# ------------------------------------------------------------

# From the SIRC page/token you provided:
# Southern = 4
REGION_ID = "4"


# ------------------------------------------------------------
# SIRC BRANCHES
# ------------------------------------------------------------

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
    "Madurai": "116",
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
    "West Godavari": "281",
}


# ------------------------------------------------------------
# TELEGRAM TOPICS
# ------------------------------------------------------------

HIGH_DENSITY_BRANCHES = {
    "BENGALURU": "🏢 Bengaluru",
    "CHENNAI": "🏙️ Chennai",
    "HYDERABAD": "🏢 Hyderabad",
    "COIMBATORE": "🏭 Coimbatore",
    "KOZHIKODE": "🌴 Kozhikode",
    "MADURAI": "🏛️ Madurai",
    "MANGALURU": "🌊 Mangaluru",
    "MYSURU": "🏛️ Mysuru",
    "THIRUVANANTHAPURAM": "🌴 Thiruvananthapuram",
    "VIJAYAWADA": "🏙️ Vijayawada",
    "VISAKHAPATNAM": "🌊 Visakhapatnam",
}

CATCH_ALL_TOPIC_NAME = "📍 Other SIRC Branches"


# ------------------------------------------------------------
# COURSES
# ------------------------------------------------------------

COURSES_TO_CHECK = [
    {
        "id": "46",
        "name": "Orientation Course (OC)",
        "tier": "INTER",
        "group_id": GROUP_INTER_ID,
        "icon": "🎓",
    },
    {
        "id": "47",
        "name": "Information Technology (ITT)",
        "tier": "INTER",
        "group_id": GROUP_INTER_ID,
        "icon": "💻",
    },
    {
        "id": "48",
        "name": "Advanced ITT",
        "tier": "FINAL",
        "group_id": GROUP_FINAL_ID,
        "icon": "⚡",
    },
    {
        "id": "45",
        "name": "MCS Course (GMCS)",
        "tier": "FINAL",
        "group_id": GROUP_FINAL_ID,
        "icon": "👔",
    },
    {
        "id": "49",
        "name": "MCS Course (Weekend)",
        "tier": "FINAL",
        "group_id": GROUP_FINAL_ID,
        "icon": "👔",
    },
]


# ============================================================
# HTTP HEADERS
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/155.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.icaionlineregistration.org",
    "Referer": URL,
    "Connection": "keep-alive",
}


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(filepath, default):
    if not os.path.exists(filepath):
        return default

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Could not read {filepath}: {e}")
        return default


def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================
# ASP.NET FORM STATE
# ============================================================

def extract_form_state(soup):
    """
    Extract current ASP.NET hidden fields.
    """

    def value(field_name, default=""):
        tag = soup.find("input", {"name": field_name})
        if tag:
            return tag.get("value", default)
        return default

    return {
        "__VIEWSTATE": value("__VIEWSTATE"),
        "__EVENTVALIDATION": value("__EVENTVALIDATION"),
        "__VIEWSTATEGENERATOR": value(
            "__VIEWSTATEGENERATOR",
            "10EF2921"
        ),
        "__LASTFOCUS": value("__LASTFOCUS"),
        "__SCROLLPOSITIONX": value("__SCROLLPOSITIONX", "0"),
        "__SCROLLPOSITIONY": value("__SCROLLPOSITIONY", "0"),
    }


def get_current_page(session):
    """
    Fresh GET to obtain a valid ASP.NET session + tokens.
    """

    response = session.get(
        URL,
        headers=HEADERS,
        timeout=25,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    state = extract_form_state(soup)

    if not state["__VIEWSTATE"]:
        raise RuntimeError("VIEWSTATE missing from initial page")

    if not state["__EVENTVALIDATION"]:
        raise RuntimeError("EVENTVALIDATION missing from initial page")

    return response.text, soup, state


# ============================================================
# PAGE / DROPDOWN INSPECTION
# ============================================================

def get_select_values(soup, select_id):
    """
    Return all option values from a dropdown.
    """

    select = soup.find("select", {"id": select_id})

    if not select:
        return {}

    result = {}

    for option in select.find_all("option"):
        value = option.get("value", "").strip()
        text = option.get_text(strip=True)

        if value:
            result[value] = text

    return result


def page_contains_sirc_branches(soup):
    """
    Checks whether the current page already has SIRC branch options.
    """

    branch_values = get_select_values(soup, "ddlPou")

    if not branch_values:
        return False

    required_codes = set(BRANCHES_TO_CHECK.values())
    existing_codes = set(branch_values.keys())

    # If even a decent portion is present, we consider
    # the SIRC branch list loaded.
    overlap = len(required_codes.intersection(existing_codes))

    return overlap >= 3


# ============================================================
# REGION SELECTION
# ============================================================

def select_region(session, soup, state):
    """
    Some ASP.NET pages populate ddlPou only after ddl_reg
    triggers a postback.

    This function performs that postback only when needed.
    """

    if page_contains_sirc_branches(soup):
        print("[INFO] SIRC branch dropdown already loaded.")
        return soup, state

    print("[INFO] SIRC branches not present.")
    print("[INFO] Triggering Southern Region postback...")

    payload = {
        **state,

        "__EVENTTARGET": "ddl_reg",
        "__EVENTARGUMENT": "",

        "ddl_reg": REGION_ID,
        "ddlPou": "",
        "ddl_course": "",
    }

    headers = dict(HEADERS)
    headers["Content-Type"] = "application/x-www-form-urlencoded"

    response = session.post(
        URL,
        data=payload,
        headers=headers,
        timeout=25,
    )

    response.raise_for_status()

    new_soup = BeautifulSoup(response.text, "html.parser")
    new_state = extract_form_state(new_soup)

    if page_contains_sirc_branches(new_soup):
        print("[OK] SIRC branch dropdown loaded successfully.")
    else:
        print(
            "[WARN] SIRC branches still not visible after region postback."
        )

    return new_soup, new_state


# ============================================================
# RESPONSE VALIDATION
# ============================================================

def response_has_aspnet_error(text):
    error_patterns = [
        "Invalid viewstate",
        "Validation of viewstate MAC failed",
        "Invalid postback or callback argument",
        "The state information is invalid",
        "HttpException",
        "Server Error",
    ]

    lowered = text.lower()

    return any(pattern.lower() in lowered for pattern in error_patterns)


# ============================================================
# QUERY PORTAL
# ============================================================

def query_portal(
    session,
    course_id,
    branch_code,
    state,
):
    """
    Submit the Get List form using the latest form state.
    """

    payload = {
        **state,

        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",

        "ddl_reg": REGION_ID,
        "ddlPou": branch_code,
        "ddl_course": course_id,

        "btn_getlist": "Get List",
    }

    headers = dict(HEADERS)
    headers["Content-Type"] = "application/x-www-form-urlencoded"

    response = session.post(
        URL,
        data=payload,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    return response


# ============================================================
# TABLE DETECTION
# ============================================================

def find_batch_table(soup):
    """
    More tolerant than simply looking for one exact table.
    """

    for table in soup.find_all("table"):

        text = " ".join(table.stripped_strings).lower()

        has_batch = (
            "batch no" in text
            or "batch code" in text
        )

        has_seats = (
            "available seats" in text
            or "seats" in text
        )

        if has_batch and has_seats:
            return table

    return None


# ============================================================
# BATCH PARSER
# ============================================================

def parse_batches(table):
    results = []

    rows = table.find_all("tr")

    if not rows:
        return results

    # --------------------------------------------------------
    # Try to identify headers first
    # --------------------------------------------------------

    header_map = {}

    header_row = rows[0]
    header_cells = header_row.find_all(["th", "td"])

    for index, cell in enumerate(header_cells):
        header = re.sub(
            r"\s+",
            " ",
            cell.get_text(" ", strip=True).lower()
        )

        if header:
            header_map[header] = index

    def find_header_index(*possible_names):
        for name in possible_names:
            for header, index in header_map.items():
                if name in header:
                    return index
        return None

    batch_idx = find_header_index(
        "batch no",
        "batch code",
    )

    seats_idx = find_header_index(
        "available seats",
        "seat",
    )

    from_idx = find_header_index(
        "from date",
        "start date",
        "from",
    )

    to_idx = find_header_index(
        "to date",
        "end date",
        "to",
    )

    timings_idx = find_header_index(
        "timings",
        "timing",
        "time",
    )

    pou_idx = find_header_index(
        "pou",
        "place",
        "centre",
        "center",
    )

    status_idx = find_header_index(
        "status",
    )

    # --------------------------------------------------------
    # Fallback to the old ICAI structure
    # --------------------------------------------------------

    if batch_idx is None:
        batch_idx = 0

    if seats_idx is None:
        seats_idx = 1

    if from_idx is None:
        from_idx = 2

    if to_idx is None:
        to_idx = 3

    if timings_idx is None:
        timings_idx = 4

    if pou_idx is None:
        pou_idx = 5

    # Old code expected status around column 10
    if status_idx is None:
        status_idx = 10

    # --------------------------------------------------------
    # Parse actual data rows
    # --------------------------------------------------------

    for row in rows:

        cells = row.find_all("td")

        if len(cells) < 6:
            continue

        cols = [
            re.sub(r"\s+", " ", c.get_text(" ", strip=True))
            for c in cells
        ]

        # Header row
        if cols and "batch no" in cols[0].lower():
            continue

        def safe_get(index, default=""):
            if index is None:
                return default
            if index < 0 or index >= len(cols):
                return default
            return cols[index].strip()

        batch_no = safe_get(batch_idx)

        if not batch_no:
            continue

        batch_data = {
            "batch_no": batch_no,
            "seats": safe_get(seats_idx, "N/A"),
            "from_date": safe_get(from_idx, "N/A"),
            "to_date": safe_get(to_idx, "N/A"),
            "timings": safe_get(timings_idx, "N/A"),
            "pou": safe_get(pou_idx, "N/A"),
            "status": safe_get(status_idx, "Open"),
        }

        results.append(batch_data)

    return results


# ============================================================
# TELEGRAM
# ============================================================

def get_or_create_topic(
    group_id,
    tier,
    topic_name,
    topics_map,
):
    tier_key = tier.upper()

    if tier_key not in topics_map:
        topics_map[tier_key] = {}

    if topic_name in topics_map[tier_key]:
        return topics_map[tier_key][topic_name]

    if not BOT_TOKEN or not group_id:
        print("[WARN] Telegram bot/group not configured.")
        return None

    api_url = (
        f"https://api.telegram.org/bot{BOT_TOKEN}"
        f"/createForumTopic"
    )

    payload = {
        "chat_id": group_id,
        "name": topic_name,
    }

    try:
        response = requests.post(
            api_url,
            json=payload,
            timeout=15,
        )

        data = response.json()

        if data.get("ok"):
            thread_id = data["result"]["message_thread_id"]

            topics_map[tier_key][topic_name] = thread_id

            save_json(
                TOPICS_FILE,
                topics_map,
            )

            print(
                f"[{tier}] Created topic "
                f"'{topic_name}' -> {thread_id}"
            )

            time.sleep(1)

            return thread_id

        print(
            f"[WARN] Could not create topic "
            f"'{topic_name}': {data}"
        )

    except Exception as e:
        print(
            f"[ERROR] Topic creation failed "
            f"'{topic_name}': {e}"
        )

    return None


def send_telegram_alert(
    batch,
    course,
    group_id,
    thread_id,
    max_retries=3,
):
    if not BOT_TOKEN or not group_id:
        return False

    # Escape dynamic values because Telegram is using HTML parse mode
    pou = html.escape(str(batch["pou"]))
    batch_no = html.escape(str(batch["batch_no"]))
    from_date = html.escape(str(batch["from_date"]))
    to_date = html.escape(str(batch["to_date"]))
    timings = html.escape(str(batch["timings"]))
    seats = html.escape(str(batch["seats"]))
    status = html.escape(str(batch["status"]))

    text = (
        f"{course['icon']} "
        f"<b>[SIRC] New ICAI {html.escape(course['name'])} Batch!</b>\n\n"

        f"📍 <b>Centre:</b> {pou}\n"
        f"🆔 <b>Batch Code:</b> <code>{batch_no}</code>\n"
        f"📅 <b>Dates:</b> {from_date} to {to_date}\n"
        f"⏰ <b>Timings:</b> {timings}\n"
        f"💺 <b>Available Seats:</b> {seats}\n"
        f"📌 <b>Status:</b> {status}\n\n"

        f"🔗 <a href='{URL}'>Register on ICAI Portal</a>"
    )

    api_url = (
        f"https://api.telegram.org/bot{BOT_TOKEN}"
        f"/sendMessage"
    )

    payload = {
        "chat_id": group_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    if thread_id:
        payload["message_thread_id"] = thread_id

    for attempt in range(1, max_retries + 1):

        try:
            response = requests.post(
                api_url,
                json=payload,
                timeout=15,
            )

            if response.status_code == 429:

                try:
                    retry_after = (
                        response.json()
                        .get("parameters", {})
                        .get("retry_after", 5)
                    )
                except Exception:
                    retry_after = 5

                print(
                    f"[TELEGRAM] Rate limited. "
                    f"Waiting {retry_after}s..."
                )

                time.sleep(retry_after + 1)
                continue

            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):
                print(
                    f"[TELEGRAM] API returned failure: {data}"
                )
                return False

            print(
                f"[TELEGRAM] Alert sent: "
                f"{batch['batch_no']}"
            )

            time.sleep(1.5)

            return True

        except Exception as e:
            print(
                f"[TELEGRAM] Attempt "
                f"{attempt}/{max_retries} failed: {e}"
            )

            if attempt < max_retries:
                time.sleep(2)

    return False


# ============================================================
# MAIN SCANNER
# ============================================================

def main():

    print("=" * 70)
    print("ICAI SIRC BATCH SCRAPER")
    print("=" * 70)

    if not BOT_TOKEN:
        print(
            "[WARN] TELEGRAM_BOT_TOKEN environment variable "
            "is not set."
        )

    seen_batches = set(
        load_json(
            SEEN_DATA_FILE,
            []
        )
    )

    topics_map = load_json(
        TOPICS_FILE,
        {
            "INTER": {},
            "FINAL": {},
        }
    )

    newly_seen = set()

    session = requests.Session()
    session.headers.update(HEADERS)

    # --------------------------------------------------------
    # INITIAL GET
    # --------------------------------------------------------

    print("\n[1] Opening ICAI portal...")

    try:
        page_html, soup, state = get_current_page(session)

        print("[OK] Initial page loaded.")
        print(
            f"[DEBUG] ViewState length: "
            f"{len(state['__VIEWSTATE'])}"
        )
        print(
            f"[DEBUG] EventValidation length: "
            f"{len(state['__EVENTVALIDATION'])}"
        )

    except Exception as e:
        print(f"[FATAL] Initial GET failed: {e}")
        return

    # --------------------------------------------------------
    # LOAD SIRC BRANCH DROPDOWN
    # --------------------------------------------------------

    try:
        soup, state = select_region(
            session,
            soup,
            state,
        )

    except Exception as e:
        print(
            f"[FATAL] Could not initialise "
            f"Southern Region: {e}"
        )
        return

    # --------------------------------------------------------
    # OPTIONAL DEBUG
    # --------------------------------------------------------

    branch_options = get_select_values(
        soup,
        "ddlPou",
    )

    print(
        f"[DEBUG] Branch options currently loaded: "
        f"{len(branch_options)}"
    )

    # This catches the region-ID problem immediately.
    expected_sample = ["101", "102", "111", "251"]

    for code in expected_sample:
        if code in branch_options:
            print(
                f"[DEBUG] Branch code {code} loaded "
                f"as '{branch_options[code]}'"
            )

    # --------------------------------------------------------
    # COURSE LOOP
    # --------------------------------------------------------

    for course in COURSES_TO_CHECK:

        print()
        print("=" * 70)
        print(
            f"SCANNING SIRC [{course['tier']}] "
            f"{course['name']}"
        )
        print("=" * 70)

        # ----------------------------------------------------
        # Branch loop
        # ----------------------------------------------------

        for branch_name, branch_code in BRANCHES_TO_CHECK.items():

            try:

                print(
                    f"\n[{course['name']}] "
                    f"{branch_name} ({branch_code})"
                )

                # --------------------------------------------
                # Check whether branch exists in current state
                # --------------------------------------------

                if (
                    branch_options
                    and branch_code not in branch_options
                ):
                    print(
                        f"  [WARN] Branch code {branch_code} "
                        f"is not in current ddlPou."
                    )

                    print(
                        "  [INFO] Refreshing SIRC region state..."
                    )

                    page_html, soup, state = get_current_page(
                        session
                    )

                    soup, state = select_region(
                        session,
                        soup,
                        state,
                    )

                    branch_options = get_select_values(
                        soup,
                        "ddlPou",
                    )

                # --------------------------------------------
                # Query selected branch
                # --------------------------------------------

                response = query_portal(
                    session,
                    course["id"],
                    branch_code,
                    state,
                )

                response_text = response.text

                # --------------------------------------------
                # ASP.NET state failure
                # --------------------------------------------

                if response_has_aspnet_error(response_text):

                    print(
                        "  [WARN] ASP.NET state error detected."
                    )

                    print(
                        "  [INFO] Refreshing session/tokens..."
                    )

                    page_html, soup, state = get_current_page(
                        session
                    )

                    soup, state = select_region(
                        session,
                        soup,
                        state,
                    )

                    branch_options = get_select_values(
                        soup,
                        "ddlPou",
                    )

                    response = query_portal(
                        session,
                        course["id"],
                        branch_code,
                        state,
                    )

                    response_text = response.text

                # --------------------------------------------
                # Extract fresh state from returned page
                # --------------------------------------------

                result_soup = BeautifulSoup(
                    response_text,
                    "html.parser",
                )

                new_state = extract_form_state(
                    result_soup
                )

                if (
                    new_state["__VIEWSTATE"]
                    and new_state["__EVENTVALIDATION"]
                ):
                    # Keep rolling forward with the latest state.
                    state = new_state

                # --------------------------------------------
                # Detect batch table
                # --------------------------------------------

                table = find_batch_table(
                    result_soup
                )

                if not table:

                    body_text = " ".join(
                        result_soup.stripped_strings
                    ).lower()

                    if (
                        "no record" in body_text
                        or "no batch" in body_text
                        or "record not found" in body_text
                    ):
                        print(
                            "  -> 0 active batches"
                        )
                    else:
                        print(
                            "  -> NO TABLE FOUND"
                        )

                        print(
                            f"  [DEBUG] HTTP status: "
                            f"{response.status_code}"
                        )

                        title = (
                            result_soup.title.get_text(
                                strip=True
                            )
                            if result_soup.title
                            else "No title"
                        )

                        print(
                            f"  [DEBUG] Page title: {title}"
                        )

                        # Useful when debugging SIRC specifically.
                        if "invalid" in body_text:
                            print(
                                "  [DEBUG] Response contains "
                                "'invalid'."
                            )

                    continue

                # --------------------------------------------
                # Parse batches
                # --------------------------------------------

                batches = parse_batches(table)

                print(
                    f"  -> FOUND {len(batches)} BATCHES"
                )

                if not batches:
                    continue

                # --------------------------------------------
                # Telegram topic
                # --------------------------------------------

                branch_key = branch_name.upper()

                topic_title = (
                    HIGH_DENSITY_BRANCHES.get(
                        branch_key,
                        CATCH_ALL_TOPIC_NAME,
                    )
                )

                thread_id = get_or_create_topic(
                    course["group_id"],
                    course["tier"],
                    topic_title,
                    topics_map,
                )

                # --------------------------------------------
                # Alert new batches
                # --------------------------------------------

                for batch in batches:

                    batch_id = batch["batch_no"]

                    if batch_id in seen_batches:
                        continue

                    success = send_telegram_alert(
                        batch,
                        course,
                        course["group_id"],
                        thread_id,
                    )

                    if success:
                        seen_batches.add(
                            batch_id
                        )

                        newly_seen.add(
                            batch_id
                        )

            except requests.RequestException as e:

                print(
                    f"  [HTTP ERROR] "
                    f"{branch_name}: {e}"
                )

                # Give the server/session a little breathing room.
                time.sleep(2)

            except Exception as e:

                print(
                    f"  [ERROR] "
                    f"{course['name']} @ "
                    f"{branch_name}: {e}"
                )

        # Small pause between courses.
        time.sleep(1)

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    if newly_seen:

        save_json(
            SEEN_DATA_FILE,
            sorted(seen_batches),
        )

        print()
        print(
            f"[SIRC] Run complete. "
            f"{len(newly_seen)} new batches recorded."
        )

    else:

        print()
        print(
            "[SIRC] Run complete. "
            "No new batches."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
