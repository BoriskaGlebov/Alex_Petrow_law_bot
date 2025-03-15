import re
from typing import Optional

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot.application_form.router import ApplicationForm
from bot.users.dao import UserDAO
from bot.users.keyboards.inline_kb import approve_keyboard
from bot.users.keyboards.markup_kb import phone_kb
from bot.users.schemas import TelegramIDModel, UpdateNumberSchema
from bot.users.utils import normalize_phone_number


def extract_number(text: str) -> Optional[int]:
    """
    Извлекает первое число из строки.

    Функция использует регулярное выражение для поиска первого числа в тексте.
    Возвращает первое найденное число в виде целого числа, либо None, если число не найдено.

    Args:
        text (str): Строка, из которой будет извлечено число.

    Returns:
        Optional[int]: Первое найденное число в строке или None, если число не найдено.

    Example:
        extract_number("Цена: 150 рублей") -> 150
        extract_number("Нет чисел здесь") -> None
    """
    match = re.search(r"\b(\d+)\b", text)
    if match:
        return int(match.group(1))
    else:
        return None


async def handle_contact(message: Message, state: FSMContext, session) -> None:
    """
    Обрабатывает получение номера телефона пользователя.
    Поддерживает как кнопку запроса номера, так и ввод вручную.

    Требует корректный номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX.
    """

    user_id = message.from_user.id
    if message.contact:  # Если номер пришел через кнопку
        phone_number = message.contact.phone_number
    else:  # Если пользователь ввел номер вручную
        phone_number = message.text.strip()
        # Проверяем корректность номера
        phone_pattern = re.compile(
            r"^(\+7|8)?\d{10}$"
        )  # Разрешает +7XXXXXXXXXX или 8XXXXXXXXXX
        if not phone_pattern.match(phone_number):
            await message.answer(
                "Ошибка: введите корректный номер телефона в формате +7XXXXXXXXXX или 8XXXXXXXXXX.",
                reply_markup=phone_kb(),
            )
            return

    # Нормализуем номер (добавляем +7, если надо)
    normalized_phone = normalize_phone_number(phone_number)

    # Проверяем, есть ли пользователь в БД
    existing_user = await UserDAO.find_one_or_none(
        session=session, filters=TelegramIDModel(telegram_id=user_id)
    )

    if existing_user and (existing_user.phone_number is None):
        await UserDAO.update(
            filters=TelegramIDModel(telegram_id=user_id),
            values=UpdateNumberSchema(phone_number=normalized_phone),
            session=session,
        )
        await message.answer(
            f"Спасибо! Ваш номер {normalized_phone} сохранен.",
            reply_markup=ReplyKeyboardRemove(),
        )

        await message.answer(
            "Вы хотите оставить 📝 заявку на вывод заблокированных средств?",
            reply_markup=approve_keyboard(
                "Да", "Нет"
            ),  # Предлагаем клавиатуру с вариантами
        )
        await state.set_state(ApplicationForm.approve_work)
    else:
        await message.answer("Ошибка: ваш аккаунт не найден в базе данных.")