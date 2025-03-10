import asyncio
from collections import namedtuple

from aiogram import F
from aiogram.filters import CommandObject, CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.chat_action import ChatActionSender
from loguru import logger
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.router import Router
from sqlalchemy.util import merge_lists_w_ordering

from bot.application_form.keyboards.inline_kb import approve_keyboard
from bot.config import bot
from bot.database import connection
from bot.application_form.utils import extract_number
from bot.users.dao import UserDAO
from bot.users.keyboards.markup_kb import main_kb
from bot.users.schemas import TelegramIDModel, UserModel
from bot.users.utils import get_refer_id_or_none

echo_router = Router()


@echo_router.message(F.text)
async def echo_start(message: Message, **kwargs) -> None:
    """
    Обработчик для получения текстовых сообщений от пользователя и отправки стандартного ответа.

    Эта функция срабатывает, когда пользователь отправляет любое текстовое сообщение,
    и бот отвечает сообщением с информацией о том, что запрос не может быть обработан.

    Args:
        message (Message): Объект, представляющий сообщение, которое пользователь отправил боту.
        **kwargs: Дополнительные аргументы, которые могут быть переданы через декоратор (например, метаданные о сообщении).

    Returns:
        None: Функция не возвращает значения, но отправляет ответное сообщение пользователю.

    Raises:
        Exception: Если возникает ошибка при обработке сообщения, она будет зафиксирована в логе,
                    и пользователю будет отправлено сообщение о произошедшей ошибке.

    Example:
        - Пользователь отправляет текстовое сообщение.
        - Бот отвечает: "Видимо пошло что-то не так. Я скоро разберусь! Я пока не знаю как ответить на ваш запрос!"
    """
    try:
        await message.answer(
            "Видимо пошло что-то не так. Я скоро разберусь!\nЯ пока не знаю как ответить на ваш запрос!"
        )
    except Exception as e:
        # Логируем ошибку, если она возникла
        logger.error(f"Ошибка при выполнении команды /application для пользователя {message.from_user.id}: {e}")
        await message.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже.")
