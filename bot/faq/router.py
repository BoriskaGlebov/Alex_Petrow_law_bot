from aiogram import F
from aiogram.filters import CommandObject, CommandStart, Command
from loguru import logger
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.router import Router
from aiogram.exceptions import TelegramBadRequest

from bot.database import connection
from bot.faq.dao import QuestionsDAO
from bot.faq.keyboards.inline_kb import faq_inline_keyboard
from bot.faq.schemas import QuestionFilter
from bot.users.dao import UserDAO
from bot.users.keyboards.markup_kb import main_kb
from bot.users.schemas import TelegramIDModel, UserModel
from bot.users.utils import get_refer_id_or_none

faq_router = Router()
# Глобальный кэш для хранения вопросов и ответов
questions_cache = {}


# Обработчик команды '/faq' и текстового сообщения 'База знаний'
@faq_router.message(Command('faq'))
@faq_router.message(F.text.contains('База знаний'))
@connection()
async def faq_start(message: Message, session, **kwargs) -> None:
    """
    Отправляет пользователю список вопросов с кнопками.
    """
    try:
        # Очищаем кэш перед обновлением
        questions_cache.clear()
        # Здесь должен быть запрос к БД для получения вопросов
        questions_filter = QuestionFilter()
        questions_answers = await QuestionsDAO.find_all(session=session, filters=questions_filter)
        # Кэшируем вопросы в памяти
        questions_cache.update({q.id: q for q in questions_answers})

        # Отправляем вопросы пользователю с клавиатурой
        await message.answer("Частые вопросы:", reply_markup=faq_inline_keyboard(list(questions_cache.values())))
    except Exception as e:
        # Логируем ошибку, если она возникла
        logger.error(f"Ошибка при выполнении команды /faq: {e}")
        await message.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже.")


# Обработчик для получения ответа на вопрос
# Обработчик для получения ответа на вопрос
@faq_router.callback_query(F.data.startswith('qst_'))
async def faq_callback(call: CallbackQuery):
    """
    Отправляет ответ на выбранный вопрос.
    """
    try:
        await call.answer(text="Смотрю", show_alert=False)
        qst_id = int(call.data.replace('qst_', ''))

        # Получаем данные вопроса из кеша
        qst_data: QuestionsDAO = questions_cache.get(qst_id)

        if qst_data:
            qst_data_dict = qst_data.to_dict()
            msg_text = f'Ответ на вопрос: {qst_data_dict["question"]}\n\n' \
                       f'<b>{qst_data_dict["answer"]}</b>\n\n' \
                       f'Выбери другой вопрос:'

            # Проверяем, совпадает ли новый текст с текущим
            current_text = call.message.text

            # Если текст не изменился, не отправляем новый запрос
            if current_text != msg_text:
                await call.message.edit_text(msg_text, reply_markup=faq_inline_keyboard(list(questions_cache.values())))

        else:
            await call.message.answer("Ответ на данный вопрос не найден.")

    except TelegramBadRequest:
        # Этот код срабатывает, если сообщение не было изменено (текст не изменился)
        pass
    except Exception as e:
        # Логируем ошибку, если она возникла
        logger.error(f"Ошибка при обработке запроса: {e}")
        await call.message.answer("Произошла ошибка. Попробуйте снова.")


# Обработчик для получения ответа на вопрос
@faq_router.callback_query(F.data.startswith('back_home'))
async def faq_main_menu(call: CallbackQuery):
    """
    Отправляет ответ на кнопку назад
    """
    await call.answer()
    # qst_id = int(call.data.replace('back_home', ''))

    await call.message.answer("Выберите один из пунктов меню 👇", reply_markup=main_kb())
