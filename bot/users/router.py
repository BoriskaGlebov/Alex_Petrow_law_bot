import asyncio
from typing import Any, Optional

from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.utils.chat_action import ChatActionSender
from loguru import logger

import bot.application_form.dao
from bot.config import bot
from bot.database import connection
from bot.users.dao import UserDAO
from bot.users.keyboards.markup_kb import main_kb
from bot.users.schemas import TelegramIDModel, UserModel
from bot.users.utils import get_refer_id_or_none, mistakes_handler

user_router = Router()


class CheckForm(StatesGroup):
    age = State()
    resident = State()


@user_router.message(Command("admin"))
async def admin_start(message: Message, state: FSMContext, **kwargs: Any) -> None:
    """
    Обрабатывает команду /admin, очищает состояние пользователя и сообщает о том,
    что администратор ожидает заявки.

    Команда /admin используется для запуска сессии администратора, очищая
    текущее состояние пользователя. В случае ошибки отправляется сообщение с
    уведомлением о проблемах при обработке.

    Аргументы:
        message (Message): Сообщение от пользователя, которое вызвало команду /admin.
        state (FSMContext): Контекст состояния для пользователя, который будет очищен.
        **kwargs (Any): Дополнительные параметры, передаваемые в обработчик.

    Возвращает:
        None: Не возвращает значений, только выполняет действия с сообщением и состоянием.

    Исключения:
        Exception: В случае ошибки при выполнении команды будет сгенерировано исключение.
    """
    try:
        # Очищаем состояние пользователя
        await state.clear()
        await message.answer("Ожидаю заявки как Администратор")

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при выполнении команды /admin: {e}")
        await message.answer(
            "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже."
        )


@user_router.message(CommandStart())
@connection()
async def cmd_start(
        message: Message, command: CommandObject, session, state: FSMContext, **kwargs
) -> None:
    """
    Обработчик команды /start для Telegram-бота. Проверяет, существует ли пользователь в базе данных,
    и если нет — регистрирует нового пользователя, привязывая его к реферальному ID (если он передан).

    Оптимизировано выполнение с минимизацией задержек и улучшением работы с базой данных.

    Args:
        message (Message): Сообщение, которое пользователь отправил боту.
        command (CommandObject): Объект, содержащий информацию о команде и ее аргументах.
        session: Сессия для работы с базой данных (тип: `AsyncSession`).
        state (FSMContext): Состояние машины состояний, обнуляется для предотвращения ошибок пользователя.
        **kwargs: Дополнительные аргументы, переданные через декоратор.

    Returns:
        None: Функция не возвращает значения, но отправляет сообщения в чат с пользователем.

    Raises:
        Exception: Если при обработке команды возникает ошибка, она будет зафиксирована в логе.
    """
    try:
        # Установочные данные
        inf_bot = await bot.get_me()
        msg1 = f"🤖 <b>Здравствуйте! Меня зовут {inf_bot.first_name}. Я секретарь группы юридической помощи.</b>."
        msg2 = "Для составления заявки 📄 мне необходимо заполнить анкету. Это займет несколько минут."
        msg3 = "Вам нужно будет ответить на несколько вопросов ❔ и приложить необходимые 🪪 документы."
        # msg4 = "Вам  (вашему клиенту)  уже исполнилось 🔞 18 лет? "
        msg4 = "Нужно выбрать одну из услуг 👇"

        # Очищаем состояние
        await state.clear()

        # Получаем ID пользователя из сообщения
        user_id: int = message.from_user.id

        # Включаем индикатор набора текста
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            # Проверяем, существует ли уже пользователь в базе данных
            user_info = await UserDAO.find_one_or_none(
                session=session, filters=TelegramIDModel(telegram_id=user_id)
            )

            # Если пользователь уже существует, отправляем сообщение
            if user_info:
                # Сообщение для существующего пользователя
                response_message = f"👋 Привет, {message.from_user.full_name}! Необходимо ответить на пару вопросов:"
                follow_up_message = "Нужно выбрать одну из услуг 👇"
                reply_markup = main_kb()
                # await state.set_state(CheckForm.age)

                # Отправляем все сообщения
                await message.answer(
                    response_message, reply_markup=ReplyKeyboardRemove()
                )
                await message.answer(follow_up_message, reply_markup=reply_markup)
            else:
                # Определяем реферальный ID, если он был передан
                ref_id: Optional[int] = get_refer_id_or_none(
                    command_args=command.args, user_id=user_id
                )

                # Создаем нового пользователя и добавляем его в базу данных
                values = UserModel(
                    telegram_id=user_id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                    referral_id=ref_id,
                )
                await UserDAO.add(session=session, values=values)

                # Формируем сообщение для пользователя, в зависимости от реферального ID
                # ref_message = f" Вы успешно закреплены за пользователем с ID {ref_id}" if ref_id else ""
                response_message = msg1
                follow_up_message = [msg2, msg3, msg4]
                # reply_markup = approve_keyboard("Да", "Нет")
                reply_markup = main_kb()
                # await state.set_state(CheckForm.age)

                # Отправляем все сообщения
                await message.answer(
                    response_message, reply_markup=ReplyKeyboardRemove()
                )
                await asyncio.sleep(0.5)
                await message.answer(follow_up_message[0])
                await asyncio.sleep(0.5)
                await message.answer(follow_up_message[1])
                await asyncio.sleep(0.5)
                await message.answer(follow_up_message[2], reply_markup=reply_markup)

    except Exception as e:
        # Логируем ошибку
        logger.error(
            f"Ошибка при выполнении команды /start для пользователя {message.from_user.id}: {e}"
        )
        await message.answer(
            "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже."
        )





@user_router.message(F.text, CheckForm.age)
@user_router.message(F.text, CheckForm.resident)
async def mistakes_handler_user(message: Message, state: FSMContext) -> None:
    """
    Обработчик сообщений пользователя, который проверяет данные, введенные пользователем в рамках
    формы (например, возраст и место жительства), и обрабатывает ошибки.

    Этот обработчик вызывает функцию `mistakes_handler` для дальнейшей обработки сообщений и ошибок,
    если введенные данные некорректны.

    Параметры:
    ----------
    message : Message
        Сообщение от пользователя, содержащее текстовый ввод. Включает данные, которые были отправлены
        пользователем в рамках ввода (например, возраст или место жительства).

    state : FSMContext
        Контекст состояния машины состояний (FSM) для отслеживания данных состояния пользователя.
        Используется для хранения промежуточных данных в процессе ввода формы.

    Возвращаемое значение:
    ----------------------
    None
        Функция не возвращает значение, так как она выполняет побочные эффекты — обработку
        и корректировку состояния бота в ответ на сообщение пользователя.

    Логика:
    -------
    - Обработчик срабатывает на текстовые сообщения, которые соответствуют полям ввода формы:
      `CheckForm.age` и `CheckForm.resident`.
    - Он передает сообщение и текущий контекст состояния в функцию `mistakes_handler` для дальнейшей
      обработки ошибок ввода, таких как неверный возраст или место жительства.
    """
    await mistakes_handler(message=message, bot=bot, state=state)
