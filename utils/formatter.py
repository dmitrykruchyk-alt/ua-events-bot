"""
Форматер повідомлень для Telegram.
Генерує красиве HTML-повідомлення з деталями події.
"""

# Прапори країн
COUNTRY_FLAGS = {
    "germany":          "🇩🇪", "deutschland": "🇩🇪",
    "poland":           "🇵🇱", "polska":      "🇵🇱",
    "czech":            "🇨🇿", "czechia":     "🇨🇿", "czech republic": "🇨🇿",
    "austria":          "🇦🇹", "österreich":  "🇦🇹",
    "switzerland":      "🇨🇭", "schweiz":     "🇨🇭",
    "italy":            "🇮🇹", "italia":      "🇮🇹",
    "spain":            "🇪🇸", "españa":      "🇪🇸",
    "denmark":          "🇩🇰", "danmark":     "🇩🇰",
    "france":           "🇫🇷",
    "netherlands":      "🇳🇱", "holland":     "🇳🇱",
    "belgium":          "🇧🇪",
    "sweden":           "🇸🇪", "sverige":     "🇸🇪",
    "norway":           "🇳🇴", "norge":       "🇳🇴",
    "finland":          "🇫🇮",
    "ireland":          "🇮🇪",
    "hungary":          "🇭🇺",
    "slovakia":         "🇸🇰",
    "portugal":         "🇵🇹",
    "europe":           "🌍",
}

SOURCE_LABELS = {
    "kontramarka.com": "Kontramarka",
    "bravo.vip":       "Bravo.vip",
    "karabas.pl":      "Karabas PL",
    "karabas.cz":      "Karabas CZ",
    "karabas.de":      "Karabas DE",
    "karabas.ch":      "Karabas CH",
    "karabas.it":      "Karabas IT",
    "karabas.es":      "Karabas ES",
    "karabas.dk":      "Karabas DK",
    "karabas.co":      "Karabas EU",
}


def get_flag(country: str) -> str:
    if not country:
        return "🌍"
    c = country.lower().strip()
    for key, flag in COUNTRY_FLAGS.items():
        if key in c:
            return flag
    return "🎭"


def format_event_message(event: dict, source: str) -> str:
    """
    Форматує подію у HTML-повідомлення для Telegram.

    Приклад виводу:
    ━━━━━━━━━━━━━━━━━━━━━
    🎵 НОВА ПОДІЯ 🇵🇱

    🎤 <b>СКАЙ — 25 лет на сцене</b>

    📅 10.09.2026
    📍 Варшава, Poland
    💶 167zł - 195zł

    🔗 Купити квитки

    📌 Джерело: Kontramarka
    ━━━━━━━━━━━━━━━━━━━━━
    """
    title   = event.get("title", "Без назви")
    date    = event.get("date", "")
    city    = event.get("city", "")
    country = event.get("country", "")
    price   = event.get("price", "")
    url     = event.get("url", "")

    flag = get_flag(country)
    source_label = SOURCE_LABELS.get(source, source)

    # Формуємо рядок місця
    location_parts = [p for p in [city, country] if p]
    location = ", ".join(location_parts) if location_parts else "Уточнюйте на сайті"

    lines = [
        f"━━━━━━━━━━━━━━━━━━━━━",
        f"🎵 <b>НОВА ПОДІЯ</b> {flag}",
        f"",
        f"🎤 <b>{_esc(title)}</b>",
        f"",
    ]

    if date:
        lines.append(f"📅 {_esc(date)}")
    if location:
        lines.append(f"📍 {_esc(location)}")
    if price:
        lines.append(f"💶 {_esc(price)}")

    lines.append("")

    if url:
        lines.append(f'🔗 <a href="{url}">Купити квитки</a>')

    lines += [
        "",
        f"📌 Джерело: {source_label}",
        f"━━━━━━━━━━━━━━━━━━━━━",
    ]

    return "\n".join(lines)


def _esc(text: str) -> str:
    """Екранує HTML-символи для Telegram."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
