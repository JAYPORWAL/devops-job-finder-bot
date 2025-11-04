import os
import logging
import html
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.error import TimedOut

# ✅ Import your scraper classes
from scraper.linkedin_scraper import LinkedInScraper
from scraper.indeed_scraper import IndeedScraper
from scraper.naukri_scraper import NaukriScraper
from scraper.internshala_scraper import InternshalaScraper

# -------------------------------------------------------------------
# Load environment variables
# -------------------------------------------------------------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# -------------------------------------------------------------------
# Logging setup
# -------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Job fetching logic
# -------------------------------------------------------------------
def fetch_jobs(platform="all"):
    """Fetch DevOps jobs from selected platforms."""
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
        logger.error(f"❌ Error while scraping {platform}: {e}")
    return all_jobs

# -------------------------------------------------------------------
# /start command — Welcome message + platform selection
# -------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message and job platform options."""
    user = update.effective_user
    welcome_text = (
        f"👋 Hello {html.escape(user.first_name or 'there')}!\n\n"
        "🤖 <b>Welcome to DevOps Job Bot!</b>\n\n"
        "I help you find the latest <b>DevOps Internships</b> & <b>Jobs</b> "
        "from top platforms in real time.\n\n"
        "✅ <b>Features:</b>\n"
        "• Find jobs from LinkedIn, Indeed, Naukri & Internshala\n"
        "• Instant apply links\n"
        "• Fresh, verified postings\n\n"
        "👇 Choose a platform to get started!"
    )

    keyboard = [
        [
            InlineKeyboardButton("💼 Indeed", callback_data="platform_indeed"),
            InlineKeyboardButton("🔗 LinkedIn", callback_data="platform_linkedin"),
        ],
        [
            InlineKeyboardButton("🧭 Naukri", callback_data="platform_naukri"),
            InlineKeyboardButton("🌐 All Platforms", callback_data="platform_all"),
        ],
    ]

    await update.message.reply_text(
        welcome_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# -------------------------------------------------------------------
# Handle platform choice
# -------------------------------------------------------------------
async def handle_platform_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and display jobs when user selects a platform."""
    query = update.callback_query
    await query.answer()
    platform = query.data.replace("platform_", "")

    await query.edit_message_text(
        f"🔍 Fetching latest <b>DevOps</b> jobs from <b>{platform.capitalize()}</b>...",
        parse_mode="HTML",
    )

    try:
        jobs = await asyncio.to_thread(fetch_jobs, platform)  # run scraping in thread
        if not jobs:
            await query.message.reply_text("⚠️ No jobs found right now. Try again later.")
            return

        await query.message.reply_text(
            f"📢 Found {len(jobs)} jobs! Showing top 5 results:"
        )

        # Send top 5 results with safe pacing
        for job in jobs[:5]:
            title = html.escape(job.get("title", "Untitled"))
            company = html.escape(job.get("company", "Unknown"))
            location = html.escape(job.get("location", "Not specified"))
            link = job.get("link", "#")

            job_text = (
                f"💼 <b>{title}</b>\n"
                f"🏢 {company}\n"
                f"📍 {location}\n"
                f"🔗 <a href='{html.escape(link)}'>Apply Now</a>"
            )

            try:
                await query.message.reply_text(
                    job_text, parse_mode="HTML", disable_web_page_preview=True
                )
                await asyncio.sleep(1.5)  # prevent Telegram flood limits
            except TimedOut:
                logger.warning("⚠️ Telegram timeout while sending message. Retrying...")
                await asyncio.sleep(3)

        await query.message.reply_text(
            "✅ Done! You can type /start to search again anytime."
        )

    except Exception as e:
        logger.error(f"❌ Error while handling {platform}: {e}")
        await query.message.reply_text("⚠️ Something went wrong. Please try again later.")

# -------------------------------------------------------------------
# /help command — list available commands
# -------------------------------------------------------------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🧠 <b>DevOps Job Bot Help</b>\n\n"
        "Here’s what I can do for you:\n\n"
        "🔹 /start — Start and choose a job platform\n"
        "🔹 /help — Show this help message\n\n"
        "💡 Tip: You can restart anytime using /start.\n\n"
        "Happy job hunting! 🚀"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")

# -------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------
def main():
    if not TELEGRAM_TOKEN:
        raise SystemExit("❌ Missing TELEGRAM_BOT_TOKEN in .env file!")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_platform_choice))

    logger.info("🚀 DevOps Job Bot started successfully and is now polling for updates...")
    app.run_polling()

# -------------------------------------------------------------------
# Run the bot
# -------------------------------------------------------------------
if __name__ == "__main__":
    main()
