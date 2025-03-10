from bot.faq.models import Questions


def update_cache(old_questions: dict[int, Questions], new_questions: dict[int, Questions]) -> dict[int, Questions]:
    """
    Обновляет кеш вопросов, заменяя старые данные новыми.

    Алгоритм работы:
    1. Если `new_questions` не пуст, обновляет `old_questions` новыми данными.
    2. Добавляет новые или изменённые записи из `new_questions`.
    3. Удаляет записи, которых нет в `new_questions`, но они присутствуют в `old_questions`.
    4. Если `new_questions` пуст, возвращает `old_questions` без изменений.

    :param old_questions: Текущий кеш вопросов (словарь {id: Questions}).
    :param new_questions: Новый набор вопросов для обновления (словарь {id: Questions}).
    :return: Обновлённый кеш с актуальными вопросами.
    """
    if new_questions:
        old_keys = list(old_questions.keys())

        old_questions.update(new_questions)  # Обновляем кеш новыми вопросами
        for key in old_keys:  # Удаляем вопросы, которых нет в новом наборе
            if key not in new_questions:
                del old_questions[key]
        return old_questions
    else:
        return old_questions
