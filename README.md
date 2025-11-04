🧠 DevOps Job Bot – Automated Job Finder (Resume-Aware)

Author: Jay Porwal

Role: Associate Cloud & DevOps Engineer
Tech: Python • Docker • Telegram Bot • Scraping • Automation

🚀 Overview

DevOps Job Bot is an intelligent job-scraping and alert system that automatically finds the most relevant DevOps & Cloud Engineer jobs/internships from multiple platforms — LinkedIn, Naukri, Indeed, and Internshala — and sends them directly to your Telegram every few hours.

✅ Multi-Platform Scraping

Collects latest job listings from LinkedIn, Indeed, Naukri, and Internshala.

Filters listings from the past 7 days only.

✅ Resume-Aware Filtering

Matches jobs to your personal resume keywords (DevOps, AWS, Docker, Terraform, etc.).

Calculates a relevance score for every job and ranks results accordingly.

✅ Smart Job Classification

Automatically detects job experience level (Fresher / Junior / Mid / Senior).

Detects if the job has an Easy Apply option or redirects to an external site.

✅ Telegram Job Notifications

Sends each new, relevant job directly to your Telegram chat in clean HTML format.

Includes job title, company, location, experience level, match score, and apply type.

✅ Automation & Deduplication

Runs every SCRAPE_INTERVAL_MINUTES (default: 30).

Keeps track of sent jobs in data/seen_jobs.json to avoid duplicates.

Logs all activity in logs/bot.log.

🧩 Project Structure
devops-job-bot/
├── bot.py                        # Main scheduler and resume-aware filter logic
├── scraper/
│   ├── linkedin_scraper.py       # LinkedIn scraper
│   ├── naukri_scraper.py         # Naukri scraper
│   ├── indeed_scraper.py         # Indeed scraper
│   └── internshala_scraper.py    # Internshala scraper
├── utils/
│   └── telegram_utils.py         # Telegram send function
├── data/
│   └── seen_jobs.json            # Stores IDs of already sent jobs
├── logs/
│   └── bot.log                   # Scheduler logs
├── .env                          # Environment variables (Telegram tokens, etc.)
├── requirements.txt              # Python dependencies
└── README.md                     # Project documentation (you’re reading it)

⚙️ Installation
1️⃣ Clone the Repository
git clone https://github.com/JAYPORWAL/devops-job-bot.git
cd devops-job-bot

2️⃣ Create a Virtual Environment
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux / Mac

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Configure Environment Variables

Create a .env file in the project root:

TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
SCRAPE_INTERVAL_MINUTES=30


💡 To get your Telegram Chat ID:

Open Telegram → search for @userinfobot

Type /start → copy your chat ID.

💡 To create a Telegram Bot Token:

Open Telegram → search for @BotFather

Type /newbot → follow steps → copy the token.

▶️ Running the Bot
Run manually
python bot.py


The bot will:

Start all scrapers.

Filter jobs based on your DevOps resume.

Send top matches to your Telegram every 30 minutes (or as per .env).

You’ll see logs like:

INFO Starting DevOps Job Bot (resume-aware)
INFO Fetched 87 total job candidates
INFO 45 jobs after date filter (7 days)
INFO Sent job: DevOps Engineer - XYZ Ltd (score=6)

🧠 How It Works
Step	Process	Description
1️⃣	Scrape	Fetch jobs from LinkedIn, Naukri, Indeed, Internshala
2️⃣	Filter	Keep only recent (last 7 days)
3️⃣	Score	Match against your resume keywords (AWS, GCP, Docker, Terraform, etc.)
4️⃣	Classify	Detect experience level & apply method
5️⃣	Notify	Send HTML message to Telegram
6️⃣	Store	Save job IDs to seen_jobs.json to avoid duplicates
📊 Job Scoring Logic
Match Type	Example Keywords	Weight
Role Keywords	DevOps Engineer, Associate DevOps, Cloud Engineer	+3
Skills Keywords	AWS, GCP, Docker, CI/CD, Terraform, GitHub Actions	+1 each
Internship Match	Intern, Internship, Trainee	+2
Source Boost	LinkedIn / Naukri / Indeed / Internshala	+1

🔴 High Match = Score ≥ 6
🟠 Good Match = Score 3–5
🟢 Possible Match = Score 1–2

📬 Telegram Message Example
DevOps Engineer
XYZ Pvt Ltd — Bengaluru
LinkedIn • 2 days ago

Built CI/CD pipelines using AWS and Docker...

Relevance: 🔴 High match (score 8)
Matched: devops engineer, aws, docker, ci/cd, github actions
Experience: Fresher/Entry
How to apply: Easy Apply (LinkedIn)
➡️ View / Apply

🧾 Logging & Debugging

All logs are stored in logs/bot.log

To view live logs:

tail -f logs/bot.log   # Linux/Mac
Get-Content logs\bot.log -Wait   # Windows

🛑 Start / Stop the Bot
Action	Command
Start Bot	python bot.py
Stop Bot	Ctrl + C
Background Run (Linux)	nohup python bot.py &
View Logs	tail -f logs/bot.log
🔧 Customization

Change interval:
Update .env → SCRAPE_INTERVAL_MINUTES=60 for hourly checks.

Add or remove skills:
Edit the list RESUME_KEYWORDS and ROLE_KEYWORDS in bot.py.

Focus only on internships:
Change the search keywords in scrapers to "DevOps Internship".

Raise filter strictness:
In bot.py, find:

if job.get("score", 0) < 1:
    continue


and change 1 → 3 to only send top-relevant jobs.

🧰 Requirements

Python 3.8+

Libraries:

requests
beautifulsoup4
apscheduler
python-dotenv
html5lib


(These are already in requirements.txt.)

👨‍💻 Author

Jay Porwal
Associate Cloud & DevOps Engineer
📧 jayporwal3101@gmail.com

🌐 GitHub
 | LinkedIn