from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

#
# def admin_keyboard() -> InlineKeyboardMarkup:
#     kb = InlineKeyboardBuilder()
#     kb.button(text="Кнопка инлайн меню", callback_data="back_home")
#
#     kb.adjust(1)
#     return kb.as_markup()


def owner_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❎ Cобственные средства", callback_data="owner_True")
    builder.button(text="❎ Средства клиенты", callback_data="owner_False")
    builder.adjust(2)
    return builder.as_markup()
def can_contact_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❎ Могу", callback_data="can_contact_True")
    builder.button(text="❎ Не могу", callback_data="can_contact_False")
    builder.adjust(2)
    return builder.as_markup()