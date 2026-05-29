"""
Універсальний BS4-скрапер для всіх сайтів без JS-рендерингу.
Покриває: hilfe-ua.de, ukrainskidom.pl, ukrainci.cz, ukrainet.eu,
          naszvybir.pl, visitukraine.today, mticket.eu,
          ukrainischeshaus.de, uccc.cz
"""

import logging
import re
import requests
from bs4 import BeautifulSoup

log = logging.getLogger("scraper.generic")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "uk,en;q=0.9,de;q=0.8,pl;q=0.7",
}

SITE_CONFIGS = {
    # 🇩🇪 Германия
    "hilfe-ua.de": {
        "url":          "https://hilfe-ua.de/ua/events/",
        "country":      "Germany",
        "link_pattern": r"/event/|/events/[^/]+/?$",
        "source":       "hilfe-ua.de",
    },
    "ukrainischeshaus.de": {
        "url":          "https://ukrainischeshaus.de/events/",
        "country":      "Germany",
        "link_pattern": r"/event/|/events/|/programm/",
        "source":       "ukrainischeshaus.de",
    },
    # 🇵🇱 Польша
    "ukrainskidom.pl": {
        "url":          "https://ukrainskidom.pl/uk/events/",
        "country":      "Poland",
        "link_pattern": r"/event/|/events/|/uk/[^/]+/?$",
        "source":       "ukrainskidom.pl",
    },
    "naszvybir.pl": {
        "url":          "https://naszvybir.pl/events/",
        "country":      "Poland",
        "link_pattern": r"/event/|/events/|/afisza/|/kultura/",
        "source":       "naszvybir.pl",
    },
    # 🇨🇿 Чехия
    "ukrainci.cz": {
        "url":          "https://www.ukrajinci.cz/cs/kultura/",
        "country":      "Czech Republic",
        "link_pattern": r"/kultura/|/akce/|/event",
        "source":       "ukrainci.cz",
    },
    "uccc.cz": {
        "url":          "https://uccc.cz/events/",
        "country":      "Czech Republic",
        "link_pattern": r"/event/|/events/|/akce/",
        "source":       "uccc.cz",
    },
    # 🇦🇹 Австрия
    "ukrainet.eu": {
        "url":          "https://ukrainet.eu/events/",
        "country":      "Austria",
        "link_pattern": r"/event/|/events/|/veranstaltung",
        "source":       "ukrainet.eu",
    },
    # 🌍 ЄС загальний
    "visitukraine.today": {
        "url":          "https://visitukraine.today/blog?tag=abroad",
        "country":      "Europe",
        "link_pattern": r"/blog/|/event/|/events/",
        "source":       "visitukraine.today",
    },
    "mticket.eu": {
        "url":          "https://mticket.eu/uk",
        "country":      "Europe",
        "link_pattern": r"/event/|/concert/|/show/|/ticket/",
        "source":       "mticket.eu",
    },
}


def scrape_generic(site_key: str) -> list[dict]:
    config = SITE_CONFIGS.get(site_key)
    if not config:
        log.error(f"Невідомий сайт: {site_key}")
        return []

    url     = config["url"]
    country = config["country"]
    source  = config["source"]
    pattern = config.get("link_pattern", r"/event")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=25)
        resp.raise_for_status()
    except Exception as e:
        log.warning(f"{site_key}: {e}")
        return []

    soup   = BeautifulSoup(resp.text, "html.parser")
    events = []
    seen   = set()
    base   = "/".join(url.split("/")[:3])

    for link in soup.find_all("a", href=re.compile(pattern)):
        href = link.get("href", "")
        if not href or href in seen:
            continue
        seen.add(href)

        if href.startswith("/"):
            href = base + href
        elif not href.startswith("http"):
            continue

        # Пропускаємо службові сторінки
        if any(x in href for x in ["#", "?page=", "/tag/", "/category/", "/author/"]):
            continue

        text  = link.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            continue

        title = lines[0]
        if len(title) < 4 or title.lower() in ("more", "читати", "детальніше", "mehr"):
            continue

        date_str = city = price = ""
        for line in lines[1:]:
            if re.search(r"\d{1,2}[./]\d{2}[./]\d{2,4}", line) and not date_str:
                date_str = line.strip()
            if re.search(r"[€$£]|zł|Kč|CHF|kr\b|PLN", line):
                price = line.strip()
            if not city and len(line) < 40 and not re.search(r"\d{4}", line):
                city = line.strip()

        events.append({
            "title":   title,
            "date":    date_str,
            "city":    city,
            "country": country,
            "price":   price,
            "url":     href,
            "source":  source,
        })

    log.info(f"{site_key}: {len(events)} подій")
    return events
