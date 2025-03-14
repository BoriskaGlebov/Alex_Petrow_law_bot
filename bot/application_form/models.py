from enum import Enum as PyEnum
from typing import Dict, Optional

from sqlalchemy import JSON, BigInteger, Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database import Base, int_pk


class ApplicationStatus(PyEnum):
    PENDING = "pending"  # Ожидает обработки
    APPROVED = "approved"  # Одобрена
    REJECTED = "rejected"  # Отклонена


class Application(Base):
    """
    Модель заявки, содержащая информацию о заявке пользователя.

    Атрибуты:
        id (int): Уникальный идентификатор заявки (первичный ключ).
        user_id (int): Идентификатор пользователя (внешний ключ, связь с User).
        status (ApplicationStatus): Статус заявки (по умолчанию "pending").
        text_application (Optional[str]): Текстовое описание заявки (может быть пустым).
        admin_message_ids (Dict[int, int]): Словарь соответствий admin_id → message_id.
        owner (bool): Флаг, указывающий, является ли пользователь владельцем заявки (по умолчанию True).
        user (User): Связь с пользователем, создавшим заявку.
        photos (List[Photo]): Связь с фотографиями, прикрепленными к заявке.
        videos (List[Video]): Связь с видеозаписями, прикрепленными к заявке.
        debts (List[BankDebt]): Связь с задолженностями, относящимися к заявке.

    Таблица:
        - Имя таблицы: `applications`
        - Внешние ключи: `user_id` → `users.id` (с каскадным удалением)
    """

    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.PENDING, nullable=False
    )
    text_application: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    admin_message_ids: Mapped[Dict[int, int]] = mapped_column(JSON, default=dict)
    owner: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="applications", lazy="selectin")
    photos = relationship(
        "Photo",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    videos = relationship(
        "Video",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    debts = relationship(
        "BankDebt",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Photo(Base):
    """
    Модель для хранения фотографий пользователей.
    Атрибуты:
        id (int): Уникальный идентификатор записи (первичный ключ).
        file_id (str): Уникальный идентификатор фотографии в Telegram.
        application_id (int): ID заявки, к которой привязана фотография.
    """

    id: Mapped[int_pk]  # Уникальный идентификатор записи (PK)
    file_id: Mapped[str] = mapped_column(
        String, nullable=False, unique=False
    )  # ID файла в Telegram
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )  # ID заявки

    # Связь с заявкой
    application = relationship("Application", back_populates="photos")


class Video(Base):
    """
    Модель для хранения видео пользователей.
    Атрибуты:
        id (int): Уникальный идентификатор записи (первичный ключ).
        file_id (str): Уникальный идентификатор видео в Telegram.
        application_id (int): ID заявки, к которой привязано видео.
    """

    id: Mapped[int_pk]  # Уникальный идентификатор записи (PK)
    file_id: Mapped[str] = mapped_column(
        String, nullable=False, unique=False
    )  # ID файла в Telegram
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )  # ID заявки

    # Связь с заявкой
    application = relationship("Application", back_populates="videos")


class BankDebt(Base):
    """
    Модель для хранения информации о задолженности в банке.
    Атрибуты:
        id (int): Уникальный идентификатор записи (первичный ключ).
        bank_name (str): Название банка.
        total_amount (float): Общая сумма задолженности в банке.
        application_id (int): ID заявки, к которой привязана задолженность.
    """

    id: Mapped[int_pk]  # Уникальный идентификатор записи (PK)
    bank_name: Mapped[str] = mapped_column(String, nullable=False)  # Название банка
    total_amount: Mapped[float] = mapped_column(
        BigInteger, nullable=False
    )  # Сумма задолженности
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )  # ID заявки

    # Связь с заявкой
    application = relationship("Application", back_populates="debts")
