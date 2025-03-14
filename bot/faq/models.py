from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from bot.database import Base, int_pk


class Questions(Base):
    """
    Модель таблицы для хранения вопросов и ответов.

    Эта модель используется для хранения вопросов и их соответствующих ответов.
    Каждая запись в таблице содержит уникальный идентификатор (id), текст вопроса (question)
    и текст ответа (answer). Структура таблицы используется для эффективного хранения и
    извлечения вопросов и ответов, например, для частых запросов на FAQ.

    Атрибуты:
    - id (int): Уникальный идентификатор вопроса (первичный ключ).
    - question (str): Текст вопроса, который задается пользователем.
    - answer (str): Ответ на заданный вопрос.
    """

    id: Mapped[int_pk]
    question: Mapped[str] = mapped_column(
        String, nullable=False
    )  # Текст вопроса (обязательное поле)
    answer: Mapped[str] = mapped_column(
        String, nullable=False
    )  # Текст ответа (обязательное поле)

    def __repr__(self):
        """
        Представление объекта в виде строки для отладки.
        Возвращает строку с ID, текстом вопроса и текста ответа.

        Пример:
        <Question(id=1, question='Как работает бот?', answer='Бот выполняет команды пользователя.')>
        """
        return (
            f"<Question(id={self.id}, question={self.question}, answer={self.answer})>"
        )
