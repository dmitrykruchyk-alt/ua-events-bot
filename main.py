"""
UA Events Bot — головний файл
17 джерел з таблиці UA_Events_Resources_Europe.xlsx
Тільки 🟢 БЕЗПЕЧНІ джерела (без RU-контенту)
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

# ══════════════════════════════════════════════════════════════
# ВСІ ДЖЕРЕЛА З ТАБЛИЦІ (тільки 🟢 БЕЗПЕЧНІ)
# ══════════════════════════════════════════════════════════════
SCRAPERS = [

    # ── 🎟 КВИТКОВІ ПЛАТФОРМИ (Топ-пріоритет) ─────────────────
    # kontramarka.com — розділ /uk/ukrainian-artists/ (тільки укр.)
    ("kontramarka.com",     scrape_kontramarka),

    # bravo.vip — тільки укр. артисти, підтверджено
    ("bravo.vip",           scrape_bravo_vip),

    # mticket.eu — укр. версія (з RU-фільтром)
    ("mticket.eu",          lambda: scrape_generic("mticket.eu")),

    # ── 🎭 KARABAS МЕРЕЖА — 8 країн (один парсер) ─────────────
    ("karabas.pl",          lambda: scrape_karabas("pl")),   # 🇵🇱 Польща
    ("karabas.cz",          lambda: scrape_karabas("cz")),   # 🇨🇿 Чехія
    ("karabas.de",          lambda: scrape_karabas("de")),   # 🇩🇪 Нiмеччина
    ("karabas.ch",          lambda: scrape_karabas("ch")),   # 🇨🇭 Швейцарія
    ("karabas.it",          lambda: scrape_karabas("it")),   # 🇮🇹 Італія
    ("karabas.es",          lambda: scrape_karabas("es")),   # 🇪🇸 Іспанія
    ("karabas.dk",          lambda: scrape_karabas("dk")),   # 🇩🇰 Данія
    ("karabas.co",          lambda: scrape_karabas("co")),   # 🌍 ЄС

    # ── 🏛 КУЛЬТУРНІ ЦЕНТРИ ДІАСПОРИ ──────────────────────────
    ("hilfe-ua.de",         lambda: scrape_generic("hilfe-ua.de")),           # 🇩🇪
    ("ukrainischeshaus.de", lambda: scrape_generic("ukrainischeshaus.de")),   # 🇩🇪 Берлін
    ("ukrainskidom.pl",     lambda: scrape_generic("ukrainskidom.pl")),       # 🇵🇱 Варшава
    ("naszvybir.pl",        lambda: scrape_generic("naszvybir.pl")),          # 🇵🇱
    ("ukrainci.cz",         lambda: scrape_generic("ukrainci.cz")),           # 🇨🇿
    ("uccc.cz",             lambda: scrape_generic("uccc.cz")),               # 🇨🇿 Прага
    ("ukrainet.eu",         lambda: scrape_generic("ukrainet.eu")),           # 🇦🇹 Відень
    ("visitukraine.today",  lambda: scrape_generic("visitukraine.today")),    # 🌍 ЄС

    # ── 🔌 API-ДЖЕРЕЛА (потребують ключа в Railway Variables) ──
    # Ticketmaster: додайте TICKETMASTER_KEY в Railway → Variables
    # Реєстрація безкоштовна: developer.ticketmaster.com
    ("ticketmaster",        scrape_ticketmaster),

    # НЕ ПІДКЛЮЧЕНО (потребують токенів / небезпечні без фільтру):
    # besteventseurope.com — 🔴 містить RU-артистів
    # Google Events/SerpAPI — 🔴 без фільтру небезпечно
    # Facebook Graph API    — 🟡 потрібен FB-токен (додамо пізніше)
    # Eventbrite API        — 🟡 потрібен ключ (додамо пізніше)
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
                if is_russian_content(event):
                    log.warning(f"  ⛔ RU-фільтр: {event.get('title','?')[:50]}")
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

    log.info(f"✅ Готово. Нових: {new_total} | Всього в базі: {storage.count()}")


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
        log.error(f"  ❌ send error: {e}")


async def main():
    log.info("🤖 UA Events Bot v2.0")
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
