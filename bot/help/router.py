from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from loguru import logger
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.dispatcher.router import Router
from bot.config import settings  # Загружаем список админов
from bot.utils.commands import admin_commands, user_commands

help_router = Router()


@logger.catch
@help_router.message(Command("help"))
async def help_cmd(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает команду /help и отправляет пользователю список доступных команд.
    Показывает разные команды для обычных пользователей и администраторов.
    """
    try:
        logger.debug(f"Пользователь {message.from_user.id} нажал кнопку помощи")

        # Получаем команды в зависимости от роли пользователя
        command_list = [
            f"/{cmd.command} - {cmd.description}"
            for cmd in (
                admin_commands
                if message.from_user.id in settings.ADMIN_IDS
                else user_commands
            )
            if cmd.command != "admin"
        ]

        await state.clear()

        # Отправка ответа с соответствующим списком команд
        await message.answer(
            text="\n".join(command_list), reply_markup=ReplyKeyboardRemove()
        )

        logger.bind(user=message.from_user.id).info(
            f"Команда /help выполнена пользователем {message.from_user.id}"
        )
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /help: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
