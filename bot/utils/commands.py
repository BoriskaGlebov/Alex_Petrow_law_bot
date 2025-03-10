from aiogram.types import BotCommand, BotCommandScopeDefault

from bot.config import bot

# Список команд для бота с их описаниями маленькими буквами
commands = [
    BotCommand(command='start', description=' 🏎  Старт работы с приложением'),
    BotCommand(command='application', description=' 📝  Создание заявки на оказание услуги'),
    BotCommand(command='faq', description=' 🗂  Ответы на часто задаваемые вопросы!'),
    BotCommand(command='help', description=' ⁉️  Описание функций')
]


async def set_commands(commands_list: list[BotCommand]) -> None:
    """
    Настроить командное меню для бота.

    Эта функция устанавливает список команд, которые будут доступны всем пользователям бота.
    Команды устанавливаются с помощью метода `set_my_commands` API бота.

    Параметры:
    - `commands` (list[BotCommand]): Список объектов `BotCommand`, представляющих команды и их описания.

    Возвращаемое значение:
    - None: Функция ничего не возвращает.

    Пример использования:
    ```
    commands = [BotCommand(command='start', description='Старт')]
    await set_commands(commands)
    ```
    """
    await bot.set_my_commands(commands_list, BotCommandScopeDefault())
