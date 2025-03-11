from sqlalchemy import Enum, ForeignKey, Integer, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database import Base, int_pk, async_session
from enum import Enum as PyEnum


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
        photos (List[int]): Список ID фотографий.
        videos (List[int]): Список ID видео.
        debts (List['BankDebt']): Список задолженностей в разных банках.
    """

    id: Mapped[int_pk]  # Уникальный идентификатор заявки (первичный ключ).

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )  # ID пользователя (связь с User)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.PENDING, nullable=False
    )  # Статус заявки

    text_application: Mapped[str] = mapped_column(String, nullable=True)
    # Связь с пользователем
    user = relationship("User", back_populates="applications", lazy="selectin")

    # Связь с фотографиями и видео
    photos = relationship("Photo", back_populates="application", cascade="all, delete-orphan", lazy="selectin")
    videos = relationship("Video", back_populates="application", cascade="all, delete-orphan", lazy="selectin")

    # Связь с задолженностями в банках
    debts = relationship("BankDebt", back_populates="application", cascade="all, delete-orphan", lazy="selectin")


class Photo(Base):
    """
    Модель для хранения фотографий пользователей.
    Атрибуты:
        id (int): Уникальный идентификатор записи (первичный ключ).
        file_id (str): Уникальный идентификатор фотографии в Telegram.
        application_id (int): ID заявки, к которой привязана фотография.
    """

    id: Mapped[int_pk]  # Уникальный идентификатор записи (PK)
    file_id: Mapped[str] = mapped_column(String, nullable=False, unique=False)  # ID файла в Telegram
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"),
                                                nullable=False)  # ID заявки

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
    file_id: Mapped[str] = mapped_column(String, nullable=False, unique=False)  # ID файла в Telegram
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"),
                                                nullable=False)  # ID заявки

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
    total_amount: Mapped[float] = mapped_column(BigInteger, nullable=False)  # Сумма задолженности
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"),
                                                nullable=False)  # ID заявки

    # Связь с заявкой
    application = relationship("Application", back_populates="debts")
