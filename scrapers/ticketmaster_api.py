"""
Скрапер: Ticketmaster International Discovery API
Офіційний безкоштовний API — не потребує Playwright.
Фільтрує події по keyword=Ukrainian у DE, PL, CZ, AT, CH, NL, BE.
"""

import logging
import os
import requests

log = logging.getLogger("scraper.ticketmaster")

# Безкоштовний ключ: реєстрація на developer.ticketmaster.com
# Додайте в Railway як змінну: TICKETMASTER_KEY
TM_KEY = os.getenv("TICKETMASTER_KEY", "")

BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

# Країни для пошуку
COUNTRIES = ["DE", "PL", "CZ", "AT", "CH", "NL", "BE", "SE", "NO", "DK", "IT", "ES", "FR"]

# Ключові слова для пошуку українських подій
KEYWORDS = [
    "Ukrainian", "Ukrainians", "Ukraine",
    "DZIDZIO", "СКАЙ", "SKAI", "Vakarchuk",
    "Druha Rika", "Друга ріка",
    "KAZKA", "Dorofeeva", "Jerry Heil",
    "Klavdia Petrivna", "Bez Obmezhen",
]


def scrape_ticketmaster() -> list[dict]:
    if not TM_KEY:
        log.warning("TICKETMASTER_KEY не встановлено — пропускаємо")
        return []

    events = []
    seen_ids = set()

    for keyword in KEYWORDS[:5]:  # перші 5 щоб не перевищити ліміт
        for country in ["DE", "PL", "CZ", "AT"]:  # пріоритетні країни
            try:
                params = {
                    "apikey":      TM_KEY,
                    "keyword":     keyword,
                    "countryCode": country,
                    "size":        20,
                    "sort":        "date,asc",
                    "classificationName": "Music",
                }
                resp = requests.get(BASE_URL, params=params, timeout=15)
                if resp.status_code != 200:
                    continue

                data = resp.json()
                items = (data.get("_embedded") or {}).get("events") or []

                for item in items:
                    tm_id = item.get("id", "")
                    if tm_id in seen_ids:
                        continue
                    seen_ids.add(tm_id)

                    # Назва
                    title = item.get("name", "")

                    # Дата
                    dates = item.get("dates", {})
                    date_str = dates.get("start", {}).get("localDate", "")

                    # Місце
                    venues = (item.get("_embedded") or {}).get("venues") or []
                    city    = venues[0].get("city", {}).get("name", "") if venues else ""
                    country_name = venues[0].get("country", {}).get("name", "") if venues else country

                    # Ціна
                    price_ranges = item.get("priceRanges") or []
                    price = ""
                    if price_ranges:
                        mn = price_ranges[0].get("min", "")
                        mx = price_ranges[0].get("max", "")
                        currency = price_ranges[0].get("currency", "€")
                        if mn and mx:
                            price = f"{mn}–{mx} {currency}"

                    # URL
                    url = item.get("url", "")

                    events.append({
                        "title":   title,
                        "date":    date_str,
                        "city":    city,
                        "country": country_name,
                        "price":   price,
                        "url":     url,
                        "source":  "ticketmaster",
                    })

            except Exception as e:
                log.debug(f"Ticketmaster {keyword}/{country}: {e}")

    log.info(f"ticketmaster: зібрано {len(events)} подій")
    return events
