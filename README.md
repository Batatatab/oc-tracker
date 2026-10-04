# oc-tracker

# ICAI Batch Monitor

A simple automation bot that checks `icaionlineregistration.org` for newly added batches and sends alerts to Telegram group topics.

I basically vibecoded this whole thing because checking the ICAI portal manually all day for OC, ITT, Adv ITT, and MCS seats was exhausting, and seats always fill up in minutes.

---

### What it does

- Scrapes all 5 regions: NIRC, WIRC, EIRC, SIRC, and CIRC.
- Covers Inter (Orientation Course & ITT) and Final (Adv ITT & MCS).
- Automatically posts alerts into city-specific Telegram forum topics (and sends smaller branches to an "Other Branches" topic).
- Saves alerted batches in JSON files so you don't get pinged twice for the same batch.
- Runs all 5 regional scrapers in parallel.
- Automatically checks for new batches every 15 minutes.

---

### Files in this repo

- `scraper_circ.py` - Central region scraper
- `scraper_nirc.py` - Northern region scraper
- `scraper_wirc.py` - Western region scraper
- `scraper_eirc.py` - Eastern region scraper
- `scraper_sirc.py` - Southern region scraper
- `.github/workflows/checker.yml` - GitHub Actions workflow that runs all scrapers in parallel
- `seen_batches_*.json` - Keeps track of already alerted batches
- `topics_*.json` - Stores Telegram topic IDs so it doesn't create duplicate topics
- `requirements.txt` - Python packages needed (`requests`, `beautifulsoup4`)

---

### How to set it up

#### 1. Fork or clone this repo

```bash
git clone https://github.com/Batatatab/oc-tracker.git
cd oc-tracker


```

#### 2. Install dependencies locally (optional)
```bash
pip install -r requirements.txt
```

#### 3. Telegram Bot Setup
1. Create a bot using [@BotFather](https://t.me/BotFather) and copy your bot token.
2. Create your Telegram Supergroup and turn on **Topics** in group settings.
3. Add your bot as an admin and give it the **Manage Topics** permission.
4. Open the `scraper_*.py` files and put your group IDs in `GROUP_INTER_ID` and `GROUP_FINAL_ID`.

#### 4. GitHub Actions Setup
1. Go to your repo **Settings** -> **Secrets and variables** -> **Actions**.
2. Click **New repository secret**, name it `TELEGRAM_BOT_TOKEN`, and paste your token.
3. Go to **Settings** -> **Actions** -> **General** -> scroll down to **Workflow permissions**.
4. Select **Read and write permissions** and click **Save** (this allows the action to commit updated JSON files).

#### 5. Run it
- Go to the **Actions** tab on your GitHub repo.
- Select **ICAI Multi-Region Batch Checker**.
- Click **Run workflow** to test it out manually.
- When enabled, it runs automatically every 15 minutes.

---
⏰ Automatic Scheduling

The workflow is triggered externally using cron-job.org.
GitHub's built-in scheduled workflows weren't reliably triggering, so I use cron-job.org to call GitHub's workflow_dispatch API instead.

The current schedule is:
 */15 6-22 * * *

Timezone: Asia/Kolkata
 
This triggers the workflow every 15 minutes from 6:00 AM to 10:45 PM IST, every day.
The scheduler only starts the GitHub workflow. The actual scraping happens inside GitHub Actions.

 
## 📲 Telegram Alerts

The scraper can send batch availability alerts directly to Telegram.

There are separate groups for **Intermediate** and **Final**, with forum topics organized by city/branch so you can receive only the alerts relevant to you.

### WIRC — Western India Regional Council
- **Inter (OC & ITT):** https://t.me/WIRCINTERreminder
- **Final (Adv. ITT & MCS):** https://t.me/WIRCFINALreminder

### NIRC — Northern India Regional Council
- **Inter (OC & ITT):** https://t.me/NIRCINTERreminder
- **Final (Adv. ITT & MCS):** https://t.me/NIRCFINALreminder

### CIRC — Central India Regional Council
- **Inter (OC & ITT):** https://t.me/CIRCINTERreminder
- **Final (Adv. ITT & MCS):** https://t.me/CIRCFINALreminder

### SIRC — Southern India Regional Council
- **Inter (OC & ITT):** https://t.me/SIRCINTERreminder
- **Final (Adv. ITT & MCS):** https://t.me/SIRCFINALreminder

### EIRC — Eastern India Regional Council
- **Inter (OC & ITT):** https://t.me/EIRCINTERreminder
- **Final (Adv. ITT & MCS):** https://t.me/EIRCFINALreminder

### How it works

1. Join the group for your **course and region**.
2. Open the **Start Here** topic to find your branch/city.
3. Smaller branches that don't have their own topic are routed to **Other Branches**.
4. Mute the rest of the group and unmute only your relevant topic if you want to avoid unnecessary notifications.

Each alert contains the **batch number, batch dates, available seats, and a direct registration link**.

No ICAI login or credentials are required. The scraper only reads the publicly available batch schedule and does not access user accounts.

> **Note:** The Telegram alerts are completely free. The project is open source.

### Disclaimer

This is an unofficial student project made to help track batch openings. It is not affiliated with or endorsed by ICAI. Always check the official ICAI portal directly before booking or making travel arrangements.


