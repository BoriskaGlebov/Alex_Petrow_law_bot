from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from loguru import logger
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.dispatcher.router import Router
from bot.config import settings  # Загружаем список админов
from bot.utils.commands import admin_commands, user_commands

help_router = Router()


@help_router.message(Command('help'))
async def help_cmd(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает команду /help и отправляет пользователю список доступных команд.
    Показывает разные команды для обычных пользователей и администраторов.
    """
    logger.debug('Пользователь нажал кнопку помощи')

    # Разделение команд для пользователей и админов
    user_cmd = [f'/{cmd.command} - {cmd.description}' for cmd in user_commands if cmd.command != 'admin']
    admin_cmd = [f'/{cmd.command} - {cmd.description}' for cmd in admin_commands]

    # Определяем список команд в зависимости от пользователя
    if message.from_user.id in settings.ADMIN_IDS:
        command_list = admin_cmd
    else:
        command_list = user_cmd

    await state.clear()

    # Отправка ответа с соответствующим списком команд
    await message.answer(
        text="\n".join(command_list),
        reply_markup=ReplyKeyboardRemove()
    )

    logger.info(f'Команда /help выполнена пользователем {message.from_user.id}')
