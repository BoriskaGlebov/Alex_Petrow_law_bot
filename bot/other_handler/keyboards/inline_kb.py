# from aiogram.types import InlineKeyboardMarkup
# from aiogram.utils.keyboard import InlineKeyboardBuilder
#
#
# def admin_keyboard() -> InlineKeyboardMarkup:
#     kb = InlineKeyboardBuilder()
#     kb.button(text="Кнопка инлайн меню", callback_data="back_home")
#     kb.adjust(1)
#     return kb.as_markup()
#
#
# def approve_keyboard(approve: str, dismiss: str) -> InlineKeyboardMarkup:
#     """
#     Создает inline-клавиатуру с кастомными текстами для кнопок подтверждения и отклонения.
#
#     Аргументы:
#         approve (str): Текст для кнопки подтверждения (например, "Да").
#         dismiss (str): Текст для кнопки отклонения (например, "Нет").
#
#     Возвращает:
#         InlineKeyboardMarkup: Объект клавиатуры с двумя кнопками:
#             - ✅ {approve} (callback_data='approve_True')
#             - ❌ {dismiss} (callback_data='approve_False')
#     """
#     builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
#
#     # Добавляем кнопки
#     builder.button(text=f'✅ {approve}', callback_data='approve_True')
#     builder.button(text=f'❌ {dismiss}', callback_data='approve_False')
#
#     # Делаем клавиатуру в один ряд по 2 кнопки
#     builder.adjust(2)
#
#     return builder.as_markup()
