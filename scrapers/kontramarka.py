"""
Скрапер: kontramarka.com/uk/ukrainian-artists/
Використовує Playwright бо сторінка рендериться через JS (SPA).
"""

import logging
import re
from datetime import datetime

log = logging.getLogger("scraper.kontramarka")

URL = "https://www.kontramarka.com/uk/ukrainian-artists/"


def scrape_kontramarka() -> list[dict]:
    """Повертає список подій з контрамарки."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.error("Playwright не встановлено. Запустіть: playwright install chromium")
        return []

    events = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        log.info(f"Завантажуємо {URL}")
        page.goto(URL, timeout=30_000)

        # Чекаємо поки JS завантажить картки подій
        try:
            page.wait_for_selector("a[href*='/tickets-']", timeout=15_000)
        except Exception:
            log.warning("Картки не знайдені — можливо сторінка змінила структуру")
            browser.close()
            return []

        # Збираємо всі картки
        cards = page.query_selector_all("a[href*='/tickets-']")
        seen_hrefs = set()

        for card in cards:
            try:
                href = card.get_attribute("href") or ""
                if not href or href in seen_hrefs:
                    continue
                seen_hrefs.add(href)

                # Повний URL
                if href.startswith("/"):
                    href = "https://www.kontramarka.com" + href

                # Текст всієї картки
                full_text = (card.inner_text() or "").strip()
                lines = [l.strip() for l in full_text.splitlines() if l.strip()]

                if not lines:
                    continue

                title = lines[0]

                # Дата: шукаємо паттерн DD.MM.YYYY
                date_str = ""
                city = ""
                country = ""
                price = ""

                for line in lines:
                    date_match = re.search(r"\d{1,2}\.\d{2}\.\d{4}", line)
                    if date_match and not date_str:
                        date_str = date_match.group()

                    # Місто, Країна — рядок типу "Варшава, Poland"
                    if "," in line and not date_match and len(line) < 60:
                        parts = line.split(",", 1)
                        if len(parts) == 2:
                            city = parts[0].strip()
                            country = parts[1].strip()

                    # Ціна — рядок з €, zł, Kč, CHF, kr, HUF
                    if re.search(r"[€$£]|zł|Kč|CHF|kr|HUF|лв", line):
                        price = line.strip()

                # Парсимо дату
                event_date = None
                if date_str:
                    try:
                        event_date = datetime.strptime(date_str, "%d.%m.%Y").date().isoformat()
                    except ValueError:
                        pass

                events.append({
                    "title":   title,
                    "date":    event_date or date_str,
                    "city":    city,
                    "country": country,
                    "price":   price,
                    "url":     href,
                    "source":  "kontramarka.com",
                })

            except Exception as e:
                log.debug(f"Помилка картки: {e}")

        browser.close()

    log.info(f"kontramarka: зібрано {len(events)} подій")
    return events
