# Alex Petrow Law Bot

Alex Petrow Law Bot — это Telegram-бот для сбора и обработки заявок пользователей администраторами.

## Функционал

Бот поддерживает следующие команды:
- `/start` — начало работы, создание заявки.
- `/admin` — режим администратора (доступен только для администраторов, ожидает появление новых заявок).
- `/faq` — ответы на часто задаваемые вопросы.
- `/help` — информация о функциях бота.

## Установка и запуск

### 1. Подготовка окружения
Перед запуском необходимо создать `.env` файл со следующими параметрами:

```ini
DB_USER=some_user
DB_PASSWORD=some_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tlg_bot
BOT_TOKEN=7824055801:AAFRcMRSncPHjGA4-uAQ8KH5HDtsbtWqYXE
ADMIN_IDS=[439653349]
BASE_DIR=/home/user/PycharmProjects/Alex_Petrow_law_bot
REDIS_LOGIN=default
REDIS_PASSWORD=password
REDIS_HOST=localhost
NUM_DB=0
```

### 2. Запуск через Docker
Бот поддерживает запуск через `docker-compose`. Чтобы развернуть его, выполните:

```sh
docker-compose up --build -d
```

Это соберет и запустит контейнеры в фоновом режиме.

### 3. Миграции базы данных (если необходимо)
Если нужно выполнить миграции для базы данных, используйте Alembic:

```sh
alembic upgrade head
```

## Технологии
- Python (Aiogram3, SQLAlchemy, Alembic)
- PostgreSQL
- Redis
- Aiogram (для работы с Telegram API)
- Docker, Docker Compose

## Разработка и тестирование
Если вы хотите разрабатывать или тестировать бота локально, выполните:

```sh
python bot/main.py
```

Для работы с тестовой базой данных можно задать `DB_NAME=test_tlg_bot` в `.env` файле.

## Контакты
Если у вас есть вопросы или предложения, свяжитесь с автором проекта.

Это команда для запуска линтера ruff

```bash
ruff check --fix . && ruff format .

```