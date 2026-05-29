FROM python:3.11-slim

# Системні залежності для Playwright
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Встановити браузер Chromium для Playwright
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

# Директорія для SQLite бази
RUN mkdir -p /data
ENV DB_PATH=/data/events.db

CMD ["python", "main.py"]
