import os
import sys
from typing import List

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from loguru import logger
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

    # BASE_DIR: Optional[str] = None

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
        return f"redis://{self.REDIS_LOGIN}:{self.REDIS_PASSWORD.get_secret_value()}@{self.REDIS_HOST}:6379/{self.NUM_DB}"


# Получаем параметры для загрузки переменных среды
settings = Settings()
# Хранилище FSM
storage = RedisStorage.from_url(settings.get_redis_url())

# Инициализируем бота и диспетчер
bot: Bot = Bot(
    token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
# Это если работать без Redis
# dp = Dispatcher(storage=MemoryStorage())
dp = Dispatcher(storage=storage)
admins = settings.ADMIN_IDS


def user_filter(record: dict) -> bool:
    """Фильтр для логгера, проверяющий наличие ключа 'user' в extra данных."""
    return bool(record["extra"].get("user") and (record["extra"].get("user") != "-"))


def filename_filter(record: dict) -> bool:
    """Фильтр для логгера, проверяющий наличие ключа 'filename' в extra данных."""
    return bool(record["extra"].get("filename"))


def default_filter(record: dict) -> bool:
    """Фильтр для логов без bind (если нет user и filename)."""
    # return not (record["extra"].get("user") or record["extra"].get("f
    # Для отладкиilename"))
    if record["extra"].get("user") == "-":
        return True
    else:
        return not record["extra"].get("user")


log_dir = os.path.join(os.path.dirname(__file__), "logs")
if not os.path.exists(log_dir):
    os.mkdir(log_dir)
# Удаляем все существующие обработчики
logger.remove()

# Глобальная конфигурация extra (но она не будет работать, если bind не передаст данные)
# logger.configure(extra={"ip": "-", "user": "-", "filename": "-"})
logger.configure(extra={"user": "-", })
# TODO установи адекватный уровень логирования
# Настройка логирования для stdout (Только если есть user или filename)
logger.add(
    sys.stdout,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> - "
           "<level>{level:^8}</level> - "
           "<cyan>{name}</cyan>:<magenta>{line}</magenta> - "
           "<yellow>{function}</yellow> - "
           "<white>{message}</white>"
           "<magenta>{extra[user]:^10}</magenta>",
    # filter=lambda record: user_filter(record) or filename_filter(record),
    filter=user_filter,
    catch=True,
    diagnose=True,
    enqueue=True,
)

# TODO установи адекватный уровень логирования
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
# log_file_path = os.path.join(settings.BASE_DIR or ".", "file.log")
log_file_path = os.path.join(log_dir or ".", "file.log")
# TODO установи адекватный уровень логирования
logger.add(
    log_file_path,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> - "
           "<level>{level:^8}</level> - "
           "<cyan>{name}</cyan>:<magenta>{line}</magenta> - "
           "<yellow>{function}</yellow> - "
           "<white>{message}</white>",
    # "<magenta>{extra[user]:^10}</magenta>",
    rotation="1 day",
    retention="7 days",
    catch=True,
    backtrace=True,
    diagnose=True,
    # filter=default_filter,
    enqueue=True,
)

# Тестирование фильтров
if __name__ == "__main__":
    # logger.info("Лог без bind (должен попасть в stdout без фильтра и в файл)")
    # logger.bind(user="boris").info("Лог с user (должен попасть в stdout с user-фильтром)")
    # logger.bind(user="boris").info("Лог с user и filename (stdout и файл)")
    # logger.bind(user="").info("Лог с пустым user (должен попасть в файл, но не в stdout с user-фильтром)")
    print(log_dir)
