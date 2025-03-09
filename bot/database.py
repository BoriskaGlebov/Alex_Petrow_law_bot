from datetime import datetime
from functools import wraps
from typing import Any

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column
from typing_extensions import Annotated

from bot.config import settings

DATABASE_URL = settings.get_db_url()
# TEST_DATABASE_URL = settings.get_test_db_url()
# настройки БД для работы как с боевой так и с тестовой базой данных
engine = create_async_engine(DATABASE_URL)
# test_engine = create_async_engine(TEST_DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
# async_test_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

# настройка аннотаций
int_pk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
created_at = Annotated[datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=datetime.now)]
str_uniq = Annotated[str, mapped_column(unique=True, nullable=False)]
str_null_true = Annotated[str, mapped_column(nullable=True)]


def connection(isolation_level: str = None):
    """
    Декоратор для автоматического управления сессией базы данных.

    !Когда стоит указывать уровень изоляции вручную?
    -READ COMMITTED (по умолчанию) — для большинства CRUD-операций.
    -REPEATABLE READ — для сложных аналитических запросов или, например, расчёта рейтинга.
    -SERIALIZABLE — если нужна полная защита от конкурентных изменений (финансы, бухгалтерия).
    ТО есть можно поставить вообще по умолчанию READ COMMITED, но посмотрим
    Args:
        isolation_level (str, optional): Уровень изоляции транзакции (например, "SERIALIZABLE").

    Returns:
        function: Декорированная асинхронная функция с доступом к сессии.
    """

    def decorator(method):
        @wraps(method)
        async def wrapper(*args, **kwargs):
            async with async_session() as session:
                try:
                    # Устанавливаем уровень изоляции, если передан
                    if isolation_level:
                        await session.execute(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}")

                    # Передаём сессию в декорированный метод
                    return await method(*args, session=session, **kwargs)
                except Exception as e:
                    await session.rollback()  # Откат транзакции при ошибке
                    raise e
                finally:
                    await session.close()  # Закрываем сессию после использования

        return wrapper

    return decorator


class Base(AsyncAttrs, DeclarativeBase):
    """
    Базовый класс для всех моделей базы данных.

    Этот класс предоставляет общие атрибуты и методы для всех моделей,
    основанных на SQLAlchemy. Он определяет автоматические поля
    `created_at` и `updated_at`, а также метод `to_dict`, который
    преобразует экземпляр модели в словарь.

    Attributes:
       created_at (Mapped[datetime]): Дата и время создания записи.
       updated_at (Mapped[datetime]): Дата и время последнего обновления записи.
    """

    __abstract__ = True

    @declared_attr.directive
    def __tablename__(self) -> str:
        return f"{self.__name__.lower()}s"

    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    def to_dict(self) -> dict[str, Any]:
        """
        Преобразует экземпляр модели в словарь.

        Возвращает:
            dict[str, Any]: Словарь, содержащий имена колонок и их значения.
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
