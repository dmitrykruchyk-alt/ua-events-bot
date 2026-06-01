"""
Фільтр подій — тільки українські артисти в дозволених країнах.

Логіка:
1. Безпечні джерела (укр. культурні центри) → одразу пропускаємо
2. Виключені країни (Туреччина, РФ...) → блокуємо
3. Загальні джерела (mticket, ticketmaster) → AI-перевірка через Claude
"""

import os
import logging
import requests

log = logging.getLogger("ua_filter")

# ── Безпечні джерела — вже відфільтровані ────────────────────
SAFE_SOURCES = {
    "kontramarka.com", "bravo.vip",
    "karabas.pl", "karabas.cz", "karabas.de",
    "karabas.ch", "karabas.it", "karabas.es",
    "karabas.dk", "karabas.co",
    "hilfe-ua.de", "ukrainskidom.pl", "ukrainci.cz",
    "uccc.cz", "ukrainet.eu", "ukrainischeshaus.de",
    "naszvybir.pl",
}

# ── Дозволені країни ──────────────────────────────────────────
ALLOWED_COUNTRIES = {
    # Пріоритет
    "germany", "deutschland",
    "poland", "polska",
    "czech", "czechia", "czech republic",
    "austria", "österreich",
    # Решта Європи
    "switzerland", "italy", "spain", "denmark",
    "france", "netherlands", "belgium", "sweden",
    "norway", "finland", "ireland", "hungary",
    "slovakia", "portugal", "europe", "eu",
    # Англомовні
    "uk", "united kingdom", "england", "britain", "scotland",
    "usa", "united states", "america",
    "canada",
}

# ── Виключені країни ──────────────────────────────────────────
EXCLUDED_COUNTRIES = {
    "turkey", "türkiye", "istanbul", "ankara",
    "russia", "россия",
    "belarus", "беларусь",
    "georgia", "tbilisi",
    "azerbaijan", "baku",
    "israel", "tel aviv",
    "armenia", "montenegro", "serbia",
}

# Claude API key
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def _ai_is_ukrainian(title: str) -> bool:
    """
    Запитує Claude Haiku: чи є артист в назві події українським?
    Дешево (~$0.0001 за запит) і точно.
    """
    if not ANTHROPIC_KEY:
        # Без ключа — пропускаємо все щоб нічого не загубити
        log.debug("ANTHROPIC_API_KEY не встановлено — пропускаємо AI перевірку")
        return True

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 5,
                "system": (
                    "You are a music expert. Answer only YES or NO. "
                    "YES = the main performer is Ukrainian. "
                    "NO = not Ukrainian or unknown."
                ),
                "messages": [{
                    "role": "user",
                    "content": f"Is the main performer Ukrainian? Event: '{title}'"
                }]
            },
            timeout=8,
        )
        if resp.status_code == 200:
            answer = resp.json()["content"][0]["text"].strip().upper()
            log.info(f"  🤖 '{title[:45]}' → {answer}")
            return answer.startswith("YES")
        else:
            log.warning(f"  AI API помилка {resp.status_code}")
            return True  # якщо API недоступний — пропускаємо

    except Exception as e:
        log.warning(f"  AI помилка: {e}")
        return True  # якщо timeout — пропускаємо


def is_ukrainian_event(event: dict) -> bool:
    """
    Повна перевірка події.
    """
    source  = (event.get("source", "") or "").lower().strip()
    country = (event.get("country", "") or "").lower().strip()
    city    = (event.get("city", "") or "").lower().strip()
    title   = (event.get("title", "") or "").strip()
    geo     = f"{country} {city}"

    # 1. Безпечне джерело — одразу OK
    if source in SAFE_SOURCES:
        return True

    # 2. Виключена країна — блокуємо
    for excl in EXCLUDED_COUNTRIES:
        if excl in geo:
            log.info(f"  🚫 '{excl}' в '{geo}' → блок: {title[:40]}")
            return False

    # 3. Перевіряємо що країна взагалі дозволена
    if geo.strip():
        country_ok = any(c in geo for c in ALLOWED_COUNTRIES)
        if not country_ok:
            log.info(f"  🚫 Країна не в списку '{geo}' → блок: {title[:40]}")
            return False

    # 4. AI-перевірка артиста
    return _ai_is_ukrainian(title)
