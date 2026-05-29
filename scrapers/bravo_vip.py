"""
Скрапер: bravo.vip/en/concerts
Звичайний HTML — requests + BeautifulSoup (без Playwright).
"""

import logging
import re
import requests
from bs4 import BeautifulSoup

log = logging.getLogger("scraper.bravo_vip")

URL = "https://bravo.vip/en/concerts"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def scrape_bravo_vip() -> list[dict]:
    events = []
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        log.error(f"bravo.vip fetch error: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Шукаємо посилання на конкретні події
    # bravo.vip використовує /en/event/slug або схожу структуру
    for link in soup.find_all("a", href=re.compile(r"/en/event/|/tickets-|/en/tickets")):
        href = link.get("href", "")
        if not href:
            continue
        if href.startswith("/"):
            href = "https://bravo.vip" + href

        # Текст картки
        text = link.get_text(separator="\n", strip=True)
        lines = [l for l in text.splitlines() if l.strip()]
        if not lines:
            continue

        title = lines[0]

        date_str = ""
        city = ""
        country = ""
        price = ""

        for line in lines:
            # Дата у форматах: "14.12.25", "14 Dec 2025", "December 14, 2025"
            d = re.search(r"\d{1,2}[./]\d{2}[./]\d{2,4}", line)
            if d and not date_str:
                date_str = d.group()

            if "," in line and len(line) < 60 and not re.search(r"\d", line[:3]):
                parts = line.split(",", 1)
                city    = parts[0].strip()
                country = parts[1].strip()

            if re.search(r"[€£$]|zł|CHF|kr\b", line):
                price = line.strip()

        events.append({
            "title":   title,
            "date":    date_str,
            "city":    city,
            "country": country,
            "price":   price,
            "url":     href,
            "source":  "bravo.vip",
        })

    # Дедублікуємо по URL
    seen = set()
    unique = []
    for e in events:
        if e["url"] not in seen:
            seen.add(e["url"])
            unique.append(e)

    log.info(f"bravo.vip: зібрано {len(unique)} подій")
    return unique
