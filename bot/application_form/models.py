from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, ForeignKey, String, Text, Enum
from typing import Optional
from bot.database import Base, int_pk
import enum


class ApplicationStatus(enum.Enum):
    PENDING = "pending"  # Ожидает обработки
    APPROVED = "approved"  # Одобрена
    REJECTED = "rejected"  # Отклонена


class Application(Base):
    """
    Модель заявки, содержащая информацию о заявке пользователя.

    Атрибуты:
        id (int): Уникальный идентификатор заявки (первичный ключ).
        user_id (int): Идентификатор пользователя (внешний ключ, связь с User).
        text_application (str): Текст заявки.
        media_id (Optional[int]): Ссылка на медиафайлы (внешний ключ на MediaFiles).
        status (ApplicationStatus): Статус заявки (по умолчанию "pending").
    """

    id: Mapped[int_pk]  # Уникальный идентификатор заявки (первичный ключ).

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, unique=True
    )  # ID пользователя
    contact_name:Mapped[str]=mapped_column(String,nullable=True)
    text_application: Mapped[str] = mapped_column(Text, nullable=False)  # Текст заявки

    # media_id: Mapped[Optional[int]] = mapped_column(
    #     ForeignKey("mediafiles.id"), nullable=True
    # )  # ID медиафайлов

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.PENDING, nullable=False
    )  # Статус заявки

    # Связь с пользователем и медиафайлами
    user = relationship("User", back_populates="applications")
    media = relationship("MediaFile", back_populates="applications", lazy="joined")


class MediaFile(Base):
    """
    Модель для хранения медиафайлов пользователей.

    Атрибуты:
        id (int): Уникальный идентификатор записи (первичный ключ).
        file_id (str): Уникальный идентификатор файла в Telegram.
        application_id (int): ID заявки, к которой привязан файл.
    """

    id: Mapped[int_pk]  # Уникальный идентификатор записи (PK)
    file_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # ID файла в Telegram
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), nullable=False)  # ID заявки
    # Связь с заявкой
    application = relationship("Application", back_populates="media")
