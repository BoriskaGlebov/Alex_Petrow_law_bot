# TODO Пока нет точного понимания команд и описания будет так , потом для админ панели будут доп сообщения
from aiogram.filters import CommandObject, CommandStart, Command
from loguru import logger
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.dispatcher.router import Router
from bot.database import connection
from bot.users.dao import UserDAO
from bot.users.schemas import TelegramIDModel, UserModel
from bot.users.utils import get_refer_id_or_none
from bot.utils.commands import commands

help_router = Router()


@help_router.message(Command('help'))
async def help_cmd(message: Message) -> None:
    """
    Обрабатывает команду /help и отправляет пользователю список доступных команд.

    Эта функция отправляет пользователю сообщение с описанием всех доступных команд.
    Для каждого элемента в списке команд формируется строка с командой и её описанием.

    Параметры:
    - `message` (Message): Объект сообщения, который содержит информацию о пользователе,
      который вызвал команду /help.

    Возвращаемое значение:
    - None: Функция ничего не возвращает. Отправляет сообщение пользователю.

    Логирование:
    - Записывает информацию о запуске команды и её успешном выполнении.

    Пример использования:
    ```python
    @help_router.message(Command('help'))
    async def help_cmd(message: Message):
        ...
    ```

    Примечания:
    - Список команд хранится в `commands` и может быть изменён в зависимости от контекста.
    - В случае необходимости, можно добавить дополнительные проверки на пользователя для кастомизации списка команд.
    """
    logger.debug('нажал кнопку помощи')

    # Формируем список текстов с командами
    text = [f'{el.command} - {el.description}' for el in commands]

    # Отправка ответа с перечислением команд
    await message.answer(text='\n'.join(text), reply_markup=ReplyKeyboardRemove())

    logger.info(f'кнопка отработала')