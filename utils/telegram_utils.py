# utils/telegram_utils.py
import requests
import logging
import html

logger = logging.getLogger(__name__)

class TelegramNotifier:
    API_URL = "https://api.telegram.org/bot{token}/{method}"

    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    def send(self, text, **kwargs):
        url = self.API_URL.format(token=self.token, method="sendMessage")
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        payload.update(kwargs)
        r = requests.post(url, data=payload, timeout=15)
        if r.status_code != 200:
            logger.warning("Telegram API returned %s: %s", r.status_code, r.text)
            r.raise_for_status()
        return r.json()

    def send_job(self, job):
        # Format job as HTML message
        title = html.escape(job.get("title") or "Untitled")
        company = html.escape(job.get("company") or "")
        location = html.escape(job.get("location") or "")
        snippet = html.escape((job.get("snippet") or "")[:800])  # limit length
        link = job.get("link") or ""
        posted = html.escape(job.get("posted_text") or "")

        # Create message
        msg = f"<b>{title}</b>\n"
        if company:
            msg += f"{company}\n"
        if location:
            msg += f"{location}\n"
        if posted:
            msg += f"<i>Posted:</i> {posted}\n"
        if snippet:
            msg += f"\n{snippet}\n"
        if link:
            msg += f"\n\u21AA <a href=\"{html.escape(link)}\">Apply / View</a>"

        return self.send(msg)
