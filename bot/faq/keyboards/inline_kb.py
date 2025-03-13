from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.faq.models import Questions


# def admin_keyboard() -> InlineKeyboardMarkup:
#     kb = InlineKeyboardBuilder()
#     kb.button(text="Кнопка инлайн меню", callback_data="back_home")
#     kb.adjust(1)
#     return kb.as_markup()


def faq_inline_keyboard(questions: list[Questions]) -> InlineKeyboardMarkup:
    """
    Создает инлайн клавиатуру с вопросами и кнопкой "На главную".

    Args:
        questions (list[Questions]): Список объектов с вопросами и ответами.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками.
    """
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки для каждого вопроса
    for el in questions:
        builder.button(text=el.question, callback_data=f'qst_{el.id}')

    # Добавляем кнопку "На главную" в конце
    builder.row(InlineKeyboardButton(
        text='На главную',
        callback_data='back_home',
    ))

    # Создаем правила распределения кнопок по строкам
    # buttons_rule = [2 for _ in questions[::2]]  # Каждые две кнопки в строке

    # Если количество кнопок нечетное, последняя строка будет с одной кнопкой
    # if len(questions) % 2 != 0:
    #     buttons_rule[-1] = 1

    # Добавляем строку для кнопок
    # buttons_rule.append(1)  # Для кнопки "На главную"
    # builder.adjust(*buttons_rule)
    builder.adjust(1)
    return builder.as_markup()
