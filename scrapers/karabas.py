"""
Скрапер: karabas.{tld}
Парсить тільки конкретні сторінки ПОДІЙ (не категорії).
Фільтрує: пропускає посилання на категорії (/concerts/, /theatre/)
та бере тільки конкретні події (/concert/slug або /event/slug).
"""

import logging
import re
import requests
from bs4 import BeautifulSoup

log = logging.getLogger("scraper.karabas")

KARABAS_DOMAINS = {
    "pl": "https://karabas.pl",
    "cz": "https://karabas.cz",
    "de": "https://karabas.de",
    "ch": "https://karabas.ch",
    "it": "https://karabas.it",
    "es": "https://karabas.es",
    "dk": "https://karabas.dk",
    "co": "https://karabas.co",
}

COUNTRY_MAP = {
    "pl": "Poland", "cz": "Czech Republic", "ch": "Switzerland",
    "it": "Italy",  "es": "Spain",          "dk": "Denmark",
    "de": "Germany","co": "Europe",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "uk,en;q=0.9",
}

# Паттерни URL конкретних подій (не категорій)
EVENT_URL_PATTERNS = [
    r"/[a-z]{2}/[^/]+-tickets-[a-z0-9]+/?$",  # /es/dzidzio-tickets-abc123/
    r"/tickets/[^/]+/?$",                        # /tickets/event-slug/
    r"/event/[^/]+/?$",                          # /event/slug/
    r"/[a-z0-9-]+-\d{4,}/?$",                   # /dzidzio-concert-123456/
]

# Паттерни URL які треба ПРОПУСКАТИ (категорії, службові)
SKIP_URL_PATTERNS = [
    r"^/concerts/?$",
    r"^/concerts/[a-z]+/?$",   # /concerts/pop/, /concerts/rock/
    r"^/theatre/?",
    r"^/cinema/?",
    r"^/sports/?",
    r"^/kids/?",
    r"^/[a-z]{2}/concerts/?$",
    r"^/[a-z]{2}/?$",          # просто /es/ або /pl/
    r"/page/\d+",
    r"/tag/",
    r"/category/",
    r"/search",
    r"\?",
    r"#",
]

# Слова-сигнали що це категорія, не подія
CATEGORY_TITLES = {
    "concerts", "conciertos", "konzerte", "koncerty", "koncerti",
    "theatre", "theater", "teatro", "teatr",
    "tickets", "entradas", "bilety", "karten",
    "all events", "voir tout", "see all",
}


def scrape_karabas(tld: str = "pl") -> list[dict]:
    base_url = KARABAS_DOMAINS.get(tld)
    if not base_url:
        log.error(f"Невідомий домен karabas: {tld}")
        return []

    country = COUNTRY_MAP.get(tld, "Europe")
    events = []

    # Пробуємо різні URL головних сторінок
    for path in ["", "/concerts", "/en/concerts", "/uk/concerts"]:
        url = base_url + path
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            if resp.status_code == 200 and len(resp.text) > 1000:
                parsed = _parse_page(resp.text, base_url, country, tld)
                if parsed:
                    events.extend(parsed)
                    break
        except Exception as e:
            log.debug(f"karabas.{tld}{path}: {e}")

    # Дедублікація по URL
    seen = set()
    unique = []
    for e in events:
        if e["url"] not in seen:
            seen.add(e["url"])
            unique.append(e)

    log.info(f"karabas.{tld}: {len(unique)} подій")
    return unique


def _should_skip_url(href: str) -> bool:
    """Повертає True якщо URL — це категорія або службова сторінка."""
    for pattern in SKIP_URL_PATTERNS:
        if re.search(pattern, href):
            return True
    return False


def _is_event_url(href: str) -> bool:
    """Повертає True якщо URL схожий на конкретну подію."""
    for pattern in EVENT_URL_PATTERNS:
        if re.search(pattern, href):
            return True
    # Якщо в URL є числовий ID — швидше за все це подія
    if re.search(r"-\d{5,}", href):
        return True
    return False


def _parse_page(html: str, base_url: str, country: str, tld: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    events = []
    seen_hrefs = set()

    for link in soup.find_all("a", href=True):
        href = link.get("href", "").strip()
        if not href:
            continue

        # Нормалізуємо URL
        if href.startswith("/"):
            full_url = base_url + href
        elif href.startswith("http"):
            # Беремо тільки посилання на той самий домен
            if base_url.split("//")[1].split("/")[0] not in href:
                continue
            full_url = href
        else:
            continue

        if full_url in seen_hrefs:
            continue

        # Пропускаємо категорії
        if _should_skip_url(href):
            continue

        # Беремо тільки конкретні події
        if not _is_event_url(href):
            continue

        seen_hrefs.add(full_url)

        # Текст картки
        text = link.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        if not lines:
            continue

        title = lines[0]

        # Пропускаємо якщо назва — це категорія
        if title.lower() in CATEGORY_TITLES or len(title) < 4:
            continue

        # Пропускаємо занадто короткі або технічні назви
        if re.match(r"^\d+$", title) or title.lower() in ("more", "buy", "details"):
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
            "url":     full_url,
            "source":  f"karabas.{tld}",
        })

    return events
