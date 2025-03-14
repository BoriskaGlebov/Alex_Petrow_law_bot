import asyncio
import re
from typing import List, Optional

from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InputMedia,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
    ReplyKeyboardRemove,
)
from aiogram.utils.chat_action import ChatActionSender
from loguru import logger

from bot.admins.keyboards.inline_kb import approve_admin_keyboard
from bot.application_form.dao import ApplicationDAO, BankDebtDAO, PhotoDAO, VideoDAO
from bot.application_form.keyboards.inline_kb import owner_keyboard, can_contact_keyboard
from bot.application_form.models import Application, ApplicationStatus
from bot.application_form.schemas import (
    BankDebtModelSchema,
    PhotoModelSchema,
    VideoModelSchema,
)
from bot.config import bot, settings
from bot.database import connection
from bot.other_handler.router import OtherHandler
from bot.users.dao import UserDAO
from bot.users.keyboards.inline_kb import approve_keyboard
from bot.users.keyboards.markup_kb import main_kb, phone_kb
from bot.users.schemas import TelegramIDModel, UpdateNumberSchema
from bot.users.utils import normalize_phone_number

application_form_router = Router()


class ApplicationForm(StatesGroup):
    approve_work = State()
    owner = State()
    photo = State()
    question_asked = State()  # Проверка на то нужно ли задавать вопрос по досылке фото
    can_contact = State()
    text_application = State()  # ТЕкст для заявки не из этого списка
    check_state = State()
    bank_name = State()
    total_amount = State()
    new_bank = State()
    video = State()
    approve_form = State()


# @application_form_router.message(Command('application_form'))
@application_form_router.message(F.text.contains("Вывод заблокированных средств"))
@connection()
async def application_form_start(
        message: Message, state: FSMContext, session, **kwargs
) -> None:
    """
    Обработчик команды, запускающий процесс подачи заявки на вывод заблокированных средств.
    Отправляет пользователю сообщение с предложением оставить заявку и ожидает ответа.

    Args:
        message (Message): Сообщение от пользователя, которое содержит текст "Вывод заблокированных средств".
        state (FSMContext): Контекст состояния машины состояний, используется для сохранения и изменения состояния пользователя.
        **kwargs: Дополнительные аргументы, которые могут быть переданы через декоратор.

    Returns:
        None: Функция не возвращает значения, но отправляет сообщения пользователю.

    Raises:
        Exception: Если при выполнении команды возникает ошибка, она будет зафиксирована в логе и отправлено сообщение о проблемах.
    """
    try:
        # Имитируем набор текста, пока выполняется вся логика
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            # Ищем пользователя в базе данных по ID
            user_inf = await UserDAO.find_one_or_none(
                session=session,
                filters=TelegramIDModel(telegram_id=message.from_user.id),
            )

            if user_inf and user_inf.phone_number:
                # Если номер телефона уже сохранен, отправляем предложение о заявке
                await message.answer(
                    "Вы хотите оставить 📝 заявку на вывод заблокированных средств?",
                    reply_markup=approve_keyboard(
                        "Да", "Нет"
                    ),  # Предлагаем клавиатуру с вариантами
                )
                # Устанавливаем состояние для машины состояний
                await state.set_state(ApplicationForm.approve_work)
            else:
                # Если номера телефона нет, просим пользователя его ввести
                await message.answer(
                    "Прежде чем мы начнем, необходимо оставить номер "
                    "телефона для оформления заявки и обратной связи.\n"
                    "Нажмите кнопку ниже или введите номер телефона вручную:\n"
                    " - +7XXXXXXXXXX\n"
                    " - 8XXXXXXXXXX ",
                    reply_markup=phone_kb(),  # Предлагаем клавиатуру с вариантами
                )
    except Exception as e:
        # Логируем ошибку, если она возникла
        logger.error(
            f"Ошибка при выполнении команды /application для пользователя {message.from_user.id}: {e}"
        )
        # Отправка сообщения об ошибке
        await message.answer(
            "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже."
        )


@application_form_router.callback_query(
    F.data.startswith("approve_"), ApplicationForm.approve_work
)
async def approve_work_callback(call: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик callback-запроса для подтверждения начала работы над заявкой на вывод заблокированных средств.
    После подтверждения пользователем, отправляется ряд сообщений с инструкциями и запросом на информацию о выводе средств.

    Args:
        call (CallbackQuery): Объект callback-запроса, содержащий данные о взаимодействии пользователя с кнопкой.
        state (FSMContext): Контекст состояния машины состояний, используется для сохранения данных пользователя в процессе взаимодействия.

    Returns:
        None: Функция не возвращает значения, но отправляет несколько сообщений в чат с пользователем, а также изменяет состояние.

    Raises:
        Exception: В случае возникновения ошибки при обработке запроса, ошибка логируется и пользователю отправляется сообщение об ошибке.
    """
    try:
        # Ответ на callback запрос
        await call.answer(text="Проверяю ввод", show_alert=False)
        await call.message.delete()
        # Обработка данных из callback_data
        approve_inf = call.data.replace("approve_", "")
        approve_inf = True if approve_inf == "True" else False
        async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
            if approve_inf:
                # Обновление данных в состоянии
                await state.update_data(approve_work=approve_inf)
                # Отправка серии сообщений с информацией
                await asyncio.sleep(1)
                await bot.send_message(
                    chat_id=call.message.chat.id,
                    text="Мы заполняем заявку на списание заблокированных средств одного должника.",
                    reply_markup=ReplyKeyboardRemove(),
                )
                await asyncio.sleep(1)
                await bot.send_message(
                    chat_id=call.message.chat.id,
                    text="❗️❗️❗️ Если у вас несколько должников, на каждого из них заполняется отдельная анкета.",
                )
                await asyncio.sleep(1)
                await bot.send_message(
                    chat_id=call.message.chat.id,
                    text="Не имеет значения, в каком количестве 🏦 банков и счетов заблокированы средства.",
                )
                await asyncio.sleep(1)
                await bot.send_message(
                    chat_id=call.message.chat.id,
                    text="В анкете необходимо будет указать, какие суммы в каких банках заблокированы.",
                )
                await asyncio.sleep(1)
                await bot.send_message(
                    chat_id=call.message.chat.id,
                    text="Вы хотите вывести средства с собственного счета или счета вашего клиента?",
                    reply_markup=owner_keyboard(),
                )
                # Устанавливаем следующее состояние для обработки данных
                await state.set_state(ApplicationForm.owner)
            else:
                # Если пользователь не подтвердил, предлагаем текстовую заявку
                await state.set_state(OtherHandler.other_question)
                await bot.send_message(
                    chat_id=call.message.chat.id,
                    text="Чем бы мы могли вам в таком случае помочь?",
                )
                # TODO Тут можно зарегистрировать заявку на другую услугу, если необходимо
                # TODO Не забыть добавить работу с БД

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        # Отправляем пользователю сообщение об ошибке
        await call.message.answer("Произошла ошибка. Попробуйте снова.")


@application_form_router.callback_query(
    F.data.startswith("owner_"), ApplicationForm.owner
)
async def owner_callback(call: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик callback-запроса для подтверждения, с какого счета будут выводиться средства (собственного или клиента).
    После подтверждения пользователем, отправляется сообщение с инструкциями по приложению фото паспорта.

    Args:
        call (CallbackQuery): Объект callback-запроса, содержащий данные о взаимодействии пользователя с кнопкой.
        state (FSMContext): Контекст состояния машины состояний, используется для сохранения данных пользователя в процессе взаимодействия.

    Returns:
        None: Функция не возвращает значений, но отправляет сообщения в чат с пользователем и обновляет состояние в машине состояний.

    Raises:
        Exception: В случае возникновения ошибки при обработке запроса, ошибка логируется и пользователю отправляется сообщение об ошибке.
    """
    try:
        async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
            # Ответ на callback запрос
            await call.answer(text="Проверяю ввод", show_alert=False)
            await call.message.delete()

            # Обработка данных из callback_data
            owner_inf = call.data.replace("owner_", "")
            owner_inf = True if owner_inf == "True" else False

            # Обновление данных в контексте состояния
            await state.update_data(owner=owner_inf)

            # Список сообщений для отправки в чат с пользователем
            if owner_inf:
                messages = [
                    "Приложите фото 2-3 страниц паспорта и фото 📸 страницы с адресом регистрации."
                ]
                # Переход к следующему состоянию для загрузки фото
                await state.set_state(ApplicationForm.photo)
            else:
                messages = [
                    "У вас есть возможность связаться 📬 с вашим клиентом?",
                ]
                # Переход к следующему состоянию для загрузки фото
                await state.set_state(ApplicationForm.can_contact)

            # Отправка сообщений с имитацией набора текста

            for message in messages:
                await asyncio.sleep(1)  # Имитация времени на ввод каждого сообщения
                if owner_inf:
                    await bot.send_message(chat_id=call.message.chat.id, text=message)
                else:
                    await bot.send_message(
                        chat_id=call.message.chat.id,
                        text=message,
                        reply_markup=can_contact_keyboard(),
                    )

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        # Отправляем пользователю сообщение об ошибке
        await call.message.answer("Произошла ошибка. Попробуйте снова.")


@application_form_router.callback_query(
    F.data.startswith("can_contact_"), ApplicationForm.can_contact
)
async def can_contact_callback(call: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик callback-запроса для подтверждения возможности связаться с клиентом.
    После подтверждения пользователем, отправляется соответствующее сообщение с инструкциями по приложению фото паспорта или видео согласия.

    Args:
        call (CallbackQuery): Объект callback-запроса, содержащий данные о взаимодействии пользователя с кнопкой.
        state (FSMContext): Контекст состояния машины состояний, используется для сохранения данных пользователя в процессе взаимодействия.

    Returns:
        None: Функция не возвращает значений, но отправляет сообщения в чат с пользователем и обновляет состояние в машине состояний.

    Raises:
        Exception: В случае возникновения ошибки при обработке запроса, ошибка логируется и пользователю отправляется сообщение об ошибке.
    """
    try:
        # Ответ на callback запрос
        await call.answer(text="Проверяю ввод", show_alert=False)
        await call.message.delete()

        # Обработка данных из callback_data
        can_contact_inf = call.data.replace("can_contact_", "")
        can_contact_inf = True if can_contact_inf == "True" else False
        logger.error(can_contact_inf)
        # Обновление данных в контексте состояния
        await state.update_data(can_contact=can_contact_inf)
        async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
            # Список сообщений для отправки в чат с пользователем
            if can_contact_inf or not can_contact_inf:
                messages = [
                    "Приложите фото 2-3 страниц паспорта и фото 📸 страницы с адресом регистрации."
                ]
                # Переход к следующему состоянию для загрузки фото
                await state.set_state(ApplicationForm.photo)
            # else:
            #     messages = [
            #         "Как только у вас появится возможность связаться с пользователем, приходите снова."
            #     ]
            #     # Убираем клавиатуру
            #     await call.message.answer(
            #         text="До свидания!", reply_markup=ReplyKeyboardRemove()
            #     )
            #     # Очищаем состояние
            #     await state.clear()
            #
            for message in messages:
                # await asyncio.sleep(1)  # Имитация времени на ввод каждого сообщения
                await bot.send_message(chat_id=call.message.chat.id, text=message)

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        # Отправляем пользователю сообщение об ошибке
        await call.message.answer("Произошла ошибка. Попробуйте снова.")


# 🔒 Словарь локальных блокировок (по user_id)
user_locks = {}


@application_form_router.message(ApplicationForm.photo, F.photo)
async def photo_message(message: Message, state: FSMContext):
    """
    Обработчик для обработки фотографий, отправленных пользователем в чат. Если пользователь отправляет фото,
    оно сохраняется в состоянии FSM, и если оно еще не было отправлено, то добавляется в список. Для предотвращения
    гонки состояний используется локальная блокировка.

    Аргументы:
    - message (Message): Объект сообщения от пользователя, содержащий фотографию.
    - state (FSMContext): Контекст состояния, используемый для сохранения данных о фотографиях.

    Типы данных:
    - message: Объект типа `aiogram.types.Message`, который содержит информацию о сообщении, включая отправленные файлы.
    - state: Контекст состояний FSM (`FSMContext`), используемый для работы с данными в процессе общения с пользователем.

    Возвращаемое значение:
    - Ответ пользователю о добавлении фото в FSM.
    """
    user_id = message.from_user.id  # Получаем user_id

    # Создаем локальную блокировку для каждого пользователя, если её ещё нет
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()

    async with user_locks[user_id]:  # 🔒 Блокируем только для этого пользователя
        try:
            await asyncio.sleep(0.5)  # ⏳ Ожидание загрузки фото

            # Берем самое большое фото из отправленных
            new_photo = message.photo[-1].file_id  # 📸 Берем самое большое фото
            logger.debug(f"Извлек ID фотографии - {new_photo}")

            # Получаем данные о текущем состоянии (например, фото, которые уже были отправлены)
            state_data = await state.get_data()
            existing_photos = state_data.get("photos", [])

            # Если фото еще не было добавлено, добавляем его в список
            if new_photo not in existing_photos:
                existing_photos.append(new_photo)
            else:
                logger.warning("Попытка добавить одинаковое фото")

            # Обновляем данные в FSM
            await state.update_data(photos=existing_photos)
            logger.debug(f"Добавил данные в FSM {(await state.get_data())['photos']}")

            # Проверяем, был ли уже задан вопрос о дальнейшем отправлении фото
            question_asked = state_data.get("question_asked", False)
            if not question_asked:
                await state.update_data(question_asked=True)
                await message.answer(
                    "Еще фото будете отправлять?",
                    reply_markup=approve_keyboard("Да", "Нет"),
                )

        except Exception as e:
            logger.error(f"Ошибка при обработке фото: {e}")
            await message.answer(
                "Произошла ошибка при обработке вашего фото. Попробуйте снова."
            )
        finally:
            # Удаляем блокировку для этого пользователя после выполнения кода
            if user_id in user_locks:
                del user_locks[user_id]  # Удаляем блокировку из словаря


# Обработчик для несжатых фото (если отправляются как документы)
@application_form_router.message(
    F.document.mime_type.startswith("image/"), ApplicationForm.photo
)
@application_form_router.message(
    F.document.mime_type.startswith("image/webp"), ApplicationForm.photo
)
# TODO некорректно сохраняет если фотка несжатая и отправлятся в формате webp
async def photo_uncompressed_message(message: Message, state: FSMContext):
    """
    Обработчик для обработки несжатых фото, отправленных пользователем как документы (включая формат WebP).
    Фото сохраняется в состояние FSM, если оно еще не было добавлено.

    Аргументы:
    - message (Message): Объект сообщения, содержащий документ с изображением.
    - state (FSMContext): Контекст состояния, используемый для сохранения данных о фотографиях.

    Типы данных:
    - message: Объект типа `aiogram.types.Message`, который содержит информацию о сообщении, включая отправленные файлы.
    - state: Контекст состояний FSM (`FSMContext`), используемый для работы с данными в процессе общения с пользователем.

    Возвращаемое значение:
    - Ответ пользователю о добавлении фото в FSM или об ошибке обработки.
    """
    user_id = message.from_user.id  # Получаем user_id

    # Создаем локальную блокировку для каждого пользователя, если её ещё нет
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()

    async with user_locks[user_id]:  # 🔒 Блокируем только для этого пользователя
        try:
            await asyncio.sleep(0.5)  # ⏳ Ожидание загрузки фото

            # Получаем photo_id для несжатого изображения
            new_photo = message.document.file_id
            logger.debug(f"Извлек ID несжатого фото - {new_photo}")

            # Получаем текущее состояние FSM
            state_data = await state.get_data()
            existing_photos = state_data.get("photos", [])

            # Проверяем, не было ли уже такого фото
            if new_photo not in existing_photos:
                existing_photos.append(new_photo)
            else:
                logger.warning("Попытка добавить одинаковое несжатое фото")

            # Обновляем состояние с фотографиями
            await state.update_data(photos=existing_photos)

            # Проверяем, был ли уже задан вопрос
            question_asked = state_data.get("question_asked", False)
            if not question_asked:
                await state.update_data(question_asked=True)
                await message.answer(
                    "Еще фото будете отправлять?",
                    reply_markup=approve_keyboard("Да", "Нет"),
                )

        except Exception as e:
            logger.error(f"Ошибка при обработке несжатого фото: {e}")
            await message.answer(
                "Произошла ошибка при обработке вашего фото. Попробуйте снова."
            )
        finally:
            # Удаляем блокировку для этого пользователя после выполнения
            if user_id in user_locks:
                del user_locks[user_id]  # Удаляем блокировку из словаря


# Обработчик для случая, когда пользователь отправляет не фото (например, видео или документы)
@application_form_router.message(
    F.document | F.video | F.audio | F.voice, ApplicationForm.photo
)
async def photo_mistakes(message: Message, state: FSMContext):
    """
    Обработчик для сообщений с файлами, когда ожидаются фото. Если прислан не фото (например, видео или документ),
    пользователю отправляется ошибка с просьбой прислать изображение.

    Аргументы:
    - message (Message): Сообщение от пользователя.
    - state (FSMContext): Контекст состояния, используемый для хранения данных процесса.
    """
    try:
        # Логируем MIME тип файла
        mime_type = (
            message.document.mime_type
            if hasattr(message, "document")
            else "Не документ"
        )
        logger.debug(f"Получен файл с MIME типом: {mime_type}")

        # Проверка, что это не изображение
        if hasattr(message, "document"):  # Если это документ
            mime_type = message.document.mime_type
            if mime_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
                # Если это не изображение, отправляем ошибку
                await message.answer("Пожалуйста, отправьте фото, а не документ!")
                await state.set_state(ApplicationForm.photo)
            else:
                # Если это изображение, обрабатываем его как несжатое фото
                await photo_uncompressed_message(message, state)
        elif hasattr(message, "video"):  # Если это видео
            await message.answer("Пожалуйста, отправьте фото, а не видео!")
            await state.set_state(ApplicationForm.photo)
        elif hasattr(message, "audio"):  # Если это аудио
            await message.answer("Пожалуйста, отправьте фото, а не аудио!")
            await state.set_state(ApplicationForm.photo)
        elif hasattr(message, "voice"):  # Если это голосовое сообщение
            await message.answer(
                "Пожалуйста, отправьте фото, а не голосовое сообщение!"
            )
            await state.set_state(ApplicationForm.photo)

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке файла: {e}")
        await message.answer(
            "Произошла ошибка при обработке вашего файла. Попробуйте снова."
        )


@application_form_router.callback_query(
    F.data.startswith("approve_"), ApplicationForm.photo
)
async def photo_callback(call: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик callback-запросов от пользователя на вопрос о добавлении дополнительных фотографий.

    Этот обработчик срабатывает, когда пользователь отвечает на вопрос о добавлении еще фото (при помощи кнопок в inline клавиатуре).
    В зависимости от ответа (Да/Нет) происходит обновление состояния FSM и отправка соответствующего сообщения.

    Аргументы:
    - call (CallbackQuery): Объект callback-запроса от пользователя. Содержит информацию о нажатой кнопке.
    - state (FSMContext): Контекст состояния, используемый для сохранения данных между запросами.

    Типы данных:
    - call: Объект типа `aiogram.types.CallbackQuery`, который содержит информацию о callback-запросе, включая нажатую кнопку.
    - state: Контекст состояний FSM (`FSMContext`), используемый для работы с данными в процессе общения с пользователем.

    Возвращаемое значение:
    - Отправляет сообщение пользователю в зависимости от его выбора (добавить фото или перейти к следующему этапу).
    """
    try:
        # Отвечаем на callback-запрос, чтобы предотвратить отображение уведомления
        await call.answer(text="Проверяю ввод", show_alert=False)

        # Извлекаем и обрабатываем данные callback-запроса
        photo_inf = call.data.replace("approve_", "")
        photo_inf = True if photo_inf == "True" else False

        # Удаляем сообщение с вопросом
        await call.message.delete()
        async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
            if photo_inf:
                # Если пользователь хочет добавить еще фото
                await state.update_data(question_asked=False)
                await bot.send_message(
                    chat_id=call.message.chat.id, text="Добавьте еще фото 👇"
                )
            else:
                # Если пользователь не хочет добавлять фото, переходим к следующему этапу
                await state.set_state(ApplicationForm.bank_name)
                await bot.send_message(
                    chat_id=call.message.chat.id,
                    text="Укажите один банк 🏦, с которого необходимо произвести списание.",
                )

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        await call.message.answer("Произошла ошибка. Попробуйте снова.")


@application_form_router.message(F.text, ApplicationForm.bank_name)
async def bank_get_inf(message: Message, state: FSMContext):
    """
    Обработчик для получения информации о банке от пользователя.

    Этот обработчик срабатывает, когда пользователь вводит название банка. Название добавляется
    в список банков в состоянии FSM, а затем пользователь запрашивается о сумме, заблокированной
    в этом банке.

    Аргументы:
    - message (Message): Объект сообщения, который содержит текст, отправленный пользователем (в данном случае, название банка).
    - state (FSMContext): Контекст состояния, используемый для сохранения данных между запросами. В данном случае для обновления списка банков.

    Типы данных:
    - message: Объект типа `aiogram.types.Message`, который содержит данные о сообщении, отправленном пользователем, включая текст.
    - state: Контекст состояний FSM (`FSMContext`), который используется для работы с данными в процессе общения с пользователем.

    Возвращаемое значение:
    - Функция не возвращает значение, но отправляет сообщение с запросом общей суммы заблокированных средств.
    """
    try:
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            # Получаем данные состояния
            state_data = await state.get_data()

            # Извлекаем текущий список банков из состояния (если он есть)
            bank_list = state_data.get("bank_name", [])

            # Добавляем новое название банка в список
            bank_list.append(message.text)

            # Обновляем состояние с новым списком банков
            await state.update_data(bank_name=bank_list)

            # Запрашиваем общую сумму, заблокированную в этом банке
            await message.answer(
                "Укажите общую сумму, заблокированную в этом банке у данного лица."
            )

            # Переходим к следующему состоянию для получения суммы
            await state.set_state(ApplicationForm.total_amount)

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")


@application_form_router.message(F.text, ApplicationForm.total_amount)
async def total_amount_get_inf(message: Message, state: FSMContext):
    """
    Обработчик для получения общей заблокированной суммы в банке от пользователя.

    Этот обработчик срабатывает, когда пользователь вводит общую сумму заблокированных средств в банке.
    Сумма добавляется в список общих сумм в состоянии FSM, а затем пользователь запрашивается, имеются ли
    заблокированные средства в других банках.

    Аргументы:
    - message (Message): Объект сообщения, который содержит текст, отправленный пользователем (в данном случае, сумма).
    - state (FSMContext): Контекст состояния, используемый для сохранения данных между запросами. В данном случае для обновления списка заблокированных сумм.

    Типы данных:
    - message: Объект типа `aiogram.types.Message`, который содержит данные о сообщении, отправленном пользователем, включая текст (сумму).
    - state: Контекст состояний FSM (`FSMContext`), который используется для работы с данными в процессе общения с пользователем.

    Возвращаемое значение:
    - Функция не возвращает значение, но отправляет сообщение с запросом о заблокированных средствах в других банках.
    """
    try:
        # Получаем текст, отправленный пользователем
        user_input = message.text.strip()

        # Используем регулярное выражение для извлечения числа (с плавающей точкой или целого)
        match = re.search(
            r"[-+]?\d*\,?\d+", user_input.replace(" ", "")
        )  # Игнорируем пробелы
        async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
            if match:
                # Заменяем запятую на точку, чтобы корректно обработать числа с плавающей точкой
                user_input_number = match.group().replace(",", ".")

                try:
                    total_amount = float(user_input_number)

                    # Проверяем, что сумма больше нуля
                    if total_amount <= 0:
                        raise ValueError("Сумма должна быть больше нуля.")

                except ValueError:
                    await message.answer(
                        "Пожалуйста, введите корректную сумму (больше нуля), используя числа и точку или запятую для десятичных знаков."
                    )
                    return

                # Получаем данные состояния
                state_data = await state.get_data()

                # Извлекаем текущий список сумм из состояния (если он есть)
                total_amount_list = state_data.get("total_amount", [])

                # Добавляем новую сумму в список
                total_amount_list.append(total_amount)

                # Обновляем состояние с новым списком сумм
                await state.update_data(total_amount=total_amount_list)

                # Запрашиваем, имеются ли заблокированные средства в других банках
                await message.answer(
                    "Имеются ли у данного лица заблокированные средства, которые необходимо списать, в других банках?",
                    reply_markup=approve_keyboard("Да", "Нет"),
                )

                # Переходим к следующему состоянию для получения информации о новом банке
                await state.set_state(ApplicationForm.new_bank)
            else:
                await message.answer(
                    "Пожалуйста, введите сумму с числами. Например: '1000' или '1000.50'."
                )

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")


# TODO Слишком большая функция было бы не плохо оптимизировать
@application_form_router.callback_query(
    F.data.startswith("approve_"), ApplicationForm.new_bank
)
@connection()
async def photo_callback_final(call: CallbackQuery, state: FSMContext, session) -> None:
    """
    Обработчик callback-запросов для вопроса о добавлении фото и подтверждения банка.

    Этот обработчик срабатывает, когда пользователь выбирает один из вариантов ответа на запрос о добавлении фото или нового банка.
    В зависимости от ответа пользователя, происходит переход на следующую стадию процесса (или добавление нового банка).

    Аргументы:
    - call (CallbackQuery): Объект callback-запроса, содержащий данные, отправленные пользователем.
    - state (FSMContext): Контекст состояния, который используется для обновления данных и перехода в новое состояние.

    Типы данных:
    - call: Объект типа `aiogram.types.CallbackQuery`, содержащий информацию о callback-запросе, включая данные (которые указывают, хочет ли пользователь добавить новый банк).
    - state: Объект типа `FSMContext`, используемый для хранения данных и управления состоянием между запросами.

    Возвращаемое значение:
    - Функция не возвращает значения, но отправляет сообщения и изменяет состояние FSM.
    """
    try:
        # Отвечаем на callback-запрос, чтобы предотвратить отображение уведомления
        await call.answer(text="Проверяю ввод", show_alert=False)

        # Извлекаем и обрабатываем данные callback-запроса
        new_bank_inf = call.data.replace("approve_", "")
        new_bank_inf = True if new_bank_inf == "True" else False

        # Удаляем сообщение с вопросом
        await call.message.delete()
        async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
            if new_bank_inf:
                # Если пользователь хочет добавить еще банк, обновляем состояние и просим указать банк
                await state.update_data(new_bank=True)

                await asyncio.sleep(2)
                await bot.send_message(
                    chat_id=call.message.chat.id,
                    text="Укажите один банк 🏦, с которого необходимо произвести списание.",
                )
                await state.set_state(ApplicationForm.bank_name)
            else:
                # Если пользователь не хочет добавлять банк, переходим к запросу видео
                await state.update_data(new_bank=False)
                await state.update_data(check_state=ApplicationStatus.PENDING.value)

                # Получаем данные пользователя из FSM
                user_data = await state.get_data()  # Тип данных: dict
                user_id: int = call.from_user.id  # Тип данных: int

                # Проверяем, существует ли уже пользователь в базе данных
                user_info = await UserDAO.find_one_or_none(
                    session=session, filters=TelegramIDModel(telegram_id=user_id)
                )
                if not user_info:
                    logger.error(
                        f"Пользователь с telegram_id {user_id} не найден в базе данных."
                    )
                    await call.message.answer("Произошла ошибка. Попробуйте снова.")
                    return

                # Извлекаем данные из FSM состояния
                status: ApplicationStatus = ApplicationStatus(
                    user_data.get("check_state", "PENDING")
                )
                owner: Optional[bool] = user_data.get("owner", None)
                can_contact: Optional[bool] = user_data.get("can_contact", None)
                video_id: Optional[str] = user_data.get(
                    "video", None
                )  # Тип данных: Optional[str]
                bank_name: Optional[List[str]] = user_data.get(
                    "bank_name", None
                )  # Тип данных: Optional[List[str]]
                total_amount: Optional[List[float]] = user_data.get(
                    "total_amount", None
                )  # Тип данных: Optional[List[float]]
                photos: List[str] = user_data.get("photos", [])  # Тип данных: List[str]

                # Создаем заявку в БД
                application_model = Application(
                    user_id=user_info.id, status=status, owner=owner, can_contact=can_contact
                )
                application: Application = await ApplicationDAO.add(
                    session=session, values=application_model.to_dict()
                )
                logger.debug(f"Создал заявку - {application.id}")

                # Добавляем фотографии, если есть
                for photo_id in photos:
                    photo_model = PhotoModelSchema(
                        file_id=photo_id, application_id=application.id
                    )
                    await PhotoDAO.add(session, photo_model)

                # Добавляем видео в базу данных
                if video_id:
                    video_model = VideoModelSchema(
                        file_id=video_id, application_id=application.id
                    )
                    await VideoDAO.add(session, video_model)

                # Добавляем задолженности, если есть
                if bank_name and total_amount:
                    # Проверяем, что списки bank_name и total_amount имеют одинаковую длину
                    if len(bank_name) == len(total_amount):
                        for bank, amount in zip(bank_name, total_amount):
                            bank_debt_model = BankDebtModelSchema(
                                bank_name=bank,
                                total_amount=amount,
                                application_id=application.id,
                            )
                            await BankDebtDAO.add(session, bank_debt_model)

                # Подготовка текста для сообщения
                response_message: str = f"Спасибо! Ваша заявка № {application.id} успешно оформлена. \n\nСтатус заявки: 🟡 {application.status.value}\n\n"

                if application.owner is not None:
                    response_message += (
                        "Собственные счета - ДА\n\n"
                        if application.owner
                        else "Собственные счета - Нет\n\n"
                    )
                if (application.owner is not None) and application.owner is not True:
                    response_message += (
                        "Может связаться с собственником счета - ДА\n\n"
                        if application.can_contact
                        else "Может связаться с собственником счета - Нет\n\n"
                    )

                # Если есть задолженности по банкам, добавляем информацию о них
                if bank_name and total_amount:
                    response_message += "Задолженности по банкам:\n"
                    for bank, amount in zip(bank_name, total_amount):
                        response_message += f"🔸 Банк: <b>{bank}</b>, Сумма задолженности: <b>{amount}</b> руб.\n"

                response_message += "\n\nПроверьте верно ли указаны все данные?"

                # Формирование медиа-аттачментов
                media: List[InputMedia] = []  # Тип данных: List[InputMedia]

                # Прикрепляем фото
                for photo_id in photos:
                    media.append(InputMediaPhoto(type="photo", media=photo_id))

                # Прикрепляем видео
                if video_id:
                    media.append(InputMediaVideo(type="video", media=video_id))

                # Отправляем сообщение с фото, видео, задолженностями и банками
                await call.message.answer_media_group(media=media)
                await call.message.answer(
                    response_message,
                    reply_markup=approve_keyboard("ДА", "НЕТ, начать сначала."),
                )

                await state.set_state(ApplicationForm.approve_form)

                logger.info(f"Заявка {application.id} успешно добавлена в базу данных.")

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        await call.message.answer("Произошла ошибка. Попробуйте снова.")


# @application_form_router.message(ApplicationForm.video, F.video)
# @connection()
# async def video_message(message: types.Message, session: AsyncSession, state: FSMContext):
#     """
#     Обработчик для обработки видео, отправленного пользователем в чат.
#     Если пользователь отправляет видео, оно сохраняется в состоянии FSM и добавляется в базу данных.
#
#     Аргументы:
#     - message (types.Message): Объект сообщения от пользователя, содержащий видео.
#     - session (AsyncSession): Сессия для работы с базой данных.
#     - state (FSMContext): Контекст состояния, используемый для сохранения данных о видео.
#
#     Возвращаемое значение:
#     - Ответ пользователю о добавлении видео в FSM и создании заявки в базе данных.
#     """
#     try:
#         await asyncio.sleep(0.5)  # Ожидание загрузки видео
#
#         # Получаем ID видео
#         new_video: str = message.video.file_id  # Тип данных: str
#         logger.debug(f"Извлек ID видео - {new_video}")
#
#         # Обновляем данные в FSM
#         await state.update_data(video=new_video)
#         await state.update_data(check_state=ApplicationStatus.PENDING.value)
#
#         # Получаем данные пользователя из FSM
#         user_data = await state.get_data()  # Тип данных: dict
#         user_id: int = message.from_user.id  # Тип данных: int
#
#         # Проверяем, существует ли уже пользователь в базе данных
#         user_info = await UserDAO.find_one_or_none(session=session, filters=TelegramIDModel(telegram_id=user_id))
#         if not user_info:
#             logger.error(f"Пользователь с telegram_id {user_id} не найден в базе данных.")
#             await message.answer("Произошла ошибка. Попробуйте снова.")
#             return
#
#         # Извлекаем данные из FSM состояния
#         status: ApplicationStatus = ApplicationStatus(user_data.get("check_state", "PENDING"))
#         video_id: Optional[str] = user_data.get('video', None)  # Тип данных: Optional[str]
#         bank_name: Optional[List[str]] = user_data.get('bank_name', None)  # Тип данных: Optional[List[str]]
#         total_amount: Optional[List[float]] = user_data.get('total_amount', None)  # Тип данных: Optional[List[float]]
#         photos: List[str] = user_data.get('photos', [])  # Тип данных: List[str]
#
#         # Создаем заявку в БД
#         application_model = Application(user_id=user_info.id, status=status)
#         application: Application = await ApplicationDAO.add(session=session, values=application_model.to_dict())
#         logger.debug(f"Создал заявку - {application.id}")
#
#         # Добавляем фотографии, если есть
#         for photo_id in photos:
#             photo_model = PhotoModelSchema(file_id=photo_id, application_id=application.id)
#             await PhotoDAO.add(session, photo_model)
#
#         # Добавляем видео в базу данных
#         if video_id:
#             video_model = VideoModelSchema(file_id=video_id, application_id=application.id)
#             await VideoDAO.add(session, video_model)
#
#         # Добавляем задолженности, если есть
#         if bank_name and total_amount:
#             # Проверяем, что списки bank_name и total_amount имеют одинаковую длину
#             if len(bank_name) == len(total_amount):
#                 for bank, amount in zip(bank_name, total_amount):
#                     bank_debt_model = BankDebtModelSchema(
#                         bank_name=bank,
#                         total_amount=amount,
#                         application_id=application.id
#                     )
#                     await BankDebtDAO.add(session, bank_debt_model)
#
#         # Подготовка текста для сообщения
#         response_message: str = f"Спасибо! Ваша заявка № {application.id} успешно оформлена. \n\nСтатус заявки: 🟡 {application.status.value}\n\n"
#
#         # Если есть задолженности по банкам, добавляем информацию о них
#         if bank_name and total_amount:
#             response_message += "Задолженности по банкам:\n"
#             for bank, amount in zip(bank_name, total_amount):
#                 response_message += f"🔸 Банк: <b>{bank}</b>, Сумма задолженности: <b>{amount}</b> руб.\n"
#
#         response_message += "\n\nПроверьте верно ли указаны все данные?"
#
#         # Формирование медиа-аттачментов
#         media: List[InputMedia] = []  # Тип данных: List[InputMedia]
#
#         # Прикрепляем фото
#         for photo_id in photos:
#             media.append(InputMediaPhoto(type='photo', media=photo_id))
#
#         # Прикрепляем видео
#         if video_id:
#             media.append(InputMediaVideo(type='video', media=video_id))
#
#         # Отправляем сообщение с фото, видео, задолженностями и банками
#         await message.answer_media_group(media=media)
#         await message.answer(response_message, reply_markup=approve_keyboard("ДА", "НЕТ, начать сначала."))
#
#         await state.set_state(ApplicationForm.approve_form)
#
#         logger.info(f"Заявка {application.id} успешно добавлена в базу данных.")
#     except Exception as e:
#         logger.error(f"Ошибка при обработке видео: {e}")
#         await message.answer("Произошла ошибка при обработке вашего видео. Попробуйте снова.")


@application_form_router.callback_query(
    F.data.startswith("approve_"), ApplicationForm.approve_form
)
@connection()
async def approve_form_callback(
        call: CallbackQuery, state: FSMContext, session
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
        approve_form_inf: bool = call.data.replace("approve_", "") == "True"

        # Удаляем клавиатуру из сообщения
        await call.message.edit_reply_markup(reply_markup=None)

        # Ищем пользователя и его последние заявки
        user_id = TelegramIDModel(telegram_id=call.from_user.id)
        user_applications = await UserDAO.find_one_or_none(
            session=session, filters=user_id
        )
        for el in user_applications.applications:
            print(el)
        if not user_applications or not user_applications.applications:
            raise ValueError("Нет доступных заявок для пользователя.")

        last_appl: Application = user_applications.applications[-1]
        print(last_appl.id)
        if approve_form_inf:
            # Если пользователь согласен с данными в форме
            await state.clear()  # Очищаем состояние FSM

            # Отправляем сообщение о том, что заявка принята
            async with ChatActionSender.typing(bot=bot, chat_id=call.message.chat.id):
                await asyncio.sleep(2)  # Имитируем набор текста
                await bot.send_message(
                    chat_id=call.message.chat.id,
                    text="В ближайшее время с вами свяжется наш специалист для уточнения деталей.",
                    reply_markup=ReplyKeyboardRemove(),
                )

            # Отправляем информацию о заявке администратору
            try:
                for admin_id in settings.ADMIN_IDS:
                    message = await bot.send_message(
                        chat_id=admin_id,
                        text=f"Была создана заявка {last_appl.id}, Это сообщение для админа",
                        reply_markup=ReplyKeyboardRemove(),
                    )

            except Exception as e:
                logger.error(
                    f"Не удалось отправить сообщение админу {admin_id} об остановке бота: {e}"
                )
                pass

            response_message: str = f"Заявка № {last_appl.id}\n\nСтатус заявки: 🟡 {last_appl.status.value}\n\n"
            response_message += (
                "Собственные счета - ДА\n\n"
                if last_appl.owner
                else "Собственные счета - Нет\n\n"
            )
            if not last_appl.owner and last_appl.can_contact is not None:
                response_message += (
                    "Может связаться с собственником счета - ДА\n\n"
                    if last_appl.can_contact
                    else "Может связаться с собственником счета - Нет\n\n"
                )
            # Добавляем задолженности по банкам, если они есть
            if last_appl.debts:
                response_message += "Задолженности по банкам:\n"
                for debt in last_appl.debts:
                    response_message += f"🔸 Банк: <b>{debt.bank_name}</b>, Сумма задолженности: <b>{debt.total_amount}</b> руб.\n"

            response_message += f"\n\n <b>{user_applications.phone_number}</b> \n\n"
            response_message += "\n\n Берете заявку в работу?"

            media: List[InputMedia] = []  # Список для хранения медиа файлов

            # Прикрепляем фотографии, если они есть
            if last_appl.photos:
                for photo in last_appl.photos:
                    media.append(InputMediaPhoto(type="photo", media=photo.file_id))

            # Прикрепляем видео, если они есть
            if last_appl.videos:
                for video in last_appl.videos:
                    media.append(InputMediaVideo(type="video", media=video.file_id))

            # Отправляем информацию о заявке администратору
            try:
                for admin_id in settings.ADMIN_IDS:
                    # Отправляем медиа группу (фото/видео) и информацию администратору
                    await bot.send_media_group(chat_id=admin_id, media=media)
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
            await ApplicationDAO.delete(session=session, filters={"id":last_appl.id})
            await bot.send_message(
                chat_id=call.message.chat.id,
                text="Необходимо начать сначала создавать заявку",
                reply_markup=main_kb(),  # Возможно, кнопка для начала новой заявки
            )

    except Exception as e:
        # Логируем ошибку и отправляем пользователю сообщение о сбое
        logger.error(f"Ошибка при обработке запроса: {e}")
        await call.message.answer("Произошла ошибка. Попробуйте снова.")


@application_form_router.message(
    lambda message: message.contact is not None or message.text is not None
)
@connection()
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

    if existing_user:
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


@application_form_router.message(F.text, ApplicationForm.approve_work)
@application_form_router.message(F.text, ApplicationForm.owner)
@application_form_router.message(F.text, ApplicationForm.photo)
@application_form_router.message(F.text, ApplicationForm.video)
@application_form_router.message(F.text, ApplicationForm.approve_form)
async def mistakes_handler(message: Message, state: FSMContext) -> None:
    """ """
    try:
        await message.answer("Необходимо нажать по кнопке 👆")

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
