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

application_form_router = Router()


class Form(StatesGroup):
    name = State()
    age = State()
    text_application = State()
    check_state = State()


@application_form_router.message(Command('application'))
@application_form_router.message(F.text.contains('Создать заявку'))
async def application_form_start(message: Message, state: FSMContext, **kwargs) -> None:
    """

    """

    try:
        user_id = message.from_user.id
        user_name = message.from_user.username
        if not user_name:
            async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
                await asyncio.sleep(2)
                await message.answer('Прежде чем начать создавать заявку как к вам можно обращаться?')
            await state.set_state(Form.name)
        else:
            # await state.update_data(name=user_name)
            await message.answer(f"Отлично, давайте создадим заявку. Можно к вам обращаться {user_name}",
                                 reply_markup=approve_keyboard())
            await state.set_state(Form.name)
    except Exception as e:
        # Логируем ошибку, если она возникла
        logger.error(f"Ошибка при выполнении команды /application для пользователя {message.from_user.id}: {e}")
        await message.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже.")


@application_form_router.callback_query(F.data.startswith('approve_'), Form.name)
async def faq_callback(call: CallbackQuery, state: FSMContext) -> None:
    """

    """
    try:
        await call.answer(text="Проверяю ввод", show_alert=False)
        approve_inf = call.data.replace('approve_', '')
        if approve_inf == "True":
            await state.update_data(name=call.from_user.username)
            async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
                await asyncio.sleep(2)
                await bot.send_message(chat_id=call.message.chat.id,
                                       text='Супер! А теперь напиши сколько тебе полных лет: ')
                await state.set_state(Form.age)
        else:
            await state.set_state(Form.name)
            await bot.send_message(chat_id=call.message.chat.id, text="Напишите как в вам можно обращаться?")

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        await call.message.answer("Произошла ошибка. Попробуйте снова.")


@application_form_router.message(F.text, Form.name)
async def capture_name(message: Message, state: FSMContext):
    try:

        await state.update_data(name=message.text)
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            await asyncio.sleep(2)
            await message.answer('Супер! А теперь напиши сколько тебе полных лет: ')
        await state.set_state(Form.age)
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /application для пользователя {message.from_user.id}: {e}")
        await message.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже.")


@application_form_router.message(F.text, Form.age)
async def capture_age(message: Message, state: FSMContext):
    check_age = extract_number(message.text)

    if not check_age or not (1 <= check_age <= 100):
        await message.reply('Пожалуйста, введите корректный возраст (число от 1 до 100).')
        return
    await state.update_data(age=check_age)

    await message.answer("Теперь сформулируйте фаш вопрос для заявки?")
    await state.set_state(Form.text_application)


@application_form_router.message(F.text, Form.text_application)
async def capture_check(message: Message, state: FSMContext):
    await state.update_data(text_application=message.text)
    data = await state.get_data()

    caption = f'Пожалуйста, проверьте все ли верно: \n\n' \
              f'<b>Полное имя</b>: {data.get("name")}\n' \
              f'<b>Возраст</b>: {data.get("age")} лет\n' \
              f'<b>Текст обращения</b>: {data.get("text_application")}\n'

    await message.answer(text=caption, reply_markup=approve_keyboard())
    await state.set_state(Form.check_state)
    #


@application_form_router.callback_query(F.data.startswith('approve_'), Form.check_state)
async def capture_approve(call: CallbackQuery, state: FSMContext):
    try:
        await call.answer(text="Проверяю ввод", show_alert=False)
        approve_inf = call.data.replace('approve_', '')
        if approve_inf == "True":
            async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
                await asyncio.sleep(2)
                await bot.send_message(chat_id=call.message.chat.id,
                                       text='Супер!')
                await state.clear()
        else:
            await state.clear()
            await bot.send_message(chat_id=call.message.chat.id, text="Давайте начнем сначала", reply_markup=main_kb())
    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        await call.message.answer("Произошла ошибка. Попробуйте снова.")
