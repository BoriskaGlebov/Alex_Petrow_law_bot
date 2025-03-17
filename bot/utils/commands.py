from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from bot.config import (
    bot,
    logger,
    settings,
)  # Убедись, что settings.ADMIN_IDS содержит ID админов

# Команды для обычных пользователей
user_commands: list[BotCommand] = [
    BotCommand(command="start", description="🏎  Старт работы с приложением"),
    BotCommand(command="unblock", description="🔐 Вывод заблокированных средств"),
    BotCommand(command="question", description="📝 Свой вопрос?"),
    BotCommand(command="faq", description="🗂  Ответы на часто задаваемые вопросы!"),
    BotCommand(command="help", description="⁉️  Описание функций"),
]

# Команды для администраторов
admin_commands: list[BotCommand] = [
    BotCommand(command="start", description="🏎  Старт работы с приложением"),
    BotCommand(command="unblock", description="🔐 Вывод заблокированных средств"),
    BotCommand(command="question", description="📝 Свой вопрос?"),
    BotCommand(command="admin", description="👀  Админ, жду заявки"),
    BotCommand(command="faq", description="🗂  Ответы на часто задаваемые вопросы!"),
    BotCommand(command="help", description="⁉️  Описание функций"),
]


async def set_bot_commands() -> None:
    """
    Устанавливает команды для пользователей и администраторов.

    - Обычные пользователи получают стандартный набор команд.
    - Администраторы получают дополнительные команды.
    """
    # Устанавливаем команды по умолчанию для всех (обычные пользователи)
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    # Устанавливаем команды для администраторов
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.set_my_commands(
                admin_commands, scope=BotCommandScopeChat(chat_id=admin_id)
            )
        except TelegramBadRequest as e:
            if "chat not found" in str(e):
                logger.bind(user=admin_id).error(
                    f"⚠️  Ошибка: у администратора {admin_id} не начат чат с ботом."
                )
            else:
                raise  # Пробрасываем другие ошибки
