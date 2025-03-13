from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.chat_action import ChatActionSender
from loguru import logger
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.router import Router
from aiogram.exceptions import TelegramBadRequest

from bot.database import connection
from bot.faq.dao import QuestionsDAO
from bot.faq.keyboards.inline_kb import faq_inline_keyboard
from bot.faq.schemas import QuestionFilter
from bot.faq.utils import update_cache
from bot.users.keyboards.markup_kb import main_kb

faq_router = Router()
# Глобальный кэш для хранения вопросов и ответов
questions_cache = {}


class Answering(StatesGroup):
    check = State()


# Обработчик команды '/faq' и текстового сообщения 'База знаний'
@faq_router.message(Command('faq'))
@faq_router.message(F.text.contains('База знаний'))
@connection()
async def faq_start(message: Message, session, state: FSMContext, **kwargs) -> None:
    """
    Обработчик команды '/faq' и текстового сообщения 'База знаний'. Отправляет пользователю список частых вопросов с кнопками.

    Это действие извлекает вопросы из базы данных и кэширует их в память. Затем пользователю отправляется
    сообщение с кнопками для выбора вопросов.

    Args:
        message (Message): Сообщение, отправленное пользователем.
        session: Сессия для работы с базой данных.
        state (FSMContext): Контекст состояния машины состояний для пользователя.
        **kwargs: Дополнительные аргументы, передаваемые через декоратор.

    Returns:
        None: Функция не возвращает значения, но отправляет сообщение пользователю.

    Raises:
        Exception: В случае ошибки при получении данных из базы или отправке сообщений.
    """
    try:
        await state.clear()

        # Имитация набора текста
        async with ChatActionSender.typing(bot=message.bot, chat_id=message.chat.id):
            # Получаем все вопросы из базы данных
            questions_filter = QuestionFilter()
            questions_answers = await QuestionsDAO.find_all(session=session, filters=questions_filter)

            # Кэшируем вопросы в памяти для быстрого доступа
            update_cache(questions_cache, {q.id: q for q in questions_answers})

            # Отправляем пользователю сообщение с вопросами и кнопками
            await message.answer("Частые вопросы:", reply_markup=faq_inline_keyboard(list(questions_cache.values())))
            await state.set_state(Answering.check)

    except TelegramBadRequest as e:
        # Логируем ошибку Telegram
        logger.error(f"Telegram error при выполнении команды /faq: {e}")
        await message.answer("Произошла ошибка при отправке сообщения. Попробуйте снова позже.")
    except Exception as e:
        # Логируем общие ошибки
        logger.error(f"Ошибка при выполнении команды /faq: {e}")
        await message.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже.")


# Обработчик для получения ответа на выбранный вопрос
@faq_router.callback_query(F.data.startswith('qst_'), Answering.check)
async def faq_callback(call: CallbackQuery) -> None:
    """
    Обработчик коллбек-запроса для выбора ответа на вопрос из списка.

    Получает ID вопроса из данных коллбека, извлекает его из кэша
    и отправляет ответ в том виде, в котором он был сохранен в базе данных.

    Если данных по данному вопросу нет в кэше, пользователю отправляется сообщение
    о том, что ответ не найден. В случае других ошибок пользователю отправляется
    сообщение об ошибке.

    Args:
        call (CallbackQuery): Коллбек-запрос, отправленный пользователем.

    Returns:
        None: Функция не возвращает значений, но редактирует сообщение с ответом на вопрос.

    Raises:
        TelegramBadRequest: Если сообщение не может быть изменено (например, текст не изменился).
        Exception: В случае других ошибок при обработке запроса.
    """
    try:
        # Подтверждение получения запроса
        await call.answer(text="Смотрю", show_alert=False)

        # Извлекаем ID вопроса из данных коллбека
        qst_id: int = int(call.data.replace('qst_', ''))

        # Получаем данные вопроса из кэша
        qst_data: QuestionsDAO = questions_cache.get(qst_id)

        if qst_data:
            # Конвертируем данные вопроса в словарь
            qst_data_dict = qst_data.to_dict()
            msg_text = f'Ответ на вопрос: {qst_data_dict["question"]}\n\n' \
                       f'<b>{qst_data_dict["answer"]}</b>\n\n' \
                       f'Выбери другой вопрос:'

            # Проверяем, совпадает ли новый текст с текущим
            current_text: str = call.message.text
            if current_text != msg_text:
                await call.message.edit_text(msg_text, reply_markup=faq_inline_keyboard(list(questions_cache.values())))

        else:
            await call.message.answer("Ответ на данный вопрос не найден.")

    except TelegramBadRequest as e:
        # Это срабатывает, если сообщение не было изменено (например, текст остался таким же)
        logger.warning(f"Ошибка при попытке редактировать сообщение: {e}")
    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        await call.message.answer("Произошла ошибка. Попробуйте снова.")


# Обработчик для перехода назад в основное меню
@faq_router.callback_query(F.data.startswith('back_home'), Answering.check)
async def faq_main_menu(call: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик коллбек-запроса для перехода назад в главное меню.

    Когда пользователь нажимает на кнопку "Назад", отправляется главное меню с возможностью выбора других опций.
    Этот обработчик очищает состояние пользователя и показывает основное меню с кнопками.

    Args:
        call (CallbackQuery): Коллбек-запрос от пользователя, содержащий данные о нажатой кнопке.
        state (FSMContext): Контекст текущего состояния машины состояний пользователя.

    Returns:
        None: Функция не возвращает значения, а отправляет сообщение с основным меню и очищает состояние пользователя.

    Raises:
        Exception: В случае ошибки при отправке сообщения или других непредвиденных ситуаций.
    """
    try:
        # Подтверждаем, что запрос обработан
        await call.answer()

        # Отправляем сообщение с основным меню
        await call.message.answer("Выберите один из пунктов меню 👇", reply_markup=main_kb())

        # Очищаем состояние пользователя
        await state.clear()

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при переходе назад в главное меню: {e}")

        # Информируем пользователя об ошибке
        await call.message.answer("Произошла ошибка при возвращении в главное меню. Попробуйте снова.")
