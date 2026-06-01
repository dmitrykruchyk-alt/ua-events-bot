"""
UA Events Bot v2.2
- Видалено visitukraine.today
- AI-фільтр через Claude API для всіх загальних джерел
"""

import asyncio
import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from telegram.constants import ParseMode

from scrapers.kontramarka import scrape_kontramarka
from scrapers.bravo_vip import scrape_bravo_vip
from scrapers.karabas import scrape_karabas
from scrapers.generic_bs4 import scrape_generic
from scrapers.ticketmaster_api import scrape_ticketmaster
from utils.storage import Storage
from utils.formatter import format_event_message
from utils.ru_filter import is_russian_content
from utils.ua_allowlist import is_ukrainian_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("main")

BOT_TOKEN   = os.environ["BOT_TOKEN"]
CHANNEL_ID  = os.environ["CHANNEL_ID"]
CHECK_HOURS = int(os.getenv("CHECK_HOURS", "6"))

SCRAPERS = [
    # ── Квиткові платформи (тільки укр. артисти) ──────────────
    ("kontramarka.com",     scrape_kontramarka),
    ("bravo.vip",           scrape_bravo_vip),
    ("mticket.eu",          lambda: scrape_generic("mticket.eu")),

    # ── KARABAS мережа (тільки укр. артисти) ──────────────────
    ("karabas.pl",          lambda: scrape_karabas("pl")),
    ("karabas.cz",          lambda: scrape_karabas("cz")),
    ("karabas.de",          lambda: scrape_karabas("de")),
    ("karabas.ch",          lambda: scrape_karabas("ch")),
    ("karabas.it",          lambda: scrape_karabas("it")),
    ("karabas.es",          lambda: scrape_karabas("es")),
    ("karabas.dk",          lambda: scrape_karabas("dk")),
    ("karabas.co",          lambda: scrape_karabas("co")),

    # ── Культурні центри діаспори (безпечні) ──────────────────
    ("hilfe-ua.de",         lambda: scrape_generic("hilfe-ua.de")),
    ("ukrainischeshaus.de", lambda: scrape_generic("ukrainischeshaus.de")),
    ("ukrainskidom.pl",     lambda: scrape_generic("ukrainskidom.pl")),
    ("naszvybir.pl",        lambda: scrape_generic("naszvybir.pl")),
    ("ukrainci.cz",         lambda: scrape_generic("ukrainci.cz")),
    ("uccc.cz",             lambda: scrape_generic("uccc.cz")),
    ("ukrainet.eu",         lambda: scrape_generic("ukrainet.eu")),

    # visitukraine.today — ВИДАЛЕНО (нерелевантний контент)

    # ── API ───────────────────────────────────────────────────
    ("ticketmaster",        scrape_ticketmaster),
]

storage = Storage(os.getenv("DB_PATH", "events.db"))
bot     = Bot(token=BOT_TOKEN)


async def run_all_scrapers():
    log.info(f"▶ Перевірка {len(SCRAPERS)} джерел...")
    new_total = 0

    for source_name, scraper_fn in SCRAPERS:
        try:
            log.info(f"  [{source_name}]...")
            events = await asyncio.to_thread(scraper_fn)
            log.info(f"  [{source_name}] знайдено: {len(events)}")

            for event in events:
                # 1. Фільтр RU-контенту
                if is_russian_content(event):
                    log.warning(f"  ⛔ RU: {event.get('title','?')[:50]}")
                    continue

                # 2. Фільтр — тільки українські події
                if not is_ukrainian_event(event):
                    log.info(f"  ⏭ Не укр.: {event.get('title','?')[:50]}")
                    continue

                # 3. Дедублікація
                event_id = storage.make_id(event)
                if storage.exists(event_id):
                    continue

                # 4. Зберегти і надіслати
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
    log.info("🤖 UA Events Bot v2.2")
    log.info(f"   Канал:    {CHANNEL_ID}")
    log.info(f"   Джерел:   {len(SCRAPERS)}")
    log.info(f"   Інтервал: кожні {CHECK_HOURS} год.")

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
