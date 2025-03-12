from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from bot.config import bot, settings  # Убедись, что settings.ADMIN_IDS содержит ID админов

# Команды для обычных пользователей
user_commands = [
    BotCommand(command='start', description='🏎  Старт работы с приложением'),
    BotCommand(command='faq', description='🗂  Ответы на часто задаваемые вопросы!'),
    BotCommand(command='help', description='⁉️  Описание функций')
]

# Команды для администраторов
admin_commands = [
    BotCommand(command='start', description='🏎  Старт работы с приложением'),
    BotCommand(command='admin', description='🏎  Админ, жду заявки'),
    BotCommand(command='faq', description='🗂  Ответы на часто задаваемые вопросы!'),
    BotCommand(command='help', description='⁉️  Описание функций'),
]

async def set_bot_commands() -> None:
    """
    Устанавливает команды для пользователей и администраторов.
    """
    # Устанавливаем команды по умолчанию для всех (обычные пользователи)
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    # Устанавливаем команды для администраторов
    for admin_id in settings.ADMIN_IDS:
        await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))
