from typing import Optional

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database import Base, int_pk


class User(Base):
    """
    Модель пользователя, представляющая запись в таблице пользователей базы данных.

    Атрибуты:
        id (int): Уникальный идентификатор пользователя.
        telegram_id (int): Уникальный идентификатор пользователя в Telegram.
        username (Optional[str]): Имя пользователя в Telegram (необязательное поле).
        first_name (Optional[str]): Имя пользователя (необязательное поле).
        last_name (Optional[str]): Фамилия пользователя (необязательное поле).
        referral_id (Optional[int]): Идентификатор реферала пользователя (необязательное поле).
        phone_number (Optional[str]): Номер телефона пользователя (необязательное поле).
        owner (bool): Флаг собственника, по умолчанию True.
    """

    id: Mapped[int_pk]  # Уникальный идентификатор (первичный ключ).

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    """
    Уникальный идентификатор пользователя в Telegram.
    Тип: int
    """

    username: Mapped[Optional[str]]
    """
    Имя пользователя в Telegram.
    Тип: Optional[str] (необязательное поле)
    """

    first_name: Mapped[Optional[str]]
    """
    Имя пользователя.
    Тип: Optional[str] (необязательное поле)
    """

    last_name: Mapped[Optional[str]]
    """
    Фамилия пользователя.
    Тип: Optional[str] (необязательное поле)
    """

    referral_id: Mapped[Optional[int]]
    """
    Идентификатор реферала пользователя.
    Тип: Optional[int] (необязательное поле)
    """

    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    """
    Номер телефона пользователя.
    Тип: Optional[str] (необязательное поле, длина 20 символов)
    """

    owner: Mapped[bool] = mapped_column(Boolean, default=True)
    """
    Флаг собственника.
    Тип: bool, по умолчанию True.
    """

    # Двусторонняя связь с Application
    applications = relationship(
        "Application",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
