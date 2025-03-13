from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Кнопка инлайн меню", callback_data="back_home")
    kb.adjust(1)
    return kb.as_markup()


def approve_admin_keyboard(
    approve: str, dismiss: str, user_id: int, application_id: int
) -> InlineKeyboardMarkup:
    """
    Создает inline-клавиатуру с кастомными текстами для кнопок подтверждения и отклонения.

    Аргументы:
        approve (str): Текст для кнопки подтверждения (например, "Да").
        dismiss (str): Текст для кнопки отклонения (например, "Нет").
        user_id (int): Идентификатор пользователя, чья заявка обрабатывается.
        application_id (int): Идентификатор заявки, для которой создаются кнопки.

    Возвращает:
        InlineKeyboardMarkup: Объект клавиатуры с двумя кнопками:
            - ✅ {approve} (callback_data='approve_True_{user_id}_{application_id}')
            - ❌ {dismiss} (callback_data='approve_False_{user_id}_{application_id}')
    """
    # Инициализация билдера для inline клавиатуры
    builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    # Добавляем кнопки с кастомными текстами и соответствующими callback_data
    builder.button(
        text=f"✅ {approve}",
        callback_data=f"approve_admin_True_{user_id}_{application_id}",
    )
    builder.button(
        text=f"❌ {dismiss}",
        callback_data=f"approve_admin_False_{user_id}_{application_id}",
    )

    # Настроим клавиатуру, чтобы кнопки располагались в одном ряду
    builder.adjust(2)

    # Возвращаем готовую клавиатуру
    return builder.as_markup()
