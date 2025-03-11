from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.config import admins


def back_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="Кнопка текстового меню")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def main_kb(user_telegram_id: int = None) -> ReplyKeyboardMarkup:
    """
    Формирует клавиатуру для главного меню бота.

    В зависимости от предоставленного ID пользователя (например, если это администратор), функция
    генерирует клавиатуру с нужными кнопками.

    Параметры:
    - `user_telegram_id` (int): Telegram ID пользователя, который вызывает клавиатуру.

    Возвращаемое значение:
    - `ReplyKeyboardMarkup`: Клавиатура, которая будет отображаться пользователю.

    Пример использования:
    ```
    user_telegram_id = 123456789
    keyboard = main_kb(user_telegram_id)
    await message.answer("Выберите действие:", reply_markup=keyboard)
    ```
    """
    # Список кнопок на главной клавиатуре
    kb_list = [
        [KeyboardButton(text="📝 Вывод заблокированных средств")],
        [KeyboardButton(text="📖 База знаний")],

        # Закомментировано, можно добавить в зависимости от потребностей
        # [KeyboardButton(text="👤 Профиль"),
        #  KeyboardButton(text="📚 Каталог")]
    ]

    # Здесь можно раскомментировать и добавить кнопки для администраторов
    # if user_telegram_id in admins:
    #     kb_list.append([KeyboardButton(text="⚙️ Админ панель")])

    # Создаем и возвращаем клавиатуру с параметрами
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)
    return keyboard


def phone_kb() -> ReplyKeyboardMarkup:
    """
    Создает клавиатуру с кнопкой для запроса номера телефона.

    Returns:
        ReplyKeyboardMarkup: Клавиатура с кнопкой запроса номера.
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Поделиться номером", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Нажмите кнопку ниже, чтобы отправить номер телефона"
    )
