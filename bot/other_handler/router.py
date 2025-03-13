import asyncio

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


@other_router.message(F.text, OtherHandler.other_question)
@connection()
async def other_question_message(message: Message, session, state: FSMContext, **kwargs) -> None:
    """

    """
    try:
        user_id: int = message.from_user.id

        # Проверяем, существует ли уже пользователь в базе данных
        user_info = await UserDAO.find_one_or_none(session=session,
                                                   filters=TelegramIDModel(telegram_id=user_id))
        application_model = Application(user_id=user_info.id, text_application=message.text)
        application: Application = await ApplicationDAO.add(session=session, values=application_model.to_dict())
        logger.debug(f"Создал заявку - {application.id}")
        # Подготовка текста для сообщения
        response_message: str = f"Спасибо! Ваша заявка № {application.id} успешно оформлена. \n\nСтатус заявки: 🟡 {application.status.value}\n\n"

        response_message += (f"Ваша вопрос:\n"
                             f"{application.text_application}")

        response_message += "\n\nПроверьте верно ли указаны все данные?"

        await message.answer(response_message, reply_markup=approve_keyboard("ДА", "НЕТ, начать сначала."))

        await state.set_state(OtherHandler.approve_form)

        logger.info(f"Заявка {application.id} успешно добавлена в базу данных.")

    except Exception as e:
        # Логируем ошибку, если она возникла
        logger.error(f"Ошибка при выполнении команды /start для пользователя {message.from_user.id}: {e}")
        await message.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже.")


@other_router.callback_query(F.data.startswith('approve_'), OtherHandler.approve_form)
@connection()
async def approve_form_callback(
        call: CallbackQuery,
        state: FSMContext,
        session
) -> None:
    """
    Обрабатывает callback-запрос пользователя, одобряющего форму заявки.
    В зависимости от решения пользователя, заявка будет либо одобрена, либо отклонена.

    Параметры:
        call (CallbackQuery): Объект callback-запроса от Telegram.
        state (FSMContext): Контекст состояния Finite State Machine (FSM) для текущего пользователя.
        session: Сессия базы данных для взаимодействия с DAO.

    Исключения:
        Обрабатываются все исключения с выводом ошибки в лог.
    """
    try:
        admin_message_ids = {}
        # Ответ на запрос для предотвращения уведомлений
        await call.answer(text="Проверяю ввод", show_alert=False)

        # Обработка данных callback-запроса
        approve_form_inf: bool = call.data.replace('approve_', '') == "True"

        # Удаляем клавиатуру из сообщения
        await call.message.edit_reply_markup(reply_markup=None)

        # Ищем пользователя и его последние заявки
        user_id = TelegramIDModel(telegram_id=call.from_user.id)
        user_applications = await UserDAO.find_one_or_none(session=session, filters=user_id)

        if not user_applications or not user_applications.applications:
            raise ValueError("Нет доступных заявок для пользователя.")

        last_appl: Application = user_applications.applications[-1]

        if approve_form_inf:
            # Если пользователь согласен с данными в форме
            await state.clear()  # Очищаем состояние FSM

            # Отправляем сообщение о том, что заявка принята
            async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
                await asyncio.sleep(2)  # Имитируем набор текста
                await bot.send_message(
                    chat_id=call.message.chat.id,
                    text='В ближайшее время с вами свяжется наш специалист для уточнения деталей.',
                    reply_markup=ReplyKeyboardRemove()
                )

            # Отправляем информацию о заявке администратору
            await bot.send_message(
                chat_id=settings.ADMIN_IDS[0],
                text=f'Была создана заявка {last_appl.id}, Это сообщение для админа',
                reply_markup=ReplyKeyboardRemove()
            )
            # Отправляем информацию о заявке администратору
            try:
                for admin_id in settings.ADMIN_IDS:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=f'Была создана заявка {last_appl.id}, Это сообщение для админа',
                        reply_markup=ReplyKeyboardRemove()
                    )
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение админу {admin_id} об остановке бота: {e}")
                pass

            response_message: str = (
                f"Заявка № {last_appl.id}\n\nСтатус заявки: 🟡 {last_appl.status.value}\n\n"
            )

            response_message += (f"Ваша вопрос:\n"
                                 f"{last_appl.text_application}")
            response_message += f"\n\n <b>{user_applications.phone_number}</b> \n\n"
            response_message += "\n\n Берете заявку в работу?"

            # Отправляем медиа группу (фото/видео) и информацию администратору

            # Отправляем информацию о заявке администратору
            try:
                for admin_id in settings.ADMIN_IDS:
                    message = await bot.send_message(chat_id=admin_id,
                                                     text=response_message,
                                                     reply_markup=approve_admin_keyboard("Берем", "Отказ",
                                                                                         call.from_user.id,
                                                                                         last_appl.id))
                    admin_message_ids[admin_id] = message.message_id  # Сохраняем message_id

                await ApplicationDAO.update(
                    session=session,
                    filters={"id": last_appl.id},
                    values={"admin_message_ids": admin_message_ids}
                )
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение админу {admin_id} об остановке бота: {e}")
                pass

        else:
            # Если пользователь не согласен с данными, удаляем заявку и отправляем сообщение
            await state.clear()
            await ApplicationDAO.delete(session=session, filters=last_appl.to_dict())
            await bot.send_message(
                chat_id=call.message.chat.id,
                text="Необходимо начать сначала создавать заявку",
                reply_markup=main_kb()  # Возможно, кнопка для начала новой заявки
            )

    except Exception as e:
        # Логируем ошибку и отправляем пользователю сообщение о сбое
        logger.error(f"Ошибка при обработке запроса: {e}")
        await call.message.answer("Произошла ошибка. Попробуйте снова.")

# @user_router.message(lambda message: message.contact is not None)
# @connection()
# async def handle_contact(message: Message, state: FSMContext, session) -> None:
#     """
#     Обрабатывает получение номера телефона пользователя.
#
#     Args:
#         message (Message): Сообщение с контактной информацией.
#         state (FSMContext): Контекст состояния FSM.
#     """
#     contact = message.contact
#     user_id = message.from_user.id
#     phone_number = contact.phone_number
#     phone_number = normalize_phone_number(phone_number)
#
#     # Сохранение номера в БД
#     existing_user = await UserDAO.find_one_or_none(filters=TelegramIDModel(telegram_id=user_id), session=session)
#
#     if existing_user:
#         await UserDAO.update(filters=TelegramIDModel(telegram_id=user_id),
#                              values=UpdateNumberSchema(phone_number=phone_number), session=session)
#     else:
#         return
#
#         # Ответ пользователю
#
#     async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
#         await asyncio.sleep(2)
#         await message.answer(
#             f"Спасибо! Ваш номер {phone_number} сохранен. Мы свяжемся с вами при необходимости.",
#             reply_markup=ReplyKeyboardRemove()
#         )
#         msg4 = f"Вам уже исполнилось 🔞 18 лет? "
#         await message.answer(msg4, reply_markup=approve_keyboard("Да", "Нет"))
#         await state.set_state(CheckForm.age)


#
# @dp.message(lambda message: message.contact is None)  # Пользователь отправил текст вместо контакта
# async def handle_manual_phone(message: Message) -> None:
#     """
#     Обрабатывает случай, когда пользователь вводит номер вручную.
#
#     Args:
#         message (Message): Сообщение пользователя.
#     """
#     user_id = message.from_user.id
#     phone_number = message.text.strip()
#
#     # Проверяем номер на соответствие формату
#     if not PHONE_REGEX.match(phone_number):
#         await message.answer(
#             "Похоже, вы ввели неверный номер телефона. Пожалуйста, используйте формат +7XXXXXXXXXX или 8XXXXXXXXXX."
#         )
#         return
#
#     # Сохранение номера в БД
#     existing_user = await UserDAO.find_one_or_none(filters=TelegramIDModel(telegram_id=user_id))
#
#     if existing_user:
#         await UserDAO.update(filters={"telegram_id": user_id}, values={"phone_number": phone_number})
#     else:
#         return
#
#     # Ответ пользователю
#     await message.answer(
#         f"Спасибо! Ваш номер {phone_number} сохранен. Мы свяжемся с вами при необходимости.",
#         reply_markup=ReplyKeyboardRemove()
#     )

#
# @user_router.callback_query(F.data.startswith('approve_'), CheckForm.age)
# async def age_callback(call: CallbackQuery, state: FSMContext) -> None:
#     """
#     Обработчик callback-запросов для проверки возраста пользователя.
#
#     Этот обработчик вызывается, когда пользователь отвечает на вопрос о возрасте в анкете.
#     Если пользователь подтвердил, что ему исполнилось 18 лет, он переходит к следующему вопросу.
#     В противном случае, анкета обнуляется, и пользователю отправляется сообщение о том, что
#     он не может воспользоваться услугами.
#
#     Args:
#         call (CallbackQuery): Объект callback-запроса, который содержит данные о взаимодействии пользователя с клавиатурой.
#         state (FSMContext): Контекст машины состояний, в котором хранятся данные анкеты.
#
#     Returns:
#         None: Функция не возвращает значения, но отправляет сообщение пользователю.
#     """
#     try:
#         await call.answer(text="Проверяю ввод", show_alert=False)
#
#         approve_inf = call.data.replace('approve_', '')
#         approve_inf = True if approve_inf == "True" else False
#         await call.message.delete()
#         # # Удаляем клавиатуру и сообщение о возрасте
#         # await call.message.edit_text("Спасибо за ответ. Проверяю данные...")
#         # await call.message.edit_reply_markup(reply_markup=None)
#         if approve_inf:
#             await state.update_data(age=approve_inf)
#             async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
#                 await asyncio.sleep(2)
#                 await bot.send_message(chat_id=call.message.chat.id,
#                                        text='Вы являетесь налоговым резитентом Российской Федерации?🇷🇺',
#                                        reply_markup=approve_keyboard("Да", "Нет"))
#                 await state.set_state(CheckForm.resident)
#         else:
#             await state.clear()
#             await bot.send_message(chat_id=call.message.chat.id,
#                                    text="К сожалению мы не предоставляем услуги лицам младше 🔞 18 лет!")
#
#     except Exception as e:
#         # Логируем ошибку
#         logger.error(f"Ошибка при обработке запроса: {e}")
#         await call.message.answer("Произошла ошибка. Попробуйте снова.")
#
#
# @user_router.callback_query(F.data.startswith('approve_'), CheckForm.resident)
# async def resident_callback(call: CallbackQuery, state: FSMContext) -> None:
#     """
#     Обработчик callback-запросов для проверки налогового резидентства пользователя.
#
#     Этот обработчик вызывается, когда пользователь отвечает на вопрос о налоговом резидентстве в анкете.
#     Если пользователь является налоговым резидентом России, ему показывается основное меню,
#     иначе анкета обнуляется, и пользователю отправляется сообщение о том, что бот не работает с налоговыми резидентами других стран.
#
#     Args:
#         call (CallbackQuery): Объект callback-запроса, который содержит данные о взаимодействии пользователя с клавиатурой.
#         state (FSMContext): Контекст машины состояний, в котором хранятся данные анкеты.
#
#     Returns:
#         None: Функция не возвращает значения, но отправляет сообщение пользователю.
#     """
#     try:
#         await call.answer(text="Проверяю ввод", show_alert=False)
#         approve_inf = call.data.replace('approve_', '')
#         approve_inf = True if approve_inf == "True" else False
#         await call.message.delete()
#         if approve_inf:
#             await state.update_data(age=approve_inf)
#             async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
#                 await asyncio.sleep(2)
#                 await bot.send_message(chat_id=call.message.chat.id,
#                                        text='Отлично, выберите один из представленных вариантов 👇',
#                                        reply_markup=main_kb())
#                 await state.clear()
#         else:
#             await state.clear()
#             await bot.send_message(chat_id=call.message.chat.id,
#                                    text="К сожалению мы 🧑‍🎓 не работаем с налоговыми резидентами других стран.")
#
#     except Exception as e:
#         # Логируем ошибку
#         logger.error(f"Ошибка при обработке запроса: {e}")
#         await call.message.answer("Произошла ошибка. Попробуйте снова.")
#
#
# @user_router.message(F.text, CheckForm.age)
# @user_router.message(F.text, CheckForm.resident)
# async def mistakes_handler(message: Message, state: FSMContext) -> None:
#     """
#     Обработчик для случаев, когда пользователь отправляет текст вместо того, чтобы выбрать одну из кнопок.
#
#     Этот обработчик вызывается, когда пользователь вводит текст в состоянии анкеты, где ожидается выбор из клавиатуры.
#     Бот информирует пользователя о том, что нужно выбрать одну из кнопок.
#
#     Args:
#         message (Message): Сообщение от пользователя, содержащее его текст.
#         state (FSMContext): Контекст машины состояний, где хранятся данные анкеты.
#
#     Returns:
#         None: Функция не возвращает значений, но отправляет сообщение пользователю о том, что нужно выбрать кнопку.
#     """
#     try:
#         await message.answer("Необходимо нажать по кнопке 👆")
#
#     except Exception as e:
#         # Логируем ошибку
#         logger.error(f"Ошибка при обработке запроса: {e}")
#         await message.answer("Произошла ошибка. Попробуйте снова.")
