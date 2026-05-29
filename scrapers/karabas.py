"""
Скрапер: karabas.{tld}
Один скрапер покриває всі домени мережі KARABAS (.pl, .cz, .de, .ch, .it, .es, .dk, .co).
Всі домени мають однакову HTML-структуру.
"""

import logging
import re
import requests
from bs4 import BeautifulSoup

log = logging.getLogger("scraper.karabas")

KARABAS_DOMAINS = {
    "pl": "https://karabas.pl",
    "cz": "https://karabas.cz",
    "de": "https://karabas.de",   # якщо існує
    "ch": "https://karabas.ch",
    "it": "https://karabas.it",
    "es": "https://karabas.es",
    "dk": "https://karabas.dk",
    "co": "https://karabas.co",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "uk,en;q=0.9",
}


def scrape_karabas(tld: str = "pl") -> list[dict]:
    """
    Парсить karabas.{tld} і повертає список подій.
    tld: 'pl', 'cz', 'ch', 'it', 'es', 'dk', 'co'
    """
    base_url = KARABAS_DOMAINS.get(tld)
    if not base_url:
        log.error(f"Невідомий домен karabas: {tld}")
        return []

    events = []

    # Karabas зазвичай має сторінку /concerts або головну з афішею
    for path in ["", "/concerts", "/concerts/", "/uk", "/uk/concerts"]:
        url = base_url + path
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            if resp.status_code == 200:
                events = _parse_karabas_page(resp.text, base_url, tld)
                if events:
                    break
        except Exception as e:
            log.debug(f"karabas.{tld}{path}: {e}")

    log.info(f"karabas.{tld}: зібрано {len(events)} подій")
    return events


def _parse_karabas_page(html: str, base_url: str, tld: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    events = []
    seen = set()

    # Шукаємо посилання на події (karabas використовує /event/slug або /concerts/slug)
    selectors = [
        "a[href*='/event/']",
        "a[href*='/concerts/']",
        "a[href*='/show/']",
        ".event-card a",
        ".concert-item a",
        "article a",
    ]

    links = []
    for sel in selectors:
        found = soup.select(sel)
        if found:
            links.extend(found)
            break

    # Fallback: всі посилання що схожі на події
    if not links:
        links = soup.find_all("a", href=re.compile(r"/(event|concert|show|ticket)/"))

    for link in links:
        href = link.get("href", "")
        if not href or href in seen:
            continue
        seen.add(href)

        if href.startswith("/"):
            href = base_url + href
        elif not href.startswith("http"):
            continue

        # Пропускаємо службові сторінки
        if any(x in href for x in ["/category/", "/tag/", "/page/", "?", "#"]):
            continue

        text = link.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            continue

        title = lines[0]
        if len(title) < 3:
            continue

        date_str = ""
        city = ""
        price = ""

        for line in lines[1:]:
            if re.search(r"\d{1,2}[./]\d{2}[./]\d{2,4}", line) and not date_str:
                date_str = line.strip()
            if re.search(r"[€$£]|zł|Kč|CHF|kr\b|PLN", line):
                price = line.strip()
            # Місто — рядок без цифр і не занадто довгий
            if not city and len(line) < 40 and not re.search(r"\d", line):
                city = line.strip()

        # Країна по домену
        country_map = {
            "pl": "Poland", "cz": "Czech Republic", "ch": "Switzerland",
            "it": "Italy",  "es": "Spain",          "dk": "Denmark",
            "de": "Germany","co": "Europe",
        }
        country = country_map.get(tld, "Europe")

        events.append({
            "title":   title,
            "date":    date_str,
            "city":    city,
            "country": country,
            "price":   price,
            "url":     href,
            "source":  f"karabas.{tld}",
        })

    return events
