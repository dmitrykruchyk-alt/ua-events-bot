# 🤖 UA Events Bot

Telegram-бот що моніторить українські події в Європі і надсилає сповіщення в канал/групу.

## Джерела
- kontramarka.com/uk/ukrainian-artists/
- bravo.vip/en/concerts
- karabas.pl, karabas.cz, karabas.de, karabas.ch, karabas.it, karabas.es, karabas.dk

## Що робить
1. Кожні N годин перевіряє всі джерела
2. Фільтрує RU-контент (blocklist + ключові слова)
3. Дедублікує по SHA256(title+date+city)
4. Надсилає нові події у Telegram-канал/групу

---

## ⚡ Деплой на Railway (безкоштовно, без сервера)

### Крок 1 — Створити бота в Telegram

1. Відкрити @BotFather в Telegram
2. `/newbot` → задати ім'я → отримати **BOT_TOKEN**
3. Додати бота в канал/групу як **адміністратора** з правом надсилати повідомлення

### Крок 2 — Отримати CHANNEL_ID

**Для каналу:**
- Якщо канал публічний: просто `@your_channel_username`
- Якщо приватний: форвардніть повідомлення з каналу боту @userinfobot → він покаже ID

**Для групи:**
- Додайте @userinfobot в групу → напишіть `/start` → він покаже Group ID (від'ємне число, напр. `-1001234567890`)

### Крок 3 — Задеплоїти на Railway

```bash
# 1. Зареєструватись на railway.app (безкоштовно)
# 2. Встановити Railway CLI
npm install -g @railway/cli

# 3. Логін
railway login

# 4. Ініціалізувати проект
cd ua_events_bot
railway init

# 5. Додати змінні середовища
railway variables set BOT_TOKEN="ВАШ_ТОКЕН"
railway variables set CHANNEL_ID="@ВАШ_КАНАЛ"
railway variables set CHECK_HOURS="6"

# 6. Деплой
railway up
```

**АБО через GitHub (рекомендовано):**
1. Завантажте папку ua_events_bot на GitHub
2. railway.app → New Project → Deploy from GitHub repo
3. Settings → Variables → додати BOT_TOKEN, CHANNEL_ID, CHECK_HOURS
4. Railway автоматично підніме Docker-контейнер

### Крок 4 — Перевірити що все працює

```bash
# Логи в реальному часі
railway logs
```

Очікуваний вивід:
```
🤖 UA Events Bot запущено
   Канал: @your_channel
   Перевірка кожні 6 год.
▶ Запуск перевірки джерел...
  Перевіряємо: kontramarka.com
  Знайдено 45 подій з kontramarka.com
  📨 Надіслано: СКАЙ в Варшаві...
```

---

## 🖥️ Локальний запуск (для тестування)

```bash
# Встановити залежності
pip install -r requirements.txt

# Встановити браузер
playwright install chromium

# Скопіювати і заповнити .env
cp .env.example .env
# відредагуйте .env

# Запустити
python main.py
```

---

## 📁 Структура проекту

```
ua_events_bot/
├── main.py                  # Головний файл, планувальник
├── scrapers/
│   ├── kontramarka.py       # Playwright-скрапер
│   ├── bravo_vip.py         # BS4-скрапер
│   └── karabas.py           # BS4-скрапер (всі домени)
├── utils/
│   ├── ru_filter.py         # Фільтр RU-контенту
│   ├── storage.py           # SQLite дедублікація
│   └── formatter.py         # Форматування повідомлень
├── requirements.txt
├── Dockerfile
├── railway.toml
└── .env.example
```

---

## ➕ Додати нове джерело

1. Створіть `scrapers/my_source.py` з функцією `scrape_my_source() -> list[dict]`
2. Кожна подія — dict з ключами: `title`, `date`, `city`, `country`, `price`, `url`, `source`
3. Додайте в `main.py` до списку `SCRAPERS`

---

## 🛡️ RU-фільтр

Редагуйте `utils/ru_filter.py`:
- `RU_ARTISTS_BLOCKLIST` — додавайте імена артистів (lowercase)
- `RU_KEYWORDS` — додавайте ключові слова в описах

---

## 💰 Вартість Railway

| План       | Ціна     | Ресурси               |
|------------|----------|-----------------------|
| Hobby      | $5/міс   | 512MB RAM, завжди on  |
| Free Trial | $0       | $5 кредит, потім стоп |

Рекомендується Hobby план ($5/міс) для стабільної роботи.
