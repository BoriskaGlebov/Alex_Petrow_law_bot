import os
import sys
from typing import List, Optional
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Класс настроек приложения, загружаемых из переменных окружения и .env файла.

    Атрибуты:
        DB_USER (str): Имя пользователя базы данных.
        DB_PASSWORD (SecretStr): Пароль пользователя базы данных (хранится в зашифрованном виде).
        DB_HOST (str): Хост базы данных.
        DB_PORT (int): Порт базы данных.
        DB_NAME (str): Имя базы данных.
        BOT_TOKEN (str): Токен Telegram-бота.
        ADMIN_IDS (List[int]): Список ID администраторов бота.
        BASE_DIR (Optional[str]): Базовая директория проекта (опционально).
        REDIS_LOGIN: str : Логин для Redis.
        REDIS_PASSWORD: SecretStr : Пароль для Redis.

    Методы:
        get_db_url() -> str: Возвращает URL для подключения к базе данных.
    """
    DB_USER: str
    DB_PASSWORD: SecretStr
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    BOT_TOKEN: str
    ADMIN_IDS: List[int]

    BASE_DIR: Optional[str] = None

    REDIS_LOGIN: str
    REDIS_PASSWORD: SecretStr
    REDIS_HOST: str
    NUM_DB: int
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    )

    def get_db_url(self) -> str:
        """
        Получает URL для основной базы данных.

        :return: URL базы данных в формате строки.
        """
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD.get_secret_value()}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    def get_redis_url(self) -> str:
        """
        Получает URL для Redis базы данных.

        :return: URL базы данных в формате строки.
        """
        return (
            f"redis://{self.REDIS_LOGIN}:{self.REDIS_PASSWORD.get_secret_value()}@{self.REDIS_HOST}:6379/{self.NUM_DB}"
        )


# Получаем параметры для загрузки переменных среды
settings = Settings()
# Хранилище FSM
print(settings.get_redis_url())
storage = RedisStorage.from_url(settings.get_redis_url())

# Инициализируем бота и диспетчер
bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
# dp = Dispatcher(storage=MemoryStorage())
dp = Dispatcher(storage=storage)
admins = settings.ADMIN_IDS


# database_url = settings.DB_URL

def user_filter(record: dict) -> bool:
    """Фильтр для логгера, проверяющий наличие ключа 'user' в extra данных."""
    return bool(record["extra"].get("user"))


def filename_filter(record: dict) -> bool:
    """Фильтр для логгера, проверяющий наличие ключа 'filename' в extra данных."""
    return bool(record["extra"].get("filename"))


def default_filter(record: dict) -> bool:
    """Фильтр для логов без bind (если нет user и filename)."""
    return not (record["extra"].get("user") or record["extra"].get("filename"))


# Удаляем все существующие обработчики
logger.remove()

# Глобальная конфигурация extra (но она не будет работать, если bind не передаст данные)
logger.configure(extra={"ip": "", "user": "", "filename": ""})

# Настройка логирования для stdout (Только если есть user или filename)
logger.add(
    sys.stdout,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> - "
           "<level>{level:^8}</level> - "
           "<cyan>{name}</cyan>:<magenta>{line}</magenta> - "
           "<yellow>{function}</yellow> - "
           "<white>{message}</white> <magenta>{extra[filename]:^10}</magenta>"
           "<magenta>{extra[user]:^10}</magenta>",
    filter=lambda record: user_filter(record) or filename_filter(record),
    catch=True,
    diagnose=True,
    enqueue=True,
)

# Логирование stdout (Только если нет bind)
logger.add(
    sys.stdout,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> - "
           "<level>{level:^8}</level> - "
           "<cyan>{name}</cyan>:<magenta>{line}</magenta> - "
           "<yellow>{function}</yellow> - "
           "<white>{message}</white>",
    filter=default_filter,  # Показывает только если нет extra["user"] и extra["filename"]
    catch=True,
    diagnose=True,
    enqueue=True,
)

# Настройка логирования в файл (Только если есть filename)
log_file_path = os.path.join(settings.BASE_DIR or ".", "file.log")

logger.add(
    log_file_path,
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {name}:{line} - {function} - {message} {extra[filename]}",
    rotation="1 day",
    retention="7 days",
    catch=True,
    backtrace=True,
    diagnose=True,
    filter=filename_filter,
    enqueue=True,
)

# Тестирование фильтров
if __name__ == '__main__':
    logger.error("Лог без bind (должен попасть в stdout без фильтра)")  # Только в stdout
    logger.bind(filename="log.txt").error("Лог с filename (должен попасть в файл)")  # Только в файл
    logger.bind(user="boris").error("Лог с user (должен попасть в stdout)")  # Только в stdout
    logger.bind(filename="log.txt", user="boris").error("Лог с обоими (должен попасть в stdout и файл)")  # Везде
