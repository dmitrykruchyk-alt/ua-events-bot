"""
Фільтр подій:
1. Географічний — дозволені країни (Європа + UK + USA + Canada)
2. AI-фільтр через Claude API — визначає чи артист український
"""

import os
import re
import logging
import requests

log = logging.getLogger("ua_filter")

# ── Дозволені країни ──────────────────────────────────────────
ALLOWED_COUNTRIES = {
    # Пріоритетні
    "germany", "deutschland", "de",
    "poland", "polska", "pl",
    "czech", "czechia", "czech republic", "cz",
    "austria", "österreich", "at",
    # Інша Європа
    "switzerland", "ch",
    "italy", "it",
    "spain", "es",
    "denmark", "dk",
    "france", "fr",
    "netherlands", "nl",
    "belgium", "be",
    "sweden", "se",
    "norway", "no",
    "finland", "fi",
    "ireland", "ie",
    "hungary", "hu",
    "slovakia", "sk",
    "portugal", "pt",
    "europe", "eu",
    # Додані
    "uk", "united kingdom", "england", "britain",
    "usa", "united states", "us", "america",
    "canada", "канада",
}

# ── Виключені країни ──────────────────────────────────────────
EXCLUDED_COUNTRIES = {
    "turkey", "türkiye", "istanbul", "туреччина",
    "russia", "россия",
    "belarus", "беларусь",
    "georgia", "tbilisi",
    "azerbaijan", "baku",
    "israel", "tel aviv",
    "armenia",
    "montenegro",
    "serbia",
}

# ── Безпечні джерела (вже відфільтровані) ────────────────────
SAFE_SOURCES = {
    "kontramarka.com", "bravo.vip",
    "karabas.pl", "karabas.cz", "karabas.de",
    "karabas.ch", "karabas.it", "karabas.es",
    "karabas.dk", "karabas.co",
    "hilfe-ua.de", "ukrainskidom.pl", "ukrainci.cz",
    "uccc.cz", "ukrainet.eu", "ukrainischeshaus.de",
    "naszvybir.pl",
}

# ── Claude API для визначення артиста ────────────────────────
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

def _is_ukrainian_artist_ai(title: str) -> bool:
    """
    Запитує Claude API: чи є артист в назві події українським?
    Повертає True якщо так, False якщо ні або невідомо.
    """
    if not ANTHROPIC_KEY:
        log.warning("ANTHROPIC_API_KEY не встановлено — AI-фільтр вимкнено")
        return True  # без ключа — пропускаємо все

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 10,
                "messages": [{
                    "role": "user",
                    "content": (
                        f"Is the performer in this event title a Ukrainian artist? "
                        f"Event: '{title}'. "
                        f"Answer only YES or NO."
                    )
                }]
            },
            timeout=10,
        )
        if response.status_code == 200:
            answer = response.json()["content"][0]["text"].strip().upper()
            log.info(f"  🤖 AI фільтр '{title[:40]}': {answer}")
            return answer.startswith("YES")
    except Exception as e:
        log.warning(f"AI фільтр помилка: {e}")

    return False  # якщо помилка — краще пропустити


def is_ukrainian_event(event: dict) -> bool:
    """
    Повна перевірка події:
    1. Безпечне джерело → одразу True
    2. Виключена країна → False
    3. Дозволена країна → перевіряємо через AI
    """
    source  = (event.get("source", "") or "").lower()
    country = (event.get("country", "") or "").lower()
    city    = (event.get("city", "") or "").lower()
    title   = (event.get("title", "") or "")

    # 1. Безпечне джерело
    if source in SAFE_SOURCES:
        return True

    # 2. Виключена країна
    for excl in EXCLUDED_COUNTRIES:
        if excl in country or excl in city:
            log.info(f"  🚫 Виключена країна '{country or city}': {title[:40]}")
            return False

    # 3. Перевірити що країна дозволена
    country_ok = any(c in country or c in city for c in ALLOWED_COUNTRIES)
    if not country_ok and (country or city):
        log.info(f"  🚫 Країна не в списку '{country or city}': {title[:40]}")
        return False

    # 4. AI-перевірка артиста
    return _is_ukrainian_artist_ai(title)
