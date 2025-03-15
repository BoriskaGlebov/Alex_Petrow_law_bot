import asyncio
import re

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender
from bot.config import logger


def get_refer_id_or_none(command_args: str, user_id: int) -> int | None:
    """
    Определяет реферальный ID из аргументов команды. Возвращает реферальный ID, если он валиден, или None,
    если аргументы не соответствуют требованиям (например, если это не число или это ID самого пользователя).

    Args:
        command_args (str): Аргументы команды, содержащие потенциальный реферальный ID.
        user_id (int): ID текущего пользователя, чтобы убедиться, что он не пытается использовать свой собственный ID в качестве реферала.

    Returns:
        int | None: Если аргумент команды является валидным реферальным ID (целое число, больше 0 и не равное user_id),
                    то возвращается этот ID. Иначе возвращается None.
    """
    return (
        int(command_args)
        if command_args
           and command_args.isdigit()
           and int(command_args) > 0
           and int(command_args) != user_id
        else None
    )


def normalize_phone_number(phone: str) -> str:
    """
    Нормализует номер телефона:
    - Добавляет + перед 7, если его нет.
    - Если начинается с 8, заменяет на +7.
    """
    phone = re.sub(r"\D", "", phone)  # Убираем все нецифровые символы

    if phone.startswith("8") and len(phone) == 11:
        phone = "+7" + phone[1:]
    elif phone.startswith("7") and len(phone) == 11:
        phone = "+7" + phone[1:]
    elif len(phone) == 10:  # Если пользователь ввел только 10 цифр (без кода страны)
        phone = "+7" + phone

    return phone if phone.startswith("+") else f"+{phone}"


async def mistakes_handler(message: Message, bot: Bot, state: FSMContext,
                           answer: str = "Пожалуйста, выберите один из вариантов, нажав на кнопку 👆") -> None:
    """
    Обработчик для случаев, когда пользователь отправляет текст вместо того, чтобы выбрать одну из кнопок.

    Этот обработчик вызывается, когда пользователь вводит текст в состоянии анкеты, где ожидается выбор из клавиатуры.
    Бот информирует пользователя о том, что нужно выбрать одну из кнопок.
    По умолчанию - Пожалуйста, выберите один из вариантов, нажав на кнопку ВВЕРХ


    Args:
        message (Message): Сообщение от пользователя, содержащее его текст.
        bot (Bot): Бот, который отправляет сообщения
        state (FSMContext): Контекст машины состояний, где хранятся данные анкеты.
        answer (str) : Ответ по умолчанию, но можно выбирать.

    Returns:
        None: Функция не возвращает значений, но отправляет сообщение пользователю о том, что нужно выбрать кнопку.
    """
    try:
        # Включаем индикатор набора текста
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            await asyncio.sleep(
                0.5
            )  # Немного подождем, чтобы пользователь видел индикатор

            # Отправляем сообщение с просьбой выбрать кнопку
            await message.answer(
                text=answer
            )

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
