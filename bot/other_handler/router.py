import asyncio
from typing import Any

from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.utils.chat_action import ChatActionSender
from loguru import logger

import bot.application_form.dao
from bot.admins.keyboards.inline_kb import approve_admin_keyboard
from bot.application_form.dao import ApplicationDAO
from bot.application_form.models import Application
from bot.application_form.utils import handle_contact
from bot.config import bot, settings
from bot.database import connection
from bot.users.dao import UserDAO
from bot.users.keyboards.inline_kb import approve_keyboard
from bot.users.keyboards.markup_kb import main_kb
from bot.users.schemas import TelegramIDModel
from bot.users.utils import age_callback, mistakes_handler, resident_callback

other_router = Router()


class OtherHandler(StatesGroup):
    other_question = State()
    approve_form = State()
    age = State()
    resident = State()
    phone_number = State()


@other_router.message(Command("question"))
@other_router.message(F.text.contains("Свой вопрос?"))
async def other_start(message: Message, state: FSMContext, **kwargs: Any) -> None:
    """
    НАчало ообработки обработчика отвечающий за нестандартн ворпос от пользователя
    """
    try:
        # Очищаем состояние пользователя
        await state.clear()
        msg4 = "Вам и/или вашему клиенту  уже исполнилось 🔞 18 лет? "
        await message.answer(
            text="Отлично! Вы хотите задать свой вопрос.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await asyncio.sleep(0.5)
        await message.answer(text=msg4, reply_markup=approve_keyboard("Да", "Нет"))
        await state.set_state(OtherHandler.age)

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при выполнении команды /question: {e}")
        await message.answer(
            "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже."
        )


@other_router.callback_query(F.data.startswith("approve_"), OtherHandler.age)
async def age_callback_other(call: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик callback-запросов, которые начинаются с "approve_" и связаны с полем возраста в форме.

    Этот обработчик активируется, когда пользователь отправляет callback-запрос с данными, которые начинаются с "approve_"
    и соответствуют полю `age` формы в классе `OtherHandler`. Он передает данные в функцию `age_callback`
    для дальнейшей обработки.

    Параметры:
    ----------
    call : CallbackQuery
        Объект callback-запроса от пользователя. Содержит информацию о запросе, включая
        данные, отправленные пользователем, и информацию о контексте кнопки.

    state : FSMContext
        Контекст состояния машины состояний (FSM) для отслеживания данных состояния пользователя.
        Используется для хранения промежуточных данных в процессе ввода формы.

    Возвращаемое значение:
    ----------------------
    None
        Функция не возвращает значение, так как она выполняет побочные эффекты — обработку
        и корректировку состояния бота в ответ на callback-запрос пользователя.

    Логика:
    -------
    - Этот обработчик активируется при callback-запросах, которые начинаются с "approve_" и соответствуют полю `age`.
    - Обработчик передает callback-запрос и контекст состояния в функцию `age_callback`, которая, вероятно, выполняет
      дальнейшую обработку данных возраста пользователя.
    """
    await age_callback(call, state, OtherHandler.resident, bot)


@other_router.callback_query(F.data.startswith("approve_"), OtherHandler.resident)
@connection()
async def resident_callback_other(
    call: CallbackQuery, state: FSMContext, session
) -> None:
    """
    Обработчик callback-запросов, которые начинаются с "approve_" и связаны с полем места жительства в форме.

    Этот обработчик активируется, когда пользователь отправляет callback-запрос с данными, которые начинаются с "approve_"
    и соответствуют полю `resident` формы в классе `OtherHandler`. Он передает данные в функцию `resident_callback`
    для дальнейшей обработки.

    Параметры:
    ----------
    call : CallbackQuery
        Объект callback-запроса от пользователя. Содержит информацию о запросе, включая
        данные, отправленные пользователем, и информацию о контексте кнопки.

    state : FSMContext
        Контекст состояния машины состояний (FSM) для отслеживания данных состояния пользователя.
        Используется для хранения промежуточных данных в процессе ввода формы.

    Возвращаемое значение:
    ----------------------
    None
        Функция не возвращает значение, так как она выполняет побочные эффекты — обработку
        и корректировку состояния бота в ответ на callback-запрос пользователя.

    Логика:
    -------
    - Этот обработчик активируется при callback-запросах, которые начинаются с "approve_" и соответствуют полю `resident`.
    - Обработчик передает callback-запрос и контекст состояния в функцию `resident_callback`, которая, вероятно, выполняет
      дальнейшую обработку данных места жительства пользователя.
    """

    await resident_callback(
        call,
        state,
        [OtherHandler.other_question, OtherHandler.phone_number],
        bot,
        answer="Введите текст вашего вопроса: 👇",
        session=session,
    )


@other_router.message(
    lambda message: message.contact is not None or message.text is not None,
    OtherHandler.phone_number,
)
@connection()
async def get_contact_phone_number(message: Message, state: FSMContext, session):
    await handle_contact(
        message=message,
        state=state,
        session=session,
        fsm=OtherHandler.other_question,
        answer="Введите ниже ваш вопрос 👇",
    )


@other_router.message(F.text, OtherHandler.other_question)
@connection()
async def other_question_message(
    message: Message, session, state: FSMContext, **kwargs
) -> None:
    """
    Обработчик для получения текстового сообщения от пользователя, оформления заявки и отправки подтверждения.

    Этот обработчик извлекает текст заявки, создает новую запись в базе данных,
    а затем отправляет пользователю сообщение с подтверждением оформления заявки.
    В процессе работы с базой данных показывается индикатор набора текста.

    Args:
        message (Message): Сообщение от пользователя, содержащее текст заявки.
        session: Сессия для работы с базой данных.
        state (FSMContext): Контекст состояния машины состояний для пользователя.
        **kwargs: Дополнительные аргументы, передаваемые через декоратор.

    Returns:
        None: Функция не возвращает значений, но отправляет сообщение пользователю с подтверждением заявки.

    Raises:
        Exception: В случае ошибки при работе с базой данных или отправке сообщения.
    """
    try:
        user_id: int = message.from_user.id

        # Показываем индикатор набора текста
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            # await asyncio.sleep(2)  # Симуляция времени для обработки данных

            # Проверяем, существует ли уже пользователь в базе данных
            user_info = await UserDAO.find_one_or_none(
                session=session, filters=TelegramIDModel(telegram_id=user_id)
            )

            if user_info is None:
                raise ValueError("Пользователь не найден в базе данных.")

            # Создаем заявку
            application_model = Application(
                user_id=user_info.id, text_application=message.text
            )
            application: Application = await ApplicationDAO.add(
                session=session, values=application_model.to_dict()
            )

            logger.debug(f"Создана заявка - {application.id}")

            # Подготовка текста для сообщения
            response_message: str = f"Спасибо! Ваша заявка № {application.id} успешно оформлена. \n\nСтатус заявки: 🟡 {application.status.value}\n\n"
            response_message += f"Ваш вопрос:\n{application.text_application}"

            response_message += "\n\nПроверьте верно ли указаны все данные?"

            # Отправляем сообщение с подтверждением
            await message.answer(
                response_message,
                reply_markup=approve_keyboard("ДА", "НЕТ, начать сначала."),
            )

            # Устанавливаем состояние для следующего шага
            await state.set_state(OtherHandler.approve_form)

            logger.info(f"Заявка {application.id} успешно добавлена в базу данных.")

    except Exception as e:
        # Логируем ошибку
        logger.error(
            f"Ошибка при обработке заявки для пользователя {message.from_user.id} ("
            f"Создание заявки по своему вопросу другому): {e}"
        )
        await message.answer(
            "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже."
        )


# Обработчик для одобрения или отклонения заявки
@other_router.callback_query(F.data.startswith("approve_"), OtherHandler.approve_form)
@connection()
async def approve_form_callback(
    call: CallbackQuery, state: FSMContext, session
) -> None:
    """
    Обрабатывает callback-запрос пользователя, одобряющего форму заявки.
    В зависимости от решения пользователя, заявка будет либо одобрена, либо отклонена.

    В процессе работы с базой данных показывается индикатор набора текста.

    Args:
        call (CallbackQuery): Коллбек-запрос от пользователя.
        state (FSMContext): Контекст состояния Finite State Machine (FSM) для текущего пользователя.
        session: Сессия базы данных для взаимодействия с DAO.

    Returns:
        None: Функция не возвращает значений, но изменяет состояние машины и отправляет сообщения.

    Raises:
        Exception: В случае ошибки при обработке данных или отправке сообщений.
    """
    try:
        admin_message_ids = {}

        # Ответ на запрос для предотвращения уведомлений
        await call.answer(text="Проверяю ввод", show_alert=False)

        # Получаем ответ на запрос для одобрения или отклонения формы
        approve_form_inf: str = call.data.replace("approve_", "")
        approve_form_inf = True if approve_form_inf == "True" else False
        # Удаляем клавиатуру из сообщения
        await call.message.edit_reply_markup(reply_markup=None)

        # Ищем пользователя и его заявки
        user_id = TelegramIDModel(telegram_id=call.from_user.id)
        user_applications = await UserDAO.find_one_or_none(
            session=session, filters=user_id
        )
        if not user_applications or not user_applications.applications:
            raise ValueError("Нет доступных заявок для пользователя.")

        last_appl: Application = user_applications.applications[-1]

        if approve_form_inf:
            # Если пользователь согласен с данными в заявке, очищаем состояние и отправляем сообщение
            await state.clear()

            # Имитируем набор текста перед отправкой сообщения пользователю
            async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
                await bot.send_message(
                    chat_id=call.message.chat.id,
                    text="В ближайшее время с вами свяжется наш специалист для уточнения деталей.",
                    reply_markup=ReplyKeyboardRemove(),
                )

            # Отправляем информацию о заявке администратору
            try:
                for admin_id in settings.ADMIN_IDS:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=f"Была создана заявка {last_appl.id}. Пожалуйста, рассмотрите заявку.",
                        reply_markup=ReplyKeyboardRemove(),
                    )
            except Exception as e:
                logger.error(
                    f"Не удалось отправить сообщение админу {admin_id} о создании заявки ботом администратору: {e}"
                )
                pass

            # Подготовка сообщения для пользователя с деталями заявки
            response_message: str = f"Заявка № {last_appl.id}\n\nСтатус заявки: 🟡 {last_appl.status.value}\n\n"

            response_message += f"Ваш вопрос:\n{last_appl.text_application}"
            response_message += f"\n\n <b>{user_applications.phone_number}</b> \n\n"
            response_message += "\n\n Берете заявку в работу?"

            # Отправка сообщения администраторам
            try:
                for admin_id in settings.ADMIN_IDS:
                    message = await bot.send_message(
                        chat_id=admin_id,
                        text=response_message,
                        reply_markup=approve_admin_keyboard(
                            "Берем", "Отказ", call.from_user.id, last_appl.id
                        ),
                    )
                    admin_message_ids[admin_id] = (
                        message.message_id
                    )  # Сохраняем message_id

                # Обновляем заявку с id сообщений для администраторов
                await ApplicationDAO.update(
                    session=session,
                    filters={"id": last_appl.id},
                    values={"admin_message_ids": admin_message_ids},
                )

            except Exception as e:
                logger.error(
                    f"Не удалось отправить сообщение админу {admin_id} об остановке бота: {e}"
                )
                pass

        else:
            # Если пользователь не согласен с данными, удаляем заявку и отправляем сообщение
            await state.clear()
            await ApplicationDAO.delete(session=session, filters={"id": last_appl.id})
            await bot.send_message(
                chat_id=call.message.chat.id,
                text="Необходимо начать сначала создавать заявку",
                reply_markup=main_kb(),  # Возможно, кнопка для начала новой заявки
            )

    except Exception as e:
        # Логируем ошибку и отправляем пользователю сообщение о сбое
        logger.error(f"Ошибка при обработке запроса по созданию кастомного вороса: {e}")
        await call.message.answer("Произошла ошибка. Попробуйте снова.")


@other_router.message(F.text, OtherHandler.age)
@other_router.message(F.text, OtherHandler.resident)
async def mistakes_handler_faq(message: Message, state: FSMContext) -> None:
    await mistakes_handler(
        message=message,
        bot=bot,
        state=state,
    )
