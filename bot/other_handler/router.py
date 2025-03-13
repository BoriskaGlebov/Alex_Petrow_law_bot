from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.chat_action import ChatActionSender
from loguru import logger
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.dispatcher.router import Router

import bot.application_form.dao
from bot.admins.keyboards.inline_kb import approve_admin_keyboard
from bot.application_form.models import Application
from bot.config import bot, settings
from bot.database import connection
from bot.users.dao import UserDAO
from bot.users.keyboards.inline_kb import approve_keyboard
from bot.users.keyboards.markup_kb import main_kb
from bot.users.schemas import TelegramIDModel
from bot.application_form.dao import ApplicationDAO

other_router = Router()


class OtherHandler(StatesGroup):
    other_question = State()
    approve_form = State()


# Обработчик для обработки сообщения с заявкой пользователя
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
            f"Ошибка при обработке заявки для пользователя {message.from_user.id}: {e}"
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
        approve_form_inf: bool = call.data.replace("approve_", "") == "True"

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
                    f"Не удалось отправить сообщение админу {admin_id} об остановке бота: {e}"
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
            await ApplicationDAO.delete(session=session, filters=last_appl.to_dict())
            await bot.send_message(
                chat_id=call.message.chat.id,
                text="Необходимо начать сначала создавать заявку",
                reply_markup=main_kb(),  # Возможно, кнопка для начала новой заявки
            )

    except Exception as e:
        # Логируем ошибку и отправляем пользователю сообщение о сбое
        logger.error(f"Ошибка при обработке запроса: {e}")
        await call.message.answer("Произошла ошибка. Попробуйте снова.")
