"""
Фільтр російського контенту.
Перевіряє назву події і виконавця на наявність у blocklist.
"""

import re

# ── Blocklist: відомі RU-артисти ────────────────────────────
RU_ARTISTS_BLOCKLIST = {
    # Поп
    "kirkorov", "кіркоров", "киркоров",
    "pugacheva", "пугачова", "пугачева",
    "meladze", "меладзе",
    "bilan", "білан", "билан",
    "baskov", "басков",
    "galkin", "галкін", "галкин",
    "leps", "лепс",
    "mikhaylov", "михайлов",
    "koroleva", "корольова", "королева",
    "valeriya", "валерія", "валерия",
    "orbakaite", "орбакайте",
    "grigory leps",
    "polina gagarina", "гагаріна", "гагарина",
    "nуsha", "нюша",
    "loboda",          # увага — перевіряти, вона також має укр. пісні
    # Рок
    "ddt", "ддт",
    "shevchuk", "шевчук",          # лише якщо в контексті ДДТ
    "bi-2", "би-2",
    "zemfira", "земфіра", "земфира",
    "mumiy troll", "мумій тролль",
    "leningrad", "ленінград",      # гурт Шнура
    "shnur", "шнур",
    "splean", "сплін",
    "mashina vremeni", "машина времени",
    # Шансон / естрада
    "grigory leps",
    "mikhail shufutinsky", "шуфутинський",
    "lyube", "люб'е",
    "nautilus pompilius",
    # Стендап
    "poperechny", "попереченко",
    "galkin maxim", "максим галкін",
    # Ключові слова в описі
}

# ── Ключові слова що сигналізують RU-контент ────────────────
RU_KEYWORDS = [
    "народний артист росії",
    "народный артист России",
    "meritorious artist of russia",
    "people's artist of russia",
    "russian singer",
    "российский певец",
    "рос. виконавець",
    "russia tour",
    "russian pop",
    "russian rock",
    # Організатори з РФ
    "russianshow",
    "концерт российского",
]


def is_russian_content(event: dict) -> bool:
    """
    Повертає True якщо подія схоже є RU-контентом.
    Перевіряє title, artist (якщо є) і description.
    """
    # Збираємо весь текст події в нижньому регістрі
    check_text = " ".join([
        event.get("title", ""),
        event.get("artist", ""),
        event.get("description", ""),
        event.get("organizer", ""),
    ]).lower()

    # Перевірка blocklist артистів
    for artist in RU_ARTISTS_BLOCKLIST:
        # Шукаємо як ціле слово або частину імені
        if re.search(r"\b" + re.escape(artist) + r"\b", check_text):
            return True

    # Перевірка ключових слів
    for kw in RU_KEYWORDS:
        if kw.lower() in check_text:
            return True

    # Особливий кейс: Loboda — може бути і укр і рос
    # Якщо в тексті є "loboda" АЛЕ НЕ має "ukraina", "україна", "ukrainian"
    if "loboda" in check_text:
        ua_context = any(w in check_text for w in [
            "ukraine", "ukrainian", "україн", "укр"
        ])
        if not ua_context:
            return True  # підозріло — краще пропустити

    return False


def get_blocklist() -> set:
    """Повертає повний blocklist для зовнішнього використання."""
    return RU_ARTISTS_BLOCKLIST.copy()
