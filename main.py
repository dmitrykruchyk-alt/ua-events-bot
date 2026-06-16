"""
UA Events Bot v2.5
- Прибрано Playwright (kontramarka) — занадто важкий для 256MB
- Залишено тільки легкі BS4-скрапери
"""

import asyncio
import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from telegram.constants import ParseMode

from scrapers.bravo_vip import scrape_bravo_vip
from scrapers.karabas import scrape_karabas
from scrapers.generic_bs4 import scrape_generic
from utils.storage import Storage
from utils.formatter import format_event_message
from utils.ru_filter import is_russian_content

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("main")

BOT_TOKEN   = os.environ["BOT_TOKEN"]
CHANNEL_ID  = os.environ["CHANNEL_ID"]
CHECK_HOURS = int(os.getenv("CHECK_HOURS", "6"))
PORT        = int(os.getenv("PORT", "8080"))

SCRAPERS = [
    # ── Квиткові платформи (легкі BS4) ───────────────────────
    ("bravo.vip",        scrape_bravo_vip),
    ("mticket.eu",       lambda: scrape_generic("mticket.eu")),

    # ── KARABAS мережа ────────────────────────────────────────
    ("karabas.pl",       lambda: scrape_karabas("pl")),
    ("karabas.cz",       lambda: scrape_karabas("cz")),
    ("karabas.de",       lambda: scrape_karabas("de")),
    ("karabas.ch",       lambda: scrape_karabas("ch")),
    ("karabas.it",       lambda: scrape_karabas("it")),
    ("karabas.es",       lambda: scrape_karabas("es")),
    ("karabas.dk",       lambda: scrape_karabas("dk")),
    ("karabas.co",       lambda: scrape_karabas("co")),

    # kontramarka.com — ВИМКНЕНО (потребує Playwright/256MB недостатньо)
]

storage = Storage(os.getenv("DB_PATH", "events.db"))
bot     = Bot(token=BOT_TOKEN)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"UA Events Bot is running")
    def log_message(self, format, *args):
        pass


def start_http_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    log.info(f"HTTP server на порту {PORT}")
    server.serve_forever()


async def run_all_scrapers():
    log.info(f"▶ Перевірка {len(SCRAPERS)} джерел...")
    new_total = 0

    for source_name, scraper_fn in SCRAPERS:
        try:
            log.info(f"  [{source_name}]...")
            events = await asyncio.to_thread(scraper_fn)
            log.info(f"  [{source_name}] знайдено: {len(events)}")

            for event in events:
                if is_russian_content(event):
                    log.warning(f"  ⛔ RU: {event.get('title','?')[:50]}")
                    continue

                event_id = storage.make_id(event)
                if storage.exists(event_id):
                    continue

                storage.save(event_id, event)
                await send_notification(event, source_name)
                new_total += 1
                await asyncio.sleep(0.4)

        except Exception as e:
            log.error(f"  ❌ [{source_name}]: {e}", exc_info=True)

    log.info(f"✅ Готово. Нових: {new_total} | В базі: {storage.count()}")


async def send_notification(event: dict, source: str):
    text = format_event_message(event, source)
    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        )
        log.info(f"  📨 {event.get('title','?')[:55]}")
    except Exception as e:
        log.error(f"  ❌ send: {e}")


async def main():
    log.info("🤖 UA Events Bot v2.5")
    log.info(f"   Канал:    {CHANNEL_ID}")
    log.info(f"   Джерел:   {len(SCRAPERS)}")
    log.info(f"   Інтервал: кожні {CHECK_HOURS} год.")

    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()

    await run_all_scrapers()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_all_scrapers, "interval", hours=CHECK_HOURS)
    scheduler.start()

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        log.info("🛑 Зупинено")


if __name__ == "__main__":
    asyncio.run(main())
