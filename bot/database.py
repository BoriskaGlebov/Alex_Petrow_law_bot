from datetime import datetime
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
