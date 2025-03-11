import asyncio
from typing import Optional

from aiogram import F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.chat_action import ChatActionSender
from loguru import logger
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.dispatcher.router import Router

import bot.application_form.dao
from bot.admins.keyboards.inline_kb import approve_admin_keyboard
from bot.application_form.dao import ApplicationDAO
from bot.application_form.models import ApplicationStatus
from bot.config import bot, settings
from bot.database import connection
from bot.users.dao import UserDAO
from bot.users.keyboards.inline_kb import approve_keyboard
from bot.users.keyboards.markup_kb import main_kb
from bot.users.schemas import TelegramIDModel, UserModel
from bot.users.utils import get_refer_id_or_none

admin_router = Router()


@admin_router.callback_query(F.data.startswith('approve_admin_'))
@connection()
async def admin_application_callback(call: CallbackQuery, session) -> None:
    """

    """
    try:
        await call.answer(text="Проверяю ввод", show_alert=False)

        approve_inf = call.data.replace('approve_admin_', '').split('_')
        user_id = int(approve_inf[1])
        print(user_id)
        application_id = int(approve_inf[2])
        print(application_id)
        approve_inf = approve_inf[0]
        print(approve_inf)
        approve_inf = True if approve_inf == "True" else False
        # await call.message.edit_reply_markup(reply_markup=None)
        if approve_inf:
            await ApplicationDAO.update(session=session, filters={'id': application_id},
                                        values={'status': ApplicationStatus("approved")})
            application = await ApplicationDAO.find_one_or_none_by_id(data_id=application_id, session=session)
            response_message: str = (
                f"Заявка № {application_id}\n\nСтатус заявки: 🟢 {application.status.value}\n\n"
            )

            # Добавляем задолженности по банкам, если они есть
            if application.debts:
                response_message += "Задолженности по банкам:\n"
                for debt in application.debts:
                    response_message += f"🔸 Банк: <b>{debt.bank_name}</b>, Сумма задолженности: <b>{debt.total_amount}</b> руб.\n"

            response_message += f"\n\n <b>{application.user.phone_number}</b> \n\n"
            response_message += "\n\n Берете заявку в работу?"

            await call.message.edit_text(response_message,
                                         reply_markup=approve_admin_keyboard('Берем', 'Отказ', user_id, application_id))
            await bot.send_message(chat_id=call.from_user.id,
                                   text="Вот ты чтото выбрал как админ а у пользователя ничего")
            await bot.send_message(chat_id=user_id,
                                   text=f"Статус заказа поменялcя на 🟢 {application.status.value} - принята в работу ")
        else:
            await ApplicationDAO.update(session=session, filters={'id': application_id},
                                        values={'status': ApplicationStatus("rejected")})
            application = await ApplicationDAO.find_one_or_none_by_id(data_id=application_id, session=session)
            response_message: str = (
                f"Заявка № {application_id}\n\nСтатус заявки: 🔴 {application.status.value} - отклонена\n\n"
            )

            # Добавляем задолженности по банкам, если они есть
            if application.debts:
                response_message += "Задолженности по банкам:\n"
                for debt in application.debts:
                    response_message += f"🔸 Банк: <b>{debt.bank_name}</b>, Сумма задолженности: <b>{debt.total_amount}</b> руб.\n"
            response_message += f"\n\n <b>{application.user.phone_number}</b> \n\n"
            response_message += "\n\n Берете заявку в работу?"

            await call.message.edit_text(response_message,
                                         reply_markup=approve_admin_keyboard('Берем', 'Отказ', user_id, application_id))
            await bot.send_message(chat_id=call.from_user.id,
                                   text="Вот ты чтото выбрал как админ а у пользователя ничего")
            await bot.send_message(chat_id=user_id, text=f"Статус заказа поменялcя на 🔴 {application.status.value} ")

    except TelegramBadRequest:
        # Это срабатывает, если сообщение не было изменено (например, текст остался таким же)
        pass
    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при обработке запроса: {e}")
        await call.message.answer("Произошла ошибка. Попробуйте снова.")

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
