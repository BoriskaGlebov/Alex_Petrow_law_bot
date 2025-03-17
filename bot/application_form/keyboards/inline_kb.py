from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
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


def product_kb(product_id, price) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💸 Купить", callback_data=f"buy_{product_id}_{price}")
    kb.button(text="🛍 Назад", callback_data="catalog")
    kb.button(text="🏠 На главную", callback_data="home")
    kb.adjust(2)
    return kb.as_markup()


def get_product_buy_kb(price) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Оплатить {price}₽", pay=True)],
            [InlineKeyboardButton(text="Отменить", callback_data="home")],
        ]
    )
