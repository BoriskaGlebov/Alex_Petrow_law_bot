from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Кнопка инлайн меню", callback_data="back_home")

    kb.adjust(1)
    return kb.as_markup()


def approve_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='✅Все верно', callback_data=f'approve_True')
    builder.button(text='❌ Нет, напишу 👇', callback_data=f'approve_False')
    builder.adjust(2)
    return builder.as_markup()