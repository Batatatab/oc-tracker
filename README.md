# oc-tracker

ICAI Batch Monitor (5-Region)
A fully automated, zero-server batch tracking bot for the official ICAI registration portal (icaionlineregistration.org). It polls all five regional councils (NIRC, WIRC, EIRC, SIRC, CIRC) concurrently on GitHub Actions and pushes real-time seat alerts directly into dedicated Telegram Supergroup Forum Topics.

Note on code origin: This entire repo was vibecoded—built through iterative prompts, reverse-engineering legacy ASP.NET postbacks, and hotfixing runtime edge cases until it worked without human intervention.

Why This Exists
The ICAI batch registration portal is notoriously painful to track:
Seats for mandatory GMCS/MCS, Adv ITT, OC, and ITT batches fill within minutes.
The site has no RSS feeds, webhooks, or push notifications.
The UI runs on legacy ASP.NET WebForms with encrypted __VIEWSTATE and dynamic __EVENTVALIDATION payloads that reject naive scrapers with HTTP 500 errors.
This project bypasses manual refreshing entirely.

Features
All 5 Regions Covered: Monitors NIRC, WIRC, EIRC, SIRC, and CIRC simultaneously.
Split Supergroup Routing: Inter courses (OC, ITT) and Final courses (Adv ITT, MCS, Weekend MCS) route to separate Telegram supergroups.
Dynamic Telegram Forum Topics:
High-density cities get dedicated city threads (e.g., 🏢 Mumbai, 🏛️ Pune, 💻 Bengaluru, 🏰 Jaipur).
Smaller tier-2/tier-3 branches automatically route into a shared 📍 Other Branches topic.
Topics are provisioned on-the-fly only when a batch actually exists (no ghost threads).
Self-healing: If someone deletes a Telegram topic, the bot catches the 400 Bad Request, recreates the topic, updates its internal cache, and delivers the alert.
Serverless & Free: Runs entirely on GitHub Actions runners using scheduled cron triggers.
Flat-File State Storage: No external databases (Postgres, Redis, Firebase) needed. Alert state and topic IDs are tracked via JSON files committed directly back to the repo via github-actions[bot].
Fault-Tolerant Parallelism: All five regional scripts run concurrently. A network hiccup or portal crash in one region will not block or abort the state commits of the other four.

Repository Structure
├── .github/workflows/
│   └── checker.yml         # GitHub Actions cron scheduler & runner
├── scraper_nirc.py         # Northern region scraper
├── scraper_wirc.py         # Western region scraper
├── scraper_eirc.py         # Eastern region scraper
├── scraper_sirc.py         # Southern region scraper
├── scraper_circ.py         # Central region scraper
├── requirements.txt        # requests, beautifulsoup4
├── seen_batches_*.json     # Deduplication history for each region
└── topics_*.json           # Telegram topic thread ID mappings

Setup & Deployment
1. Clone & Configure Telegram
Create a bot using @BotFather and save your bot token.
Create your Telegram supergroups (e.g., one for Inter, one for Final).
Enable Topics in the supergroup settings (Edit → Topics → toggle On).
Add your bot as an Administrator with Manage Topics and Post Messages permissions.
Retrieve your supergroup Chat IDs (usually formatted as -100xxxxxxxxxx).
Update GROUP_INTER_ID and GROUP_FINAL_ID in the respective scraper_*.py files.

Technical Gotchas Solved During "Vibecoding"
-ASP.NET 2-Step Handshake: The portal populates branch IDs dynamically based on the region dropdown. Querying branches directly using the initial page tokens triggers an IIS crash. The scripts run a dynamic postback handshake (GET session $\rightarrow$ POST region selection $\rightarrow$ extract signed tokens) with a hardcoded pre-signed fallback.
-HTML Sanitization: Raw portal data often contains unescaped ampersands (&) in branch names or notes that crash Telegram's HTML parse engine. All dynamic text is wrapped through html.escape().
-Git Merge Races: Concurrently updated state files are reconciled with an autostashed rebase step (git pull --rebase --autostash origin main) right before pushing to GitHub.
