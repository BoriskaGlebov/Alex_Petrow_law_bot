from typing import Type

from bot.dao.base import BaseDAO
from bot.faq.models import Questions


class QuestionsDAO(BaseDAO[Questions]):
    """
    Класс для работы с вопросами и ответами в базе данных.

    Этот класс наследует методы от `BaseDAO` и предоставляет дополнительные
    операции для работы с объектами модели `Questions`.

    Атрибуты:
        model (Type[Questions]): Модель, с которой работает данный DAO (в данном случае, таблица вопросов и ответов).
    """

    model: Type[Questions] = (
        Questions  # Модель для работы с данными вопросов и ответов.
    )
