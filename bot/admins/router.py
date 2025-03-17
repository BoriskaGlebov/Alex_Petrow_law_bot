from typing import Dict

from aiogram import F
from aiogram.dispatcher.router import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery
from loguru import logger

import bot.application_form.dao
from bot.admins.keyboards.inline_kb import approve_admin_keyboard
from bot.application_form.dao import ApplicationDAO
from bot.application_form.models import Application, ApplicationStatus
from bot.config import bot
from bot.database import connection

admin_router = Router()


@admin_router.callback_query(F.data.startswith("approve_admin_"))
@connection()
async def admin_application_callback(call: CallbackQuery, session) -> None:
    """
    Обработчик нажатий на кнопки одобрения/отклонения заявки администратором.

    Args:
        call (CallbackQuery): Объект входящего callback-запроса.
        session: Сессия базы данных.

    Raises:
        TelegramBadRequest: Ошибка Telegram, если сообщение не было изменено.
        Exception: Логируется любая другая ошибка, возникающая в процессе выполнения.
    """
    try:
        await call.answer(text="Проверяю ввод", show_alert=False)

        # Извлекаем данные из callback-запроса
        approve_inf, user_id_str, application_id_str = call.data.replace(
            "approve_admin_", ""
        ).split("_")
        user_id: int = int(user_id_str)
        application_id: int = int(application_id_str)
        approve: bool = approve_inf == "True"

        # Определяем статус заявки
        new_status = ApplicationStatus("Принято" if approve else "Отклонено")
        await ApplicationDAO.update(
            session=session,
            filters={"id": application_id},
            values={"status": new_status},
        )

        application: Application = await ApplicationDAO.find_one_or_none_by_id(
            data_id=application_id, session=session
        )

        # Формируем текст сообщения
        status_icon = "🟢" if approve else "🔴"
        response_message = (
            f"Заявка № {application_id}\n\n"
            f"Статус заявки: {status_icon} {new_status.value}\n\n"
        )

        if application.owner is not None:
            response_message += (
                "Собственные счета - ДА\n\n"
                if application.owner
                else "Собственные счета - Нет\n\n"
            )
        if not application.owner and application.can_contact is not None:
            response_message += (
                "Может связаться с собственником счета - ДА\n\n"
                if application.can_contact
                else "Может связаться с собственником счета - Нет\n\n"
            )
        if application.text_application:
            response_message += f"Ваш вопрос:\n{application.text_application}\n\n"
        if application.debts:
            response_message += "Задолженности по банкам:\n"
            for debt in application.debts:
                response_message += f"🔸 Банк: <b>{debt.bank_name}</b>, Сумма задолженности: <b>{debt.total_amount}</b> руб.\n"
        response_message += f"\n\n <b>{application.user.phone_number}</b> \n\n"
        response_message += "\n\n Берете заявку в работу?"

        # Обновляем сообщения у администраторов
        admin_message_ids: Dict[int, int] = application.admin_message_ids
        if admin_message_ids:
            for admin_id, msg_id in admin_message_ids.items():
                try:
                    await bot.edit_message_text(
                        chat_id=admin_id,
                        message_id=msg_id,
                        text=response_message,
                        reply_markup=approve_admin_keyboard(
                            "Берем", "Отказ", user_id, application_id
                        ),
                    )
                except Exception as e:
                    logger.error(
                        f"Ошибка при обновлении сообщения у админа {admin_id}: {e}"
                    )

        # Отправляем пользователю обновленный статус заявки
        await bot.send_message(
            chat_id=user_id,
            text=f"Статус заказа № {application_id} поменялcя на {status_icon} {new_status.value}",
        )

    except TelegramBadRequest:
        pass  # Игнорируем ошибку, если сообщение не было изменено
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса на обновление статуса админом: {e}")
        await call.message.answer("Произошла ошибка. Попробуйте снова.")
