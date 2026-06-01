"""
Форматер повідомлень для Telegram.
"""

COUNTRY_FLAGS = {
    "germany": "🇩🇪", "deutschland": "🇩🇪",
    "poland": "🇵🇱", "polska": "🇵🇱",
    "czech": "🇨🇿", "czechia": "🇨🇿", "czech republic": "🇨🇿",
    "austria": "🇦🇹", "österreich": "🇦🇹",
    "switzerland": "🇨🇭",
    "italy": "🇮🇹",
    "spain": "🇪🇸",
    "denmark": "🇩🇰",
    "france": "🇫🇷",
    "netherlands": "🇳🇱",
    "belgium": "🇧🇪",
    "sweden": "🇸🇪",
    "norway": "🇳🇴",
    "finland": "🇫🇮",
    "ireland": "🇮🇪",
    "hungary": "🇭🇺",
    "slovakia": "🇸🇰",
    "portugal": "🇵🇹",
    "uk": "🇬🇧", "united kingdom": "🇬🇧", "england": "🇬🇧",
    "usa": "🇺🇸", "united states": "🇺🇸",
    "canada": "🇨🇦",
    "europe": "🌍",
}

SOURCE_LABELS = {
    "kontramarka.com": "Kontramarka",
    "bravo.vip":       "Bravo.vip",
    "karabas.pl":      "Karabas 🇵🇱",
    "karabas.cz":      "Karabas 🇨🇿",
    "karabas.de":      "Karabas 🇩🇪",
    "karabas.ch":      "Karabas 🇨🇭",
    "karabas.it":      "Karabas 🇮🇹",
    "karabas.es":      "Karabas 🇪🇸",
    "karabas.dk":      "Karabas 🇩🇰",
    "karabas.co":      "Karabas EU",
    "mticket.eu":      "mTicket",
    "hilfe-ua.de":          "Hilfe-UA 🇩🇪",
    "ukrainischeshaus.de":  "Ukr. Haus Berlin",
    "ukrainskidom.pl":      "Ukr. Dim Warszawa",
    "naszvybir.pl":         "Nasz Wybir 🇵🇱",
    "ukrainci.cz":          "Ukrainci.cz",
    "uccc.cz":              "UCCC Praha",
    "ukrainet.eu":          "Ukrainet 🇦🇹",
    "ticketmaster":         "Ticketmaster",
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
    title   = event.get("title", "Без назви")
    date    = event.get("date", "")
    city    = event.get("city", "")
    country = event.get("country", "")
    price   = event.get("price", "")
    url     = event.get("url", "")

    flag = get_flag(country)
    source_label = SOURCE_LABELS.get(source, source)

    location_parts = [p for p in [city, country] if p]
    location = ", ".join(location_parts) if location_parts else ""

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━",
        f"🎵 <b>НОВА ПОДІЯ</b> {flag}",
        "",
        f"🎤 <b>{_esc(title)}</b>",
        "",
    ]

    if date:
        lines.append(f"📅 {_esc(date)}")
    if location:
        lines.append(f"📍 {_esc(location)}")
    if price:
        lines.append(f"💶 {_esc(price)}")

    lines.append("")

    if url:
        # Змінено: "Детальніше" замість "Купити квитки"
        lines.append(f'🔗 <a href="{url}">Детальніше про подію</a>')

    lines += [
        "",
        f"📌 Джерело: {source_label}",
        "━━━━━━━━━━━━━━━━━━━━━",
    ]

    return "\n".join(lines)


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
