import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)
from scraper.linkedin_scraper import LinkedInScraper
from scraper.indeed_scraper import IndeedScraper
from scraper.naukri_scraper import NaukriScraper
from scraper.internshala_scraper import InternshalaScraper

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -----------------------
# Job fetching function
# -----------------------
def fetch_jobs(platform="all"):
    all_jobs = []
    try:
        if platform in ("linkedin", "all"):
            all_jobs += LinkedInScraper().search("DevOps Engineer")
        if platform in ("indeed", "all"):
            all_jobs += IndeedScraper().search("DevOps Engineer")
        if platform in ("naukri", "all"):
            all_jobs += NaukriScraper().search("DevOps Engineer")
        if platform in ("internshala", "all"):
            all_jobs += InternshalaScraper().search("DevOps")
    except Exception as e:
        logger.error(f"Error while scraping: {e}")
    return all_jobs

# -----------------------
# Telegram Commands
# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends welcome + platform selection"""
    user = update.effective_user
    welcome_text = (
        f"👋 Hello {user.first_name or 'there'}!\n\n"
        "🤖 <b>Welcome to DevOps Job Bot!</b>\n\n"
        "I help you find the latest <b>DevOps Internships</b> & <b>Jobs</b> "
        "from top platforms in real-time!\n\n"
        "✅ <b>Features:</b>\n"
        "• Find jobs from LinkedIn, Indeed, Naukri & Internshala\n"
        "• Get one-click apply links\n"
        "• Latest postings only\n\n"
        "👉 Choose a platform below to start searching 👇"
    )

    keyboard = [
        [InlineKeyboardButton("💼 Indeed", callback_data="platform_indeed"),
         InlineKeyboardButton("🔗 LinkedIn", callback_data="platform_linkedin")],
        [InlineKeyboardButton("🧭 Naukri", callback_data="platform_naukri"),
         InlineKeyboardButton("🌐 All Platforms", callback_data="platform_all")],
    ]
    await update.message.reply_text(
        welcome_text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_platform_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch jobs based on user's choice"""
    query = update.callback_query
    await query.answer()
    platform = query.data.replace("platform_", "")

    await query.edit_message_text(
        f"🔍 Fetching latest jobs from <b>{platform.capitalize()}</b>...",
        parse_mode="HTML"
    )

    jobs = fetch_jobs(platform)
    if not jobs:
        await query.message.reply_text("⚠️ No jobs found right now. Try again later.")
        return

    await query.message.reply_text(f"📢 Found {len(jobs)} jobs! Showing top 5 results:")

    for job in jobs[:5]:
        title = job.get("title", "Untitled")
        company = job.get("company", "Unknown")
        location = job.get("location", "Not specified")
        link = job.get("link", "#")

        job_text = (
            f"💼 <b>{title}</b>\n"
            f"🏢 {company}\n"
            f"📍 {location}\n"
            f"🔗 <a href='{link}'>Apply Now</a>"
        )
        await query.message.reply_text(job_text, parse_mode="HTML")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays all available commands"""
    help_text = (
        "🧠 <b>DevOps Job Bot Help</b>\n\n"
        "Here’s what I can do for you:\n\n"
        "🔹 /start – Start the bot and choose a job platform\n"
        "🔹 /help – Show this help menu\n\n"
        "💡 Tip: You can restart anytime using /start.\n\n"
        "Happy job hunting! 🚀"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")

# -----------------------
# Main function
# -----------------------
def main():
    if not TELEGRAM_TOKEN:
        raise SystemExit("❌ Missing TELEGRAM_BOT_TOKEN in .env")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_platform_choice))

    logger.info("🚀 DevOps Job Bot started successfully!")
    app.run_polling()

if __name__ == "__main__":
    main()
