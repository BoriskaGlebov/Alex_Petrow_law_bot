import asyncio
from typing import Optional

from aiogram import F
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.chat_action import ChatActionSender
from loguru import logger
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.dispatcher.router import Router

import bot.application_form.dao
from bot.config import bot, settings
from bot.database import connection
from bot.users.dao import UserDAO
from bot.users.keyboards.inline_kb import approve_keyboard
from bot.users.keyboards.markup_kb import main_kb
from bot.users.schemas import TelegramIDModel, UserModel
from bot.users.utils import get_refer_id_or_none

user_router = Router()


class CheckForm(StatesGroup):
    age = State()
    resident = State()


@user_router.message(CommandStart())
@connection()
async def cmd_start(message: Message, command: CommandObject, session, state: FSMContext, **kwargs) -> None:
    """
    Обработчик команды /start для Telegram-бота. Проверяет, существует ли пользователь в базе данных,
    и если нет — регистрирует нового пользователя, привязывая его к реферальному ID (если он передан).

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
        msg2 = f"Для составления заявки 📄 мне необходимо заполнить анкету. Это займет несколько минут."
        msg3 = f"Вам нужно будет ответить на несколько вопросов ❔ и приложить необходимые 🪪 документы."
        msg4 = f"Вам уже исполнилось 🔞 18 лет? "

        # Очищаем состояние
        await state.clear()

        # Получаем ID пользователя из сообщения
        user_id: int = message.from_user.id

        # Проверяем, существует ли уже пользователь в базе данных
        user_info = await UserDAO.find_one_or_none(session=session,
                                                   filters=TelegramIDModel(telegram_id=user_id))

        # Если пользователь уже существует, отправляем приветственное сообщение
        if user_info:
            async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
                await message.answer(f"👋 Привет, {message.from_user.full_name}! Необходимо ответить на пару вопросов:",reply_markup=ReplyKeyboardRemove())
                await asyncio.sleep(2)
                await message.answer(msg4, reply_markup=approve_keyboard("Да", "Нет"))
                await state.set_state(CheckForm.age)
            return

        # Определяем реферальный ID, если он был передан в аргументах команды
        ref_id: Optional[int] = get_refer_id_or_none(command_args=command.args, user_id=user_id)

        # Создаем нового пользователя и добавляем его в базу данных
        values = UserModel(telegram_id=user_id,
                           username=message.from_user.username,
                           first_name=message.from_user.first_name,
                           last_name=message.from_user.last_name,
                           referral_id=ref_id)
        await UserDAO.add(session=session, values=values)

        # Формируем сообщение для пользователя, в зависимости от наличия реферального ID
        ref_message = f" Вы успешно закреплены за пользователем с ID {ref_id}" if ref_id else ""

        # Отправляем сообщение пользователю
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            await asyncio.sleep(2)
            await message.answer(msg1)
            await asyncio.sleep(2)
            await message.answer(msg2)
            await asyncio.sleep(2)
            await message.answer(msg3)
            await asyncio.sleep(2)
            await message.answer(msg4, reply_markup=approve_keyboard("Да", "Нет"))
            await state.set_state(CheckForm.age)

    except Exception as e:
        # Логируем ошибку, если она возникла
        logger.error(f"Ошибка при выполнении команды /start для пользователя {message.from_user.id}: {e}")
        await message.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже.")


@user_router.callback_query(F.data.startswith('approve_'), CheckForm.age)
async def age_callback(call: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик callback-запросов для проверки возраста пользователя.

    Этот обработчик вызывается, когда пользователь отвечает на вопрос о возрасте в анкете.
    Если пользователь подтвердил, что ему исполнилось 18 лет, он переходит к следующему вопросу.
    В противном случае, анкета обнуляется, и пользователю отправляется сообщение о том, что
    он не может воспользоваться услугами.

    Args:
        call (CallbackQuery): Объект callback-запроса, который содержит данные о взаимодействии пользователя с клавиатурой.
        state (FSMContext): Контекст машины состояний, в котором хранятся данные анкеты.

    Returns:
        None: Функция не возвращает значения, но отправляет сообщение пользователю.
    """
    try:
        await call.answer(text="Проверяю ввод", show_alert=False)
        approve_inf = call.data.replace('approve_', '')
        approve_inf = True if approve_inf == "True" else False

        if approve_inf:
            await state.update_data(age=approve_inf)
            async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
                await asyncio.sleep(2)
                await bot.send_message(chat_id=call.message.chat.id,
                                       text='Вы являетесь налоговым резитентом Российской Федерации?🇷🇺',
                                       reply_markup=approve_keyboard("Да", "Нет"))
                await state.set_state(CheckForm.resident)
        else:
            await state.clear()
            await bot.send_message(chat_id=call.message.chat.id,
                                   text="К сожалению мы не предоставляем услуги лицам младше 🔞 18 лет!")

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        await call.message.answer("Произошла ошибка. Попробуйте снова.")


@user_router.callback_query(F.data.startswith('approve_'), CheckForm.resident)
async def resident_callback(call: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик callback-запросов для проверки налогового резидентства пользователя.

    Этот обработчик вызывается, когда пользователь отвечает на вопрос о налоговом резидентстве в анкете.
    Если пользователь является налоговым резидентом России, ему показывается основное меню,
    иначе анкета обнуляется, и пользователю отправляется сообщение о том, что бот не работает с налоговыми резидентами других стран.

    Args:
        call (CallbackQuery): Объект callback-запроса, который содержит данные о взаимодействии пользователя с клавиатурой.
        state (FSMContext): Контекст машины состояний, в котором хранятся данные анкеты.

    Returns:
        None: Функция не возвращает значения, но отправляет сообщение пользователю.
    """
    try:
        await call.answer(text="Проверяю ввод", show_alert=False)
        approve_inf = call.data.replace('approve_', '')
        approve_inf = True if approve_inf == "True" else False

        if approve_inf:
            await state.update_data(age=approve_inf)
            async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
                await asyncio.sleep(2)
                await bot.send_message(chat_id=call.message.chat.id,
                                       text='Отлично, выберите один из представленных вариантов 👇',
                                       reply_markup=main_kb())
                await state.clear()
        else:
            await state.clear()
            await bot.send_message(chat_id=call.message.chat.id,
                                   text="К сожалению мы 🧑‍🎓 не работаем с налоговыми резидентами других стран.")

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        await call.message.answer("Произошла ошибка. Попробуйте снова.")


@user_router.message(F.text, CheckForm.age)
@user_router.message(F.text, CheckForm.resident)
async def mistakes_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик для случаев, когда пользователь отправляет текст вместо того, чтобы выбрать одну из кнопок.

    Этот обработчик вызывается, когда пользователь вводит текст в состоянии анкеты, где ожидается выбор из клавиатуры.
    Бот информирует пользователя о том, что нужно выбрать одну из кнопок.

    Args:
        message (Message): Сообщение от пользователя, содержащее его текст.
        state (FSMContext): Контекст машины состояний, где хранятся данные анкеты.

    Returns:
        None: Функция не возвращает значений, но отправляет сообщение пользователю о том, что нужно выбрать кнопку.
    """
    try:
        await message.answer("Необходимо нажать по кнопке 👆")

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
