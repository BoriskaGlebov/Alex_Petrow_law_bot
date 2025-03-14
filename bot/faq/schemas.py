from typing import Optional

from pydantic import BaseModel


class QuestionFilter(BaseModel):
    """
    Модель фильтра для поиска вопросов по различным критериям.
    """

    id: Optional[int] = None  # Фильтр по ID
    question: Optional[str] = None  # Фильтр по тексту вопроса
    answer: Optional[str] = None  # Фильтр по тексту ответа

    class Config:
        from_attributes = True  # Заменено orm_mode на from_attributes
