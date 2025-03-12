# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /Alex_Petrow_law_bot

# Копируем файл зависимостей (например, requirements.txt) и устанавливаем зависимости
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Открываем порт, если необходимо
EXPOSE 8000
#WORKDIR /Alex_Petrow_law_bot/botы
#do
# Команда для запуска бота
ENTRYPOINT ["sh", "-c", "sleep 5 && alembic upgrade head && python -m bot.main"]

